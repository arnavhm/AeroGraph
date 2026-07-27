"""
Build the graph-schema block that gets injected into the LLM system prompt.

The schema is derived from the LIVE graph by taking the UNION of property keys
across ALL nodes of each label - never by sampling a single node.

Why that distinction is load-bearing (verified 2026-07-27):
Aircraft.ready_at is present on only 3 of 8 Aircraft nodes (the unassigned
spares). A schema built by sampling one Aircraft node misses ready_at
entirely, and a model cannot reference a property it was never told exists -
which would make the Gate 5 Version A temporal feasibility constraint
unwritable and silently drop it from any generated query.
"""
from agent.db import get_driver

# Property keys whose values are enumerable and worth listing explicitly,
# because the exact spelling of the value matters to a WHERE clause.
_ENUM_PROPS = [("Engine", "risk_state")]


def _type_name(v):
    return type(v).__name__.replace("DateTime", "DATETIME").upper()


def _fmt_value(v):
    """Render an example value the way it would appear in Cypher, not as a Python repr."""
    if hasattr(v, "iso_format"):
        return f"datetime('{v.iso_format()}')"
    return repr(v)


def _collect_labels(s):
    return [r["label"] for r in s.run("CALL db.labels() YIELD label RETURN label ORDER BY label")]


def _label_block(s, label):
    total = s.run(f"MATCH (n:`{label}`) RETURN count(n) AS c").single()["c"]
    counts = {
        r["k"]: r["c"]
        for r in s.run(f"MATCH (n:`{label}`) UNWIND keys(n) AS k RETURN k, count(*) AS c")
    }
    lines = [f"(:{label})  -- {total} nodes"]
    for key in sorted(counts):
        # Sample a value from a node that ACTUALLY HAS the key, so heterogeneous
        # properties still get a correct type and example.
        rec = s.run(
            f"MATCH (n:`{label}`) WHERE n.`{key}` IS NOT NULL RETURN n.`{key}` AS v LIMIT 1"
        ).single()
        v = rec["v"] if rec else None
        present = counts[key]
        note = ""
        if present != total:
            note = f"   [PRESENT ON ONLY {present} OF {total} NODES - do not assume every (:{label}) has it]"
        lines.append(f"    {key} : {_type_name(v)}  e.g. {_fmt_value(v)}{note}")
    return "\n".join(lines)


def _rel_block(s):
    rows = s.run(
        "MATCH (a)-[r]->(b) "
        "RETURN DISTINCT labels(a)[0] AS f, type(r) AS t, labels(b)[0] AS d, count(*) AS n "
        "ORDER BY t"
    )
    return "\n".join(f"    (:{r['f']})-[:{r['t']}]->(:{r['d']})   -- {r['n']} edges" for r in rows)


def _enum_block(s):
    out = []
    for label, prop in _ENUM_PROPS:
        vals = [
            r["v"]
            for r in s.run(
                f"MATCH (n:`{label}`) WHERE n.`{prop}` IS NOT NULL "
                f"RETURN DISTINCT n.`{prop}` AS v ORDER BY v"
            )
        ]
        out.append(f"    {label}.{prop} is one of: {', '.join(repr(v) for v in vals)}")
    return "\n".join(out)


def build_schema_text() -> str:
    """Return the full schema description block, derived from the live graph."""
    with get_driver().session() as s:
        labels = "\n\n".join(_label_block(s, l) for l in _collect_labels(s))
        rels = _rel_block(s)
        enums = _enum_block(s)
    return (
        "NODE LABELS AND PROPERTIES\n"
        "==========================\n"
        f"{labels}\n\n"
        "RELATIONSHIPS (direction matters)\n"
        "=================================\n"
        f"{rels}\n\n"
        "ENUMERATED VALUES (exact spelling matters in WHERE clauses)\n"
        "===========================================================\n"
        f"{enums}\n"
    )


if __name__ == "__main__":
    print(build_schema_text())

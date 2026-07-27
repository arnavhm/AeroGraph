"""
Guardrails applied to LLM-generated Cypher BEFORE it reaches the database.

Layered on purpose. The string checks here are the CHEAP layer - they give a
fast, readable rejection reason. They are NOT the enforcement boundary.
Enforcement is server-side: agent/graph_tool.py runs everything inside a
Neo4j READ transaction, so the database itself refuses writes even if a
string check is somehow evaded.

Deliberately NOT implemented: a check on whether the risk_state filter appears
before the aggregation. Measured 2026-07-27 against the live graph: filtering
after aggregation still returns the correct aircraft (AG101), because on this
fleet every aircraft's highest-risk_score engine is also its Critical one.
A clause-order regex would police something that does not determine
correctness here while feeling rigorous - borrowed rigor, per charter 11.
What DOES determine correctness is measured in scripts/17_agent_gate.py.
"""
import re

MAX_QUERY_CHARS = 4000

# Write / admin / control keywords. Matched on word boundaries against a
# literal-stripped copy of the query.
_FORBIDDEN = [
    "CREATE", "DELETE", "DETACH", "SET", "MERGE", "REMOVE", "DROP",
    "LOAD", "FOREACH", "CALL", "USE", "TERMINATE", "SHOW", "GRANT",
    "REVOKE", "ALTER", "RENAME", "START",
]

_STRING_LIT = re.compile(r"'(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\"")
_LINE_COMMENT = re.compile(r"//[^\n]*")
_BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.S)


def _strip_noise(q: str) -> str:
    """Remove comments and string literals so keyword matching sees only code.

    Without this, WHERE a.name = 'CREATE ACCOUNT' would be rejected (false
    positive) and a keyword hidden inside a comment would be missed.
    """
    q = _BLOCK_COMMENT.sub(" ", q)
    q = _LINE_COMMENT.sub(" ", q)
    q = _STRING_LIT.sub("''", q)
    return q


def validate(cypher: str):
    """Return (ok: bool, reason: str). reason is '' when ok."""
    if cypher is None or not cypher.strip():
        return False, "empty query"

    if len(cypher) > MAX_QUERY_CHARS:
        return False, f"query exceeds {MAX_QUERY_CHARS} characters"

    code = _strip_noise(cypher)

    # Single statement only. A trailing semicolon is tolerated; an interior one
    # would allow smuggling a second statement past a keyword check.
    if ";" in code.rstrip().rstrip(";"):
        return False, "multiple statements are not allowed (interior ';')"

    upper = code.upper()
    for kw in _FORBIDDEN:
        if re.search(rf"\b{kw}\b", upper):
            return False, f"forbidden keyword '{kw}' - this tool is read-only"

    if not re.search(r"\bMATCH\b", upper) and not re.search(r"\bRETURN\b", upper):
        return False, "not a read query (no MATCH or RETURN)"

    return True, ""

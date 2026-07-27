"""
The ONE tool exposed to the LLM: execute_graph_query(query: str).

Defence is layered, and the layers are not equally trusted:
  1. agent.guardrails.validate() - cheap string checks, fast readable rejection.
  2. EXPLAIN - Neo4j parses and plans the query WITHOUT executing it. Real
     syntax validation by the actual parser, not a regex pretending to be one.
  3. A Neo4j READ transaction - the ENFORCEMENT boundary. The server refuses
     writes here regardless of what got past layers 1 and 2.
  4. Row cap + transaction timeout - a cartesian blow-up must not take out a
     free-tier Aura instance.
"""
import itertools

from agent.db import get_driver
from agent.guardrails import validate

MAX_ROWS = 100
QUERY_TIMEOUT_S = 15


def _jsonable(v):
    """neo4j temporal / graph types are not JSON-serialisable. Flatten them."""
    if hasattr(v, "iso_format"):
        return v.iso_format()
    if hasattr(v, "items") and not isinstance(v, dict):
        return {k: _jsonable(x) for k, x in dict(v).items()}
    if isinstance(v, dict):
        return {k: _jsonable(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_jsonable(x) for x in v]
    return v


def _run_read(query: str):
    """Execute inside an explicit READ transaction with a timeout."""
    drv = get_driver()
    with drv.session(default_access_mode="READ") as s:
        with s.begin_transaction(timeout=QUERY_TIMEOUT_S) as tx:
            res = tx.run(query)
            raw = list(itertools.islice(res, MAX_ROWS + 1))
            return [{k: _jsonable(v) for k, v in r.data().items()} for r in raw]


def _explain(query: str):
    drv = get_driver()
    with drv.session(default_access_mode="READ") as s:
        with s.begin_transaction(timeout=QUERY_TIMEOUT_S) as tx:
            tx.run(f"EXPLAIN {query}").consume()


def execute_graph_query(query: str) -> dict:
    """Run a READ-ONLY Cypher query against the AeroGraph knowledge graph.

    Args:
        query: A single read-only Cypher statement. Must not create, delete,
            or modify any data.

    Returns:
        A dict with keys: ok, rows, row_count, truncated, error, rejected_by.
    """
    base = {"ok": False, "rows": [], "row_count": 0, "truncated": False,
            "error": None, "rejected_by": None}

    ok, reason = validate(query)
    if not ok:
        return {**base, "error": reason, "rejected_by": "guardrail"}

    try:
        _explain(query)
    except Exception as e:
        return {**base, "error": f"{type(e).__name__}: {e}", "rejected_by": "explain"}

    try:
        rows = _run_read(query)
    except Exception as e:
        return {**base, "error": f"{type(e).__name__}: {e}", "rejected_by": "execution"}

    truncated = len(rows) > MAX_ROWS
    rows = rows[:MAX_ROWS]
    return {"ok": True, "rows": rows, "row_count": len(rows),
            "truncated": truncated, "error": None, "rejected_by": None}

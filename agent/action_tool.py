"""
Action execution for the pre-approved catalog (Option D).

execute_action(action_name, params) is the single execution path for catalog
actions, used by the gate (scripts/21_action_gate.py) and the API alike. Its
return shape matches agent.graph_tool.execute_graph_query() exactly — same
keys, same types, same never-raises behaviour — so a caller can swap between
the two tools without branching on response shape.

Action Cypher is deliberately NOT routed through agent.guardrails.validate().
It is pre-approved and version-controlled under cypher/actions/; the
enum-and-bounds check in agent.catalog.validate_params is its guardrail.
The READ transaction remains the enforcement boundary either way.
"""
import itertools

from agent.catalog import load_cypher, validate_params
from agent.db import get_driver
# Shared with the free-form tool so a future change to the limits cannot
# silently apply to one execution path and not the other.
from agent.graph_tool import MAX_ROWS, QUERY_TIMEOUT_S, _jsonable


def execute_action(action_name: str, params: dict | None = None) -> dict:
    """Run a pre-approved, parameterised catalog action.

    Args:
        action_name: Key into agent.catalog.ACTIONS.
        params: Parameter values; missing ones take catalog defaults.

    Returns:
        A dict with keys: ok, rows, row_count, truncated, error, rejected_by.
        Never raises. Validation failure -> rejected_by="catalog";
        execution failure -> rejected_by="execution".
    """
    base = {"ok": False, "rows": [], "row_count": 0, "truncated": False,
            "error": None, "rejected_by": None}

    ok, reason, resolved = validate_params(action_name, params)
    if not ok:
        return {**base, "error": reason, "rejected_by": "catalog"}

    try:
        cypher = load_cypher(action_name)
    except Exception as e:
        # The catalog owns cypher_file resolution; a missing or unreadable
        # file is a catalog-integrity failure, not a query-execution one.
        return {**base, "error": f"{type(e).__name__}: {e}", "rejected_by": "catalog"}

    try:
        drv = get_driver()
        with drv.session(default_access_mode="READ") as s:
            with s.begin_transaction(timeout=QUERY_TIMEOUT_S) as tx:
                res = tx.run(cypher, **resolved)
                raw = list(itertools.islice(res, MAX_ROWS + 1))
                rows = [{k: _jsonable(v) for k, v in r.data().items()} for r in raw]
    except Exception as e:
        return {**base, "error": f"{type(e).__name__}: {e}", "rejected_by": "execution"}

    truncated = len(rows) > MAX_ROWS
    rows = rows[:MAX_ROWS]
    return {"ok": True, "rows": rows, "row_count": len(rows),
            "truncated": truncated, "error": None, "rejected_by": None}

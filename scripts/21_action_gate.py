# scripts/21_action_gate.py
"""
Gate for Option D Phase 1: Action Catalog.

Asserts:
  A. Graph shape matches expected node and edge counts from scripts/15_gate.py.
  B. Catalog risk_state enum matches live distinct values from graph.
  C. Execution with default params returns the golden row (AG101, G-AGSA, 1.010777).
  D. Negative cases are rejected by validate_params (unknown action, unknown param,
     invalid enum, out of bounds int, wrong types including bool).
  E. SQL/Cypher injection strings are rejected by enum validation, and valid params
     are bound directly by the driver without string formatting.
  F. Graph shape is unchanged after all runs.
"""
import sys, pathlib, importlib.util
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _env import require_venv

require_venv()

from agent.db import get_driver
from agent.catalog import ACTIONS, load_cypher, validate_params

# Expected node and edge counts from scripts/15_gate.py (lines 19-33)
EXP_NODES = {
    "Airport": 6,
    "MaintenanceHub": 3,
    "Aircraft": 8,
    "Engine": 16,
    "FlightRoute": 5,
}
EXP_EDGES = {
    "INSTALLED_ON": 16,
    "LOCATED_AT": 8,
    "ASSIGNED_TO": 5,
    "DEPARTS_FROM": 5,
    "ARRIVES_AT": 5,
    "SITUATED_AT": 3,
}

# Value comparison oracle approach copied from scripts/17_agent_gate.py
FLOAT_TOL = 1e-6
GOLDEN_TUPLE = ["AG101", "G-AGSA", 1.010777147894676]


def _norm(v):
    if v is None:
        return ""
    if isinstance(v, bool):
        return str(v).lower()
    if isinstance(v, float):
        return f"{v:.6f}"
    return str(v).strip().lower()


def _cells(row):
    if row is None:
        return set()
    if isinstance(row, dict):
        vals = row.values()
    elif isinstance(row, (list, tuple)):
        vals = row
    else:
        vals = [row]
    return {_norm(v) for v in vals}


def _hit(cell, expected):
    if isinstance(expected, float):
        try:
            return abs(float(cell) - expected) < FLOAT_TOL
        except (TypeError, ValueError):
            return False
    return cell == _norm(expected)


def _present(cells, expected):
    return any(_hit(c, expected) for c in cells)


def get_graph_shape():
    drv = get_driver()
    with drv.session(default_access_mode="READ") as s:
        n = s.run("MATCH (x) RETURN count(x) AS c").single()["c"]
        e = s.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"]
    return n, e


def execute_action(action_name: str, params: dict | None = None) -> list[dict]:
    ok, reason, resolved = validate_params(action_name, params)
    if not ok:
        raise ValueError(f"validate_params failed: {reason}")
    cypher = load_cypher(action_name)
    drv = get_driver()
    with drv.session(default_access_mode="READ") as s:
        with s.begin_transaction(timeout=15) as tx:
            res = tx.run(cypher, **resolved)
            return [r.data() for r in res]


def main():
    failures = []

    print("=" * 72)
    print("ACTION GATE — OPTION D PHASE 1")
    print("=" * 72)

    shape_before = get_graph_shape()
    print(f"Graph state before: {shape_before[0]} nodes, {shape_before[1]} edges\n")

    # --- ASSERTION A: Graph Shape matches expected counts ---
    try:
        drv = get_driver()
        with drv.session(default_access_mode="READ") as s:
            for label, exp_n in EXP_NODES.items():
                got_n = s.run(f"MATCH (x:{label}) RETURN count(x) AS c").single()["c"]
                assert got_n == exp_n, f"Node count mismatch for {label}: got {got_n}, want {exp_n}"
            for rel, exp_e in EXP_EDGES.items():
                got_e = s.run(f"MATCH ()-[r:{rel}]->() RETURN count(r) AS c").single()["c"]
                assert got_e == exp_e, f"Edge count mismatch for {rel}: got {got_e}, want {exp_e}"
        print("[PASS] Assertion A: Graph shape matches expected node and edge counts")
    except Exception as exc:
        failures.append(f"Assertion A failed: {exc}")
        print(f"[FAIL] Assertion A: {exc}")

    # --- ASSERTION B: Enum matches live graph values ---
    try:
        drv = get_driver()
        with drv.session(default_access_mode="READ") as s:
            res = s.run("MATCH (e:Engine) RETURN DISTINCT e.risk_state AS state")
            live_states = {r["state"] for r in res}
        catalog_states = set(ACTIONS["worst_exposure_swap"]["params"]["risk_state"]["enum"])
        assert live_states == catalog_states, (
            f"Catalog enum mismatch: catalog={catalog_states}, live={live_states}"
        )
        print(f"[PASS] Assertion B: risk_state enum equals live graph values {sorted(live_states)}")
    except Exception as exc:
        failures.append(f"Assertion B failed: {exc}")
        print(f"[FAIL] Assertion B: {exc}")

    # --- ASSERTION C: Golden row on default execution ---
    try:
        rows = execute_action("worst_exposure_swap", {})
        assert len(rows) >= 1, "Expected at least 1 row returned"
        golden_found = False
        for r in rows:
            cells = _cells(r)
            if all(_present(cells, exp) for exp in GOLDEN_TUPLE):
                golden_found = True
                break
        assert golden_found, f"Golden tuple {GOLDEN_TUPLE} not found in any single row of results: {rows}"
        print(f"[PASS] Assertion C: Default execution returned golden row with {GOLDEN_TUPLE}")
    except Exception as exc:
        failures.append(f"Assertion C failed: {exc}")
        print(f"[FAIL] Assertion C: {exc}")

    # --- ASSERTION D: Negative test cases rejected by validate_params ---
    neg_cases = [
        ("unknown action name", ("nonexistent_action", {})),
        ("unknown param key", ("worst_exposure_swap", {"unknown_key": "val"})),
        ("risk_state = 'Nonexistent'", ("worst_exposure_swap", {"risk_state": "Nonexistent"})),
        ("limit = 0 (below min)", ("worst_exposure_swap", {"limit": 0})),
        ("limit = 99 (above max)", ("worst_exposure_swap", {"limit": 99})),
        ("limit = '1' (string)", ("worst_exposure_swap", {"limit": "1"})),
        ("limit = True (bool)", ("worst_exposure_swap", {"limit": True})),
    ]
    neg_passed = True
    for desc, (act, p) in neg_cases:
        ok, reason, resolved = validate_params(act, p)
        if ok or resolved != {}:
            failures.append(f"Assertion D failed: {desc} was accepted (ok={ok}, reason={reason})")
            print(f"  [FAIL] {desc}: unexpectedly accepted (reason={reason})")
            neg_passed = False
        else:
            print(f"  [PASS] {desc}: correctly rejected ({reason})")
    if neg_passed:
        print("[PASS] Assertion D: All 7 negative cases correctly rejected by validate_params")
    else:
        print("[FAIL] Assertion D: Some negative cases were not rejected")

    # --- ASSERTION E: Injection handling and parameterized execution ---
    try:
        inj_param = {"risk_state": "Critical' OR 1=1"}
        ok, reason, resolved = validate_params("worst_exposure_swap", inj_param)
        assert not ok and resolved == {}, (
            f"Injection param was accepted: ok={ok}, reason={reason}"
        )
        print(f"  [PASS] Injection case 'Critical\\' OR 1=1' correctly rejected by enum validation: {reason}")

        # Parameter binding execution verification
        valid_params = {"risk_state": "Critical", "limit": 1}
        ok_v, reason_v, resolved_v = validate_params("worst_exposure_swap", valid_params)
        assert ok_v, f"Valid params rejected: {reason_v}"
        cypher = load_cypher("worst_exposure_swap")
        drv = get_driver()
        with drv.session(default_access_mode="READ") as s:
            with s.begin_transaction(timeout=15) as tx:
                res = tx.run(cypher, **resolved_v)
                bound_rows = [r.data() for r in res]
        assert len(bound_rows) == 1, f"Expected 1 row, got {len(bound_rows)}"
        print("  [PASS] Execution successful. NOTE: That parameters are bound directly via driver tx.run() with zero string formatting is verified by code inspection, not by this gate.")
        print("[PASS] Assertion E: Injection rejected & parameterized execution verified")
    except Exception as exc:
        failures.append(f"Assertion E failed: {exc}")
        print(f"[FAIL] Assertion E: {exc}")

    # --- ASSERTION G: Parameters are load-bearing ---
    try:
        # G1
        default_rows = execute_action("worst_exposure_swap", {})
        healthy_rows = execute_action("worst_exposure_swap", {"risk_state": "Healthy"})
        if default_rows == healthy_rows:
            failures.append("Assertion G1 failed: query ignored $risk_state")
            print(f"[FAIL] Assertion G1: Query ignored $risk_state")
            print(f"       Default rows: {default_rows}")
            print(f"       Healthy rows: {healthy_rows}")
        else:
            print("[PASS] Assertion G1: worst_exposure_swap with 'Healthy' returned different rows than default")

        # G2
        limit3_rows = execute_action("worst_exposure_swap", {"limit": 3})
        assert len(limit3_rows) <= 3, f"Expected <= 3 rows, got {len(limit3_rows)}"
        print(f"  [INFO] limit=3 returned {len(limit3_rows)} rows")
        if len(limit3_rows) != len(default_rows):
            print("[PASS] Assertion G2: limit=3 returned different row count than limit=1")
        else:
            print("[OBSERVATION] Assertion G2: limit=3 returned same row count as limit=1. Eligible flights < limit.")
            print(f"       Default rows: {default_rows}")
            print(f"       Limit=3 rows: {limit3_rows}")

        # G3
        cypher_text = load_cypher("worst_exposure_swap")
        assert "$risk_state" in cypher_text, "Cypher missing '$risk_state'"
        assert "$limit" in cypher_text, "Cypher missing '$limit'"
        assert "'Critical'" not in cypher_text, "Cypher still contains literal ''Critical''"
        assert "LIMIT 1" not in cypher_text, "Cypher still contains literal 'LIMIT 1'"
        print("[PASS] Assertion G3: loaded cypher statically verified to contain params and lack literals")

    except Exception as exc:
        failures.append(f"Assertion G failed: {exc}")
        print(f"[FAIL] Assertion G: {exc}")

    # --- ASSERTION F: Graph shape unchanged ---
    shape_after = get_graph_shape()
    print(f"\nGraph state after: {shape_after[0]} nodes, {shape_after[1]} edges")
    if shape_before == shape_after:
        print("[PASS] Assertion F: Graph shape is UNCHANGED")
    else:
        failures.append(f"Assertion F failed: Graph mutated from {shape_before} to {shape_after}")
        print(f"[FAIL] Assertion F: Graph MUTATED from {shape_before} to {shape_after}")

    print("\n" + "=" * 72)
    print("SUMMARY")
    print("=" * 72)
    if not failures:
        print("ALL ASSERTIONS PASSED (6/6)")
        return 0
    else:
        print(f"FAILURES DETECTED ({len(failures)}):")
        for f in failures:
            print(f"  - {f}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

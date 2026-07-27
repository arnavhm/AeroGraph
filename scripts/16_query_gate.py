# scripts/16_query_gate.py
from _env import require_venv

require_venv()
import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()
QUERY = open("cypher/killer_query.cypher").read()
GOOD, MISS = "2026-06-15T13:25:00", "2026-06-15T13:35:00"

d = GraphDatabase.driver(
    os.environ["NEO4J_URI"],
    auth=(
        os.getenv("NEO4J_USERNAME") or os.environ["NEO4J_USER"],
        os.environ["NEO4J_PASSWORD"],
    ),
)


def run(s, q=None):
    return [r.data() for r in s.run(q or QUERY)]


def set_ready(s, tail, iso):
    s.run("MATCH (a:Aircraft {tail:$t}) SET a.ready_at = datetime($v)", t=tail, v=iso)


def assert_answer(s, label):
    rows = run(s)
    assert len(rows) == 1, f"{label}: expected 1 row, got {len(rows)}"
    r = rows[0]
    assert r["flight"] == "AG101", f"{label}: flight={r['flight']}"
    assert r["replacement_tail"] == "G-AGSA", f"{label}: tail={r['replacement_tail']}"
    assert r["engine"] == 24 and r["engine_state"] == "Critical"
    assert abs(r["exposure_score"] - 1.010777147894676) < 1e-12
    assert r["swap_at"] == "MX-LHR" and r["arrives_at"] == "EHAM"
    print(f"  {label:24} AG101 / G-AGSA / eng 24 / {r['exposure_score']:.6f}")


with d.session() as s:
    set_ready(s, "G-AGSA", GOOD)  # known state, regardless of how we arrived
    try:
        assert_answer(s, "1-4 baseline")

        set_ready(s, "G-AGSA", MISS)  # test 5
        rows = run(s)
        assert len(rows) == 0, f"test 5: expected 0 rows, got {len(rows)}"
        print("  5 refusal              0 rows")
    finally:
        set_ready(s, "G-AGSA", GOOD)  # restore even if an assert fires

    assert_answer(s, "restore verified")

    # negative controls: each sabotage must break in the predicted way
    no_filter = QUERY.replace("WHERE e.risk_state = 'Critical'", "")
    top = run(s, no_filter)
    assert top and top[0]["flight"] == "AG103", (
        f"filter not load-bearing: without it, winner is {top[0]['flight'] if top else 'none'}"
    )
    print(f"  sabotage: no filter    AG103 wins at {top[0]['exposure_score']:.4f}")

    loose = QUERY.replace(
        "<= f.scheduled_departure", "<= f.scheduled_departure + duration({minutes:10})"
    )
    assert len(run(s, loose)) == 2, (
        "clock not load-bearing: G-AGSB should qualify at +10min"
    )
    print("  sabotage: clock +10m   2 rows (G-AGSB qualifies)")

print("QUERY GATE PASS")
d.close()

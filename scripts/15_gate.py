# scripts/15_gate.py
from _env import require_venv

require_venv()
import os
from dotenv import load_dotenv
from neo4j import GraphDatabase
import neo4j.time

load_dotenv()
d = GraphDatabase.driver(
    os.environ["NEO4J_URI"],
    auth=(
        os.getenv("NEO4J_USERNAME") or os.environ["NEO4J_USER"],
        os.environ["NEO4J_PASSWORD"],
    ),
)

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

with d.session() as s:
    for label, n in EXP_NODES.items():
        got = s.run(f"MATCH (x:{label}) RETURN count(x) AS c").single()["c"]
        assert got == n, f"{label}: {got} != {n}"
        print(f"  {label:16} {got}")

    for rel, n in EXP_EDGES.items():
        got = s.run(f"MATCH ()-[r:{rel}]->() RETURN count(r) AS c").single()["c"]
        assert got == n, f"{rel}: {got} != {n}"
        print(f"  {rel:16} {got}")

    # THE one that counts can't catch
    r = s.run("MATCH (a:Aircraft {tail:'G-AGSA'}) RETURN a.ready_at AS t").single()["t"]
    assert isinstance(r, neo4j.time.DateTime), (
        f"ready_at is {type(r).__name__}, not DateTime"
    )
    print(f"  ready_at type    {type(r).__name__}  {r}")

    f = s.run(
        "MATCH (f:FlightRoute {flight_no:'AG101'}) RETURN f.scheduled_departure AS t"
    ).single()["t"]
    assert isinstance(f, neo4j.time.DateTime), (
        f"scheduled_departure is {type(f).__name__}"
    )
    print(f"  departure type   {type(f).__name__}  {f}")

    # duration arithmetic actually works in Cypher
    ok = s.run("""MATCH (a:Aircraft {tail:'G-AGSA'})-[:LOCATED_AT]->(:Airport)<-[:SITUATED_AT]-(h:MaintenanceHub)
                  MATCH (f:FlightRoute {flight_no:'AG101'})
                  RETURN a.ready_at + duration({minutes:h.min_swap_duration_minutes})
                         <= f.scheduled_departure AS feasible""").single()["feasible"]
    assert ok is True, "G-AGSA should be feasible (13:25+60=14:25 <= 14:30)"

    no = s.run("""MATCH (a:Aircraft {tail:'G-AGSB'})-[:LOCATED_AT]->(:Airport)<-[:SITUATED_AT]-(h:MaintenanceHub)
                  MATCH (f:FlightRoute {flight_no:'AG101'})
                  RETURN a.ready_at + duration({minutes:h.min_swap_duration_minutes})
                         <= f.scheduled_departure AS feasible""").single()["feasible"]
    assert no is False, "G-AGSB should be infeasible (13:35+60=14:35 > 14:30)"
    print(f"  near-miss        G-AGSA feasible={ok}  G-AGSB feasible={no}")

    e = s.run(
        "MATCH (e:Engine {engine_id:24}) RETURN e.risk_score AS r, e.risk_state AS s"
    ).single()
    assert abs(e["r"] - 0.425053) < 1e-6 and e["s"] == "Critical"
    a = s.run(
        "MATCH (a:Airport {icao:'EHAM'}) RETURN a.expected_wx_delay_min_per_arrival AS w"
    ).single()["w"]
    assert abs(a - 2.378) < 1e-9
    print(f"  eng 24 {e['r']:.6f} {e['s']} | EHAM {a}")

print("GATE PASS")
d.close()

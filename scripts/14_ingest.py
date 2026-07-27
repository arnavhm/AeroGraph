# scripts/14_ingest.py
from _env import require_venv

require_venv()
import os, csv, json
from datetime import datetime
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()
REG = json.load(open("data/mock_fleet_registry.json"))
ENG = {
    int(r["engine_id"]): r
    for r in csv.DictReader(open("data/interim/fd001_engines.csv"))
}
DT = lambda s: datetime.fromisoformat(s)

CONSTRAINTS = [
    "CREATE CONSTRAINT airport_icao IF NOT EXISTS FOR (a:Airport) REQUIRE a.icao IS UNIQUE",
    "CREATE CONSTRAINT engine_id IF NOT EXISTS FOR (e:Engine) REQUIRE e.engine_id IS UNIQUE",
    "CREATE CONSTRAINT aircraft_tail IF NOT EXISTS FOR (a:Aircraft) REQUIRE a.tail IS UNIQUE",
    "CREATE CONSTRAINT flight_no IF NOT EXISTS FOR (f:FlightRoute) REQUIRE f.flight_no IS UNIQUE",
    "CREATE CONSTRAINT hub_code IF NOT EXISTS FOR (h:MaintenanceHub) REQUIRE h.hub_code IS UNIQUE",
]


def ingest(tx):
    tx.run("MATCH (n) DETACH DELETE n")
    m = REG["meta"]

    for a in REG["airports"]:
        tx.run(
            """CREATE (:Airport {icao:$icao,
                   expected_wx_delay_min_per_arrival:$wx,
                   source:'EUROCONTROL', metric:'arrival ATFM weather delay',
                   window_days:365, snapshot_date:$snap})""",
            icao=a["icao"],
            wx=a["expected_wx_delay_min_per_arrival"],
            snap=m["snapshot_date"],
        )

    for h in REG["maintenance_hubs"]:
        tx.run(
            """MATCH (a:Airport {icao:$apt})
                  CREATE (h:MaintenanceHub {hub_code:$code,
                          min_swap_duration_minutes:$mins, supports_engine_swap:true})
                  CREATE (h)-[:SITUATED_AT]->(a)""",
            apt=h["airport"],
            code=h["hub_code"],
            mins=h["min_swap_duration_minutes"],
        )

    for ac in REG["aircraft"]:
        tx.run(
            """MATCH (apt:Airport {icao:$loc})
                  CREATE (a:Aircraft {tail:$tail, is_mock:true,
                          ready_at: CASE WHEN $ready IS NULL THEN NULL ELSE datetime($ready) END})
                  CREATE (a)-[:LOCATED_AT]->(apt)""",
            tail=ac["tail"],
            loc=ac["located_at"],
            ready=DT(ac["ready_at"]) if ac.get("ready_at") else None,
        )

        for pos, eid in enumerate(ac["engines"], start=1):
            e = ENG[eid]
            tx.run(
                """MATCH (a:Aircraft {tail:$tail})
                      CREATE (e:Engine {engine_id:$eid, dataset_id:'FD001',
                              risk_score:$rs, risk_state:$st, rul_cycles:$rul,
                              health_index:$hi, ci_lower:$lo, ci_upper:$hi2,
                              model_name:$mn, source:'EngineWatch /api/predict',
                              source_commit:'ecfcab5e', fetched_at:'2026-07-22'})
                      CREATE (e)-[:INSTALLED_ON {position:$pos}]->(a)""",
                tail=ac["tail"],
                eid=eid,
                pos=pos,
                rs=float(e["risk_score"]),
                st=e["risk_state"],
                rul=float(e["rul_cycles"]),
                hi=float(e["health_index"]),
                lo=float(e["ci_lower"]),
                hi2=float(e["ci_upper"]),
                mn=e["model_name"],
            )

    for f in REG["flights"]:
        tx.run(
            """MATCH (o:Airport {icao:$o}), (d:Airport {icao:$d})
                  CREATE (fl:FlightRoute {flight_no:$no,
                          origin_icao:$o, destination_icao:$d,
                          scheduled_departure: datetime($dep),
                          scheduled_arrival: datetime($arr),
                          schedule_basis:'synthetic-adversarial'})
                  CREATE (fl)-[:DEPARTS_FROM]->(o)
                  CREATE (fl)-[:ARRIVES_AT]->(d)""",
            no=f["flight_no"],
            o=f["origin"],
            d=f["destination"],
            dep=DT(f["scheduled_departure"]),
            arr=DT(f["scheduled_arrival"]),
        )

    for ac in REG["aircraft"]:
        if ac["assigned_flight"]:
            tx.run(
                """MATCH (a:Aircraft {tail:$tail}), (f:FlightRoute {flight_no:$fno})
                      CREATE (a)-[:ASSIGNED_TO]->(f)""",
                tail=ac["tail"],
                fno=ac["assigned_flight"],
            )


with GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.getenv("NEO4J_USERNAME") or os.environ["NEO4J_USER"],
              os.environ["NEO4J_PASSWORD"])) as d:
    with d.session() as s:
        for c in CONSTRAINTS:
            s.run(c)
        s.execute_write(ingest)
        print("nodes:", s.run("MATCH (n) RETURN count(n) AS c").single()["c"])
        print("edges:", s.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"])

from _env import require_venv; require_venv()
import json, csv, sys
from datetime import datetime, timedelta

def load_engines():
    with open("data/interim/fd001_engines.csv") as f:
        return {int(r["engine_id"]): float(r["risk_score"]) for r in csv.DictReader(f)}

def load_registry():
    with open("data/mock_fleet_registry.json") as f:
        return json.load(f)

def run_checks():
    engines = load_engines()
    reg = load_registry()
    
    print("--- VALIDATING MOCK FLEET REGISTRY ---")
    # Check 1: 16 unique engine IDs
    seen_ids = set()
    for ac in reg["aircraft"]:
        for eid in ac["engines"]:
            seen_ids.add(eid)
    
    print(f"Check 1: Engine Count = {len(seen_ids)} (Expected 16)")
    if len(seen_ids) != 16: sys.exit("FAIL: Not exactly 16 unique engine IDs")
    
    # Check 2: every aircraft's first engine strictly worse than its second
    ok2 = True
    print("Check 2: Aircraft worst-engine verification")
    for ac in reg["aircraft"]:
        e1, e2 = ac["engines"]
        r1, r2 = engines[e1], engines[e2]
        if r1 <= r2:
            print(f"  FAIL: Aircraft {ac['tail']} has eng 1 ({r1:.6f}) better than or equal to eng 2 ({r2:.6f})")
            ok2 = False
        else:
            print(f"  OK: Aircraft {ac['tail']} eng 1 ({r1:.6f}) > eng 2 ({r2:.6f})")
    if not ok2: sys.exit("FAIL: Check 2 failed")
    
    # Check 3: every located_at and flight endpoint in the airport list
    apts = {a["icao"] for a in reg["airports"]}
    ok3 = True
    print("Check 3: Airport coverage")
    for ac in reg["aircraft"]:
        if ac["located_at"] not in apts:
            print(f"  FAIL: AC {ac['tail']} located_at {ac['located_at']} not in airports")
            ok3 = False
    for f in reg["flights"]:
        if f["origin"] not in apts or f["destination"] not in apts:
            print(f"  FAIL: Flight {f['flight_no']} endpoints not in airports")
            ok3 = False
    if not ok3: sys.exit("FAIL: Check 3 failed")
    else: print("  OK: All locations present in airports list")
    
    # Check 4: 13:25 + 60 <= 14:30 < 13:35 + 60
    print("Check 4: Swap time boundary verification (Near-miss arithmetic)")
    fmt = "%Y-%m-%dT%H:%M:%S"
    dep = datetime.strptime("2026-06-15T14:30:00", fmt)
    r_sa = datetime.strptime("2026-06-15T13:25:00", fmt)
    r_sb = datetime.strptime("2026-06-15T13:35:00", fmt)
    
    hub_time = next(h["min_swap_duration_minutes"] for h in reg["maintenance_hubs"] if h["airport"] == "EGLL")
    swap_dur = timedelta(minutes=hub_time)
    
    cond1 = (r_sa + swap_dur) <= dep
    cond2 = dep < (r_sb + swap_dur)
    
    print(f"  G-AGSA ready {r_sa.time()} + {hub_time}m = {(r_sa+swap_dur).time()} <= dep {dep.time()} ? {cond1}")
    print(f"  G-AGSB ready {r_sb.time()} + {hub_time}m = {(r_sb+swap_dur).time()} >  dep {dep.time()} ? {cond2}")
    if not (cond1 and cond2):
        sys.exit("FAIL: Check 4 time boundaries failed")
    
    print("\nCheck 5: Domain Logic & Scoring Assumptions")
    STATES = {int(r["engine_id"]): r["risk_state"] for r in csv.DictReader(open("data/interim/fd001_engines.csv"))}
    apts = {a["icao"]: a for a in reg["airports"]}
    hubs = {h["airport"]: h["min_swap_duration_minutes"] for h in reg["maintenance_hubs"]}
    flights = {f["flight_no"]: f for f in reg["flights"]}
    
    ids = [e for a in reg["aircraft"] for e in a["engines"]]
    assert len(set(ids)) == 16, f"duplicate engine ids: {len(set(ids))} unique"
    
    for a in reg["aircraft"]:
        st = [STATES[e] for e in a["engines"]]
        if a["assigned_flight"] is None:
            assert set(st) == {"Healthy"}, f"spare {a['tail']} not all-Healthy: {st}"
            assert a["located_at"] in hubs, f"spare {a['tail']} not at a hub"
        print(f"  {a['tail']:8} {a['engines']} {st}")
    
    assert STATES[24] == "Critical" and STATES[56] == "Critical"
    assert STATES[63] == "Degrading", "AG103 trap dead: engine 63 must be Degrading"
    
    for f in reg["flights"]:
        assert f["origin"] in apts and f["destination"] in apts, f["flight_no"]
    assert flights["AG101"]["origin"] in hubs, "AG101 origin has no hub — swap impossible"
    
    def score(tail):
        a = next(x for x in reg["aircraft"] if x["tail"] == tail)
        worst = max(engines[e] for e in a["engines"])
        return worst * apts[flights[a["assigned_flight"]]["destination"]]["expected_wx_delay_min_per_arrival"]
    
    assert score("G-AGDA") > score("G-AGDB"), "TEST 1 DEAD: AG101 does not beat AG102"
    assert score("G-AGDC") > score("G-AGDA"), "AG103 trap dead: it must outscore AG101 pre-filter"
    print(f"  AG101 {score('G-AGDA'):.4f} > AG102 {score('G-AGDB'):.4f} | AG103 {score('G-AGDC'):.4f} (filtered)")
    
    print("ALL VALIDATION CHECKS PASS")

run_checks()

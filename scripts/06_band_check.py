from _env import require_venv; require_venv()
import requests, collections

BASE = "https://enginewatch.tech/api/predict"
bands, rows, fails = collections.defaultdict(list), [], []

for eid in range(1, 101):
    try:
        d = requests.get(BASE, params={"engine_id": eid, "dataset_id": "FD001"},
                         timeout=20).json()
        rows.append(d)
        bands[d["risk_state"]].append((d["risk_score"], eid))
    except Exception as e:
        fails.append((eid, repr(e)))

print("fetched:", len(rows), " failed:", len(fails), fails[:3])

for state in ("Healthy", "Warning", "Critical"):
    v = sorted(bands.get(state, []))
    print(f"{state:9} ABSENT" if not v else
          f"{state:9} n={len(v):3}  min={v[0][0]:.6f} (eng {v[0][1]})  max={v[-1][0]:.6f} (eng {v[-1][1]})")

present = [s for s in ("Healthy", "Warning", "Critical") if bands.get(s)]
ok = True
for a, b in zip(present, present[1:]):
    amax, bmin = max(x[0] for x in bands[a]), min(x[0] for x in bands[b])
    if amax >= bmin: ok = False
    print(f"{a}.max={amax:.6f} vs {b}.min={bmin:.6f} -> {'OK' if amax < bmin else 'OVERLAP'}")
print("BAND INTEGRITY:", "PASS" if ok else "FAIL")

off = [d["engine_id"] for d in rows if abs((1 - d["health_index"]) - d["risk_score"]) > 1e-9]
print("engines where risk_score != 1 - health_index:", len(off), off[:10])

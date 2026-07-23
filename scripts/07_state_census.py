from _env import require_venv; require_venv()
import requests, collections

BASE = "https://enginewatch.tech/api/predict"
rows = []
for eid in range(1, 101):
    rows.append(requests.get(BASE, params={"engine_id": eid, "dataset_id": "FD001"},
                             timeout=20).json())

states = collections.Counter(r["risk_state"] for r in rows)
print("total:", len(rows))
for s, n in states.most_common():
    v = sorted(r["risk_score"] for r in rows if r["risk_state"] == s)
    print(f"  {str(s):20} n={n:3}  min={v[0]:.6f}  max={v[-1]:.6f}")

# order by observed min, then check disjointness across EVERY state present
order = sorted(states, key=lambda s: min(r["risk_score"] for r in rows if r["risk_state"] == s))

ok = True
for a, b in zip(order, order[1:]):
    amax = max(r["risk_score"] for r in rows if r["risk_state"] == a)
    bmin = min(r["risk_score"] for r in rows if r["risk_state"] == b)
    if amax >= bmin: ok = False
    print(f"{str(a)}.max={amax:.6f} vs {str(b)}.min={bmin:.6f} -> {'OK' if amax < bmin else 'OVERLAP'}")

print("STATES:", list(order))
print("BAND INTEGRITY (all states):", "PASS" if ok else "FAIL")

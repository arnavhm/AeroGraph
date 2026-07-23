from _env import require_venv; require_venv()
import requests, csv

rows = []
for eid in range(1, 101):
    d = requests.get("https://enginewatch.tech/api/predict",
                     params={"engine_id": eid, "dataset_id": "FD001"}, timeout=20).json()
    rows.append(d)

rows.sort(key=lambda d: d["risk_score"], reverse=True)

with open("data/interim/fd001_engines.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader(); w.writerows(rows)

print(f"{'eng':>4} {'risk':>9} {'state':<10} {'rul':>8}")
for d in rows[:12]:
    print(f"{d['engine_id']:>4} {d['risk_score']:>9.6f} {d['risk_state']:<10} {d['rul_cycles']:>8.2f}")
print("   ...")
for d in rows[-8:]:
    print(f"{d['engine_id']:>4} {d['risk_score']:>9.6f} {d['risk_state']:<10} {d['rul_cycles']:>8.2f}")

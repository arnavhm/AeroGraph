from _env import require_venv; require_venv()
import csv
rows = [r for r in csv.DictReader(open("data/interim/fd001_engines.csv"))
        if r["risk_state"] == "Critical"]
rows.sort(key=lambda r: float(r["risk_score"]))
print(f"{'eng':>4} {'risk':>9} {'rul':>7}")
for r in rows:
    print(f"{r['engine_id']:>4} {float(r['risk_score']):>9.6f} {float(r['rul_cycles']):>7.2f}")

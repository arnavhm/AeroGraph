from _env import require_venv; require_venv()
import csv
rows = list(csv.DictReader(open("data/interim/fd001_engines.csv")))
for state in ("Healthy", "Degrading"):
    sel = sorted((r for r in rows if r["risk_state"] == state),
                 key=lambda r: float(r["risk_score"]))
    print(f"\n{state}  (n={len(sel)})")
    for r in sel:
        print(f"  eng {r['engine_id']:>3}  risk {float(r['risk_score']):.6f}  rul {float(r['rul_cycles']):>7.2f}")

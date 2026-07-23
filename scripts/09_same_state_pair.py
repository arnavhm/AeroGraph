from _env import require_venv; require_venv()
import csv, itertools

rows = list(csv.DictReader(open("data/interim/fd001_engines.csv")))
crit = sorted((r for r in rows if r["risk_state"] == "Critical"),
              key=lambda r: float(r["risk_score"]))

print("Closest same-state (Critical) adjacent pairs:")
pairs = sorted(zip(crit, crit[1:]),
               key=lambda p: float(p[1]["risk_score"]) - float(p[0]["risk_score"]))
for lo, hi in pairs[:5]:
    d = float(hi["risk_score"]) - float(lo["risk_score"])
    print(f"  diff {d:.6f} | eng {lo['engine_id']:>3} {float(lo['risk_score']):.6f}"
          f"  vs  eng {hi['engine_id']:>3} {float(hi['risk_score']):.6f}")

healthy = sorted((r for r in rows if r["risk_state"] == "Healthy"),
                 key=lambda r: float(r["risk_score"]))
print("\nHealthiest (for the second engine on each aircraft):")
for r in healthy[:6]:
    print(f"  eng {r['engine_id']:>3} {float(r['risk_score']):.6f}  rul {float(r['rul_cycles']):.1f}")

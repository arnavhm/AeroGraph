from _env import require_venv; require_venv()
import pandas as pd

SNAPSHOT = pd.Timestamp("2026-06-15")
df = pd.read_parquet("data/interim/eurocontrol_atfm.parquet")
df["DLY_APT_ARR_W_1"] = df["DLY_APT_ARR_W_1"].fillna(0)

w = df[(df["APT_ICAO"] == "LPPR") &
       (df["FLT_DATE"] > SNAPSHOT - pd.Timedelta(days=365)) &
       (df["FLT_DATE"] <= SNAPSHOT)]

total = w["DLY_APT_ARR_W_1"].sum()
top10 = w.nlargest(10, "DLY_APT_ARR_W_1")[["FLT_DATE","FLT_ARR_1","DLY_APT_ARR_W_1"]]

print(top10.to_string(index=False))
print("annual weather minutes:", total)
print("top-10-day share:", round(top10['DLY_APT_ARR_W_1'].sum() / total, 3))

# inherited-assumption check: is fillna(0) still safe for THIS airport?
zero = w[w["DLY_APT_ARR_W_1"] == 0]
print("zero-wx rows with arrivals populated:", round(zero['FLT_ARR_1'].notna().mean(), 3))
print("mean arrivals on zero-wx days:", round(zero['FLT_ARR_1'].mean(), 1))

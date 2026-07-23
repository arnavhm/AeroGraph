from _env import require_venv; require_venv()
import pandas as pd

SNAPSHOT = "2026-06-15"
df = pd.read_parquet("data/interim/eurocontrol_atfm.parquet")

day = df[df["FLT_DATE"] == SNAPSHOT].copy()
day["DLY_APT_ARR_W_1"] = day["DLY_APT_ARR_W_1"].fillna(0)

day["wx_min_per_arr"] = day["DLY_APT_ARR_W_1"] / day["FLT_ARR_1"]

cols = ["APT_ICAO", "APT_NAME", "STATE_NAME",
        "FLT_ARR_1", "DLY_APT_ARR_W_1", "wx_min_per_arr"]

busy = day[day["FLT_ARR_1"] >= 200].sort_values("wx_min_per_arr", ascending=False)
print(busy[cols].head(10).to_string(index=False))
print("---")
print(busy[cols].tail(5).to_string(index=False))

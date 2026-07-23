from _env import require_venv; require_venv()
import pandas as pd

SNAPSHOT = pd.Timestamp("2026-06-15")
WINDOW = 365
MIN_AVG_ARRIVALS = 150      # volume floor, applied where it was missing

df = pd.read_parquet("data/interim/eurocontrol_atfm.parquet")
df["DLY_APT_ARR_W_1"] = df["DLY_APT_ARR_W_1"].fillna(0)

hist = df[(df["FLT_DATE"] > SNAPSHOT - pd.Timedelta(days=WINDOW)) &
          (df["FLT_DATE"] <= SNAPSHOT)]

agg = (hist.groupby(["APT_ICAO", "APT_NAME"])
           .agg(days=("FLT_DATE", "count"),
                wx_days=("DLY_APT_ARR_W_1", lambda s: (s > 0).sum()),
                wx_min_total=("DLY_APT_ARR_W_1", "sum"),
                arr_total=("FLT_ARR_1", "sum"))
           .reset_index())

agg = agg[agg["days"] >= 350]                       # drop airports with gaps
agg["avg_arr"] = (agg["arr_total"] / agg["days"]).round(0)
agg = agg[agg["avg_arr"] >= MIN_AVG_ARRIVALS]       # drop small denominators

agg["weather_delay_risk"]  = (agg["wx_days"] / agg["days"]).round(3)
agg["wx_min_per_arr"]      = (agg["wx_min_total"] / agg["arr_total"]).round(3)
agg["wx_min_per_wx_day"]   = (agg["wx_min_total"] / agg["wx_days"].where(agg["wx_days"] > 0)).round(1)

cols = ["APT_ICAO","APT_NAME","avg_arr","weather_delay_risk","wx_min_per_arr","wx_min_per_wx_day"]
out = agg.sort_values("weather_delay_risk", ascending=False)

print("n airports passing filters:", len(out))
print(out[cols].head(12).to_string(index=False))
print("...")
print(out[cols].tail(12).to_string(index=False))

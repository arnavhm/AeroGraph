from _env import require_venv; require_venv()
import pandas as pd

SNAPSHOT = pd.Timestamp("2026-06-15")
WINDOW_DAYS = 365
SHORTLIST = ["LPPR", "EFHK", "EGSS", "LEMD", "ESSA", "LTFM"]  # High: LPPR, EFHK; Mid: EGSS, LEMD; Low: ESSA, LTFM

df = pd.read_parquet("data/interim/eurocontrol_atfm.parquet")
df["DLY_APT_ARR_W_1"] = df["DLY_APT_ARR_W_1"].fillna(0)

hist = df[(df["APT_ICAO"].isin(SHORTLIST)) &
          (df["FLT_DATE"] > SNAPSHOT - pd.Timedelta(days=WINDOW_DAYS)) &
          (df["FLT_DATE"] <= SNAPSHOT)]

risk = (hist.groupby("APT_ICAO")
            .agg(days=("FLT_DATE", "count"),
                 wx_days=("DLY_APT_ARR_W_1", lambda s: (s > 0).sum()),
                 wx_min_total=("DLY_APT_ARR_W_1", "sum"),
                 arrivals_total=("FLT_ARR_1", "sum")))

risk["weather_delay_risk"] = (risk["wx_days"] / risk["days"]).round(3)
risk["wx_min_per_arrival"] = (risk["wx_min_total"] / risk["arrivals_total"]).round(3)

print(risk[["days", "wx_days", "weather_delay_risk", "wx_min_per_arrival"]].to_string())

from _env import require_venv; require_venv()
import pandas as pd

SRC = "data/raw/Airport_Arrival_ATFM_Delay.xlsx"
OUT = "data/interim/eurocontrol_atfm.parquet"

df = pd.read_excel(SRC, sheet_name="DATA")
df["FLT_DATE"] = pd.to_datetime(df["FLT_DATE"])
df.to_parquet(OUT, index=False)

print(df.shape)
print(df["FLT_DATE"].min(), "->", df["FLT_DATE"].max())

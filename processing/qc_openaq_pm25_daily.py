import pandas as pd
from pathlib import Path

INPUT = Path(
    "data/processed/mumbai_openaq_pm25_daily_sensor_history.csv"
)

OUTPUT = Path(
    "data/processed/mumbai_openaq_pm25_daily_qc.csv"
)

df = pd.read_csv(INPUT)

df["date_start_utc"] = pd.to_datetime(
    df["date_start_utc"],
    errors="coerce",
    utc=True
)

df["date_end_utc"] = pd.to_datetime(
    df["date_end_utc"],
    errors="coerce",
    utc=True
)

df["daily_value"] = pd.to_numeric(
    df["daily_value"],
    errors="coerce"
)

df["coverage_pct"] = pd.to_numeric(
    df["coverage_pct"],
    errors="coerce"
)

# ------------------------------------------------------------
# 1. Restrict to contemporary sensor network
# ------------------------------------------------------------

START = pd.Timestamp(
    "2025-02-18",
    tz="UTC"
)

END = pd.Timestamp(
    "2026-09-18",
    tz="UTC"
)

df = df[
    (df["date_start_utc"] >= START) &
    (df["date_start_utc"] < END)
].copy()

# ------------------------------------------------------------
# 2. Basic validity checks
# ------------------------------------------------------------

df["valid_timestamp"] = (
    df["date_start_utc"].notna()
)

df["valid_value"] = (
    df["daily_value"].notna()
)

# PM2.5 concentration cannot be negative.
df["non_negative"] = (
    df["daily_value"] >= 0
)

# Extremely high values are retained in the raw dataset,
# but marked as suspicious rather than silently deleting them.
df["extreme_value"] = (
    df["daily_value"] > 500
)

# OpenAQ flag
df["source_flagged"] = (
    df["flagged"]
    .fillna(False)
    .astype(bool)
)

# ------------------------------------------------------------
# 3. Final usability flag
# ------------------------------------------------------------

df["usable_for_lstm"] = (
    df["valid_timestamp"] &
    df["valid_value"] &
    df["non_negative"] &
    (~df["extreme_value"]) &
    (~df["source_flagged"])
)

# ------------------------------------------------------------
# 4. Local date
# ------------------------------------------------------------

df["date"] = (
    df["date_start_utc"]
    .dt.tz_convert("Asia/Kolkata")
    .dt.date
)

# ------------------------------------------------------------
# 5. Sort and save
# ------------------------------------------------------------

df = df.sort_values(
    [
        "urban_ward_code",
        "sensor_id",
        "date_start_utc"
    ]
)

OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True
)

df.to_csv(
    OUTPUT,
    index=False
)

# ------------------------------------------------------------
# REPORT
# ------------------------------------------------------------

print("=" * 70)
print("OPENAQ PM2.5 QUALITY CONTROL")
print("=" * 70)

print("Records after 2025-02-18 filter:", len(df))
print("Sensors:", df["sensor_id"].nunique())
print("Wards:", df["urban_ward_code"].nunique())

print("\nDate range:")
print(df["date_start_utc"].min())
print("→")
print(df["date_start_utc"].max())

print("\nQC flags:")
print(
    "Invalid timestamps:",
    (~df["valid_timestamp"]).sum()
)

print(
    "Missing values:",
    (~df["valid_value"]).sum()
)

print(
    "Negative values:",
    (~df["non_negative"]).sum()
)

print(
    "Extreme values >500:",
    df["extreme_value"].sum()
)

print(
    "OpenAQ flagged:",
    df["source_flagged"].sum()
)

print(
    "Usable for LSTM:",
    df["usable_for_lstm"].sum()
)

print(
    "Excluded:",
    (~df["usable_for_lstm"]).sum()
)

print("\nUsable records by ward:")

print(
    df[df["usable_for_lstm"]]
    ["urban_ward_code"]
    .value_counts()
    .sort_index()
    .to_string()
)

print("\nUsable PM2.5 statistics:")

print(
    df.loc[
        df["usable_for_lstm"],
        "daily_value"
    ].describe().to_string()
)

print("\nSaved:")
print(OUTPUT)

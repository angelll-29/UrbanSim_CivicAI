import pandas as pd
from pathlib import Path

INPUT = Path(
    "data/processed/mumbai_openaq_pm25_daily_qc.csv"
)

OUTPUT = Path(
    "data/processed/mumbai_pm25_ward_daily.csv"
)

df = pd.read_csv(INPUT)

df["date"] = pd.to_datetime(
    df["date"],
    errors="coerce"
)

df["daily_value"] = pd.to_numeric(
    df["daily_value"],
    errors="coerce"
)

df = df[
    df["usable_for_lstm"] == True
].copy()

# Aggregate sensors within each ward and day
ward_daily = (
    df.groupby(
        ["urban_ward_code", "date"]
    )
    .agg(
        pm25_mean=("daily_value", "mean"),
        pm25_median=("daily_value", "median"),
        pm25_min=("daily_value", "min"),
        pm25_max=("daily_value", "max"),
        pm25_std=("daily_value", "std"),
        sensor_count=("sensor_id", "nunique"),
        observation_count=("daily_value", "count")
    )
    .reset_index()
)

# A single contributing sensor has undefined std.
ward_daily["pm25_std"] = (
    ward_daily["pm25_std"].fillna(0)
)

# Date ordering
ward_daily = ward_daily.sort_values(
    ["urban_ward_code", "date"]
)

OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True
)

ward_daily.to_csv(
    OUTPUT,
    index=False
)

print("=" * 70)
print("WARD-LEVEL PM2.5 DATASET")
print("=" * 70)

print("Ward-days:", len(ward_daily))
print(
    "Wards:",
    ward_daily["urban_ward_code"].nunique()
)

print(
    "Date:",
    ward_daily["date"].min(),
    "→",
    ward_daily["date"].max()
)

print("\nRecords by ward:")
print(
    ward_daily["urban_ward_code"]
    .value_counts()
    .sort_index()
    .to_string()
)

print("\nSensor contribution:")
print(
    ward_daily["sensor_count"]
    .value_counts()
    .sort_index()
    .to_string()
)

print("\nWard-level PM2.5 statistics:")
print(
    ward_daily["pm25_mean"]
    .describe()
    .to_string()
)

print("\nSaved:")
print(OUTPUT)

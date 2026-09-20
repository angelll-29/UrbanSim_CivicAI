from pathlib import Path
import pandas as pd

INPUT = Path(
    "data/processed/mumbai_openaq_latest_measurements.csv"
)

OUTPUT = Path(
    "data/processed/mumbai_openaq_latest_measurements_qc.csv"
)

df = pd.read_csv(INPUT)

df["datetime_utc"] = pd.to_datetime(
    df["datetime_utc"],
    utc=True,
    errors="coerce"
)

NOW = pd.Timestamp(
    "2026-09-17T00:00:00Z"
)

df["data_age_hours"] = (
    NOW - df["datetime_utc"]
).dt.total_seconds() / 3600

def classify_age(hours):

    if pd.isna(hours):
        return "INVALID"

    if hours <= 24:
        return "CURRENT_24H"

    if hours <= 72:
        return "RECENT_72H"

    if hours <= 168:
        return "RECENT_7D"

    if hours <= 720:
        return "STALE_30D"

    if hours <= 2160:
        return "STALE_90D"

    return "HISTORICAL"


df["freshness_status"] = (
    df["data_age_hours"]
    .apply(classify_age)
)

# Measurement validity.
df["value"] = pd.to_numeric(
    df["value"],
    errors="coerce"
)

df["value_valid"] = (
    df["value"].notna()
)

# Keep only meaningful environmental parameters.
VALID_PARAMETERS = [
    "pm25",
    "pm10",
    "no2",
    "so2",
    "o3",
    "co",
    "temperature",
    "relativehumidity",
    "wind_speed",
    "wind_direction"
]

df["environmental_parameter"] = (
    df["parameter_name"]
    .isin(VALID_PARAMETERS)
)

df.to_csv(
    OUTPUT,
    index=False
)

print("\nEnvironmental Data Quality")
print("--------------------------")

print("Total measurements:", len(df))

print("\nFreshness:")

print(
    df["freshness_status"]
    .value_counts()
    .to_string()
)

print("\nFreshness by pollutant:")

pollutants = [
    "pm25",
    "pm10",
    "no2",
    "so2",
    "o3",
    "co"
]

print(
    df[
        df["parameter_name"].isin(
            pollutants
        )
    ]
    .groupby(
        [
            "parameter_name",
            "freshness_status"
        ]
    )
    .size()
    .to_string()
)

print("\nLatest observation per pollutant:")

latest = (
    df[
        df["parameter_name"].isin(
            pollutants
        )
    ]
    .sort_values("datetime_utc")
    .groupby("parameter_name")
    .tail(1)
)

print(
    latest[
        [
            "parameter_name",
            "value",
            "unit",
            "datetime_utc",
            "data_age_hours",
            "freshness_status"
        ]
    ].to_string(index=False)
)

print(
    f"\nOutput: {OUTPUT}"
)

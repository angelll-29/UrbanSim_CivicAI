import numpy as np
import pandas as pd
from pathlib import Path

INPUT = Path(
    "data/processed/mumbai_openaq_multivariate_daily_aligned.csv"
)

AUDIT = Path(
    "data/processed/mumbai_openaq_multivariate_history_audit_v2.csv"
)

OUTPUT = Path(
    "data/processed/mumbai_lstm_v2_daily_features.csv"
)

PARAMETERS = [
    "pm25",
    "temperature",
    "relativehumidity",
    "wind_speed",
    "no2",
    "o3",
    "so2",
    "co"
]

EXCLUDED_LOCATIONS = {
    6956,
    6965,
    12039
}

df = pd.read_csv(INPUT)

audit = pd.read_csv(AUDIT)

df["date"] = pd.to_datetime(
    df["date"],
    errors="coerce"
)

audit["common_first_utc"] = pd.to_datetime(
    audit["common_first_utc"],
    errors="coerce",
    utc=True
)

audit["common_last_utc"] = pd.to_datetime(
    audit["common_last_utc"],
    errors="coerce",
    utc=True
)

usable = audit[
    (audit["usable_multivariate"] == True) &
    (~audit["openaq_location_id"].isin(
        EXCLUDED_LOCATIONS
    ))
].copy()

usable_ids = set(
    usable["openaq_location_id"]
    .astype(int)
)

df["openaq_location_id"] = (
    df["openaq_location_id"].astype(int)
)

df = df[
    df["openaq_location_id"].isin(
        usable_ids
    )
].copy()

# ------------------------------------------------------------
# Add cyclic wind direction encoding
# ------------------------------------------------------------

direction = pd.to_numeric(
    df["wind_direction"],
    errors="coerce"
)

radians = np.deg2rad(direction)

df["wind_direction_sin"] = np.sin(
    radians
)

df["wind_direction_cos"] = np.cos(
    radians
)

# ------------------------------------------------------------
# Add seasonal encoding
# ------------------------------------------------------------

day_of_year = (
    df["date"].dt.dayofyear
)

days_in_year = np.where(
    df["date"].dt.is_leap_year,
    366,
    365
)

season_angle = (
    2 *
    np.pi *
    (day_of_year - 1) /
    days_in_year
)

df["day_of_year_sin"] = np.sin(
    season_angle
)

df["day_of_year_cos"] = np.cos(
    season_angle
)

# ------------------------------------------------------------
# Keep required columns
# ------------------------------------------------------------

FEATURES = (
    PARAMETERS +
    [
        "wind_direction_sin",
        "wind_direction_cos",
        "day_of_year_sin",
        "day_of_year_cos"
    ]
)

columns = [
    "openaq_location_id",
    "station_name",
    "urban_ward_code",
    "date"
] + FEATURES

df = df[columns].copy()

df = df.sort_values(
    [
        "openaq_location_id",
        "date"
    ]
)

df.to_csv(
    OUTPUT,
    index=False
)

print("=" * 70)
print("LSTM-V2 FEATURE ENGINEERING")
print("=" * 70)

print(
    "Locations:",
    df["openaq_location_id"].nunique()
)

print(
    "Wards:",
    df["urban_ward_code"].nunique()
)

print(
    "Features:",
    len(FEATURES)
)

print("\nFeatures:")

for i, feature in enumerate(
    FEATURES,
    1
):
    print(
        f"{i:2d}. {feature}"
    )

print("\nRows:", len(df))

print(
    "Date range:",
    df["date"].min().date(),
    "→",
    df["date"].max().date()
)

print("\nSaved:")
print(OUTPUT)

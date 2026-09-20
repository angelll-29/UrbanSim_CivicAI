import pandas as pd
import numpy as np
from pathlib import Path

INPUT = Path(
    "data/processed/mumbai_openaq_multivariate_daily.csv"
)

AUDIT = Path(
    "data/processed/mumbai_openaq_multivariate_history_audit_v2.csv"
)

OUTPUT = Path(
    "data/processed/mumbai_openaq_multivariate_daily_aligned.csv"
)

PARAMETERS = [
    "pm25",
    "temperature",
    "relativehumidity",
    "wind_speed",
    "wind_direction",
    "no2",
    "o3",
    "so2",
    "co"
]

df = pd.read_csv(INPUT)

audit = pd.read_csv(AUDIT)

# ------------------------------------------------------------
# Parse dates
# ------------------------------------------------------------

df["date_start_utc"] = pd.to_datetime(
    df["date_start_utc"],
    errors="coerce",
    utc=True
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

# ------------------------------------------------------------
# Keep only audited usable locations
# ------------------------------------------------------------

usable = audit[
    audit["usable_multivariate"] == True
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
# Attach station-specific common window
# ------------------------------------------------------------

windows = usable[
    [
        "openaq_location_id",
        "common_first_utc",
        "common_last_utc"
    ]
].copy()

df = df.merge(
    windows,
    on="openaq_location_id",
    how="inner"
)

df = df[
    (df["date_start_utc"] >= df["common_first_utc"]) &
    (df["date_start_utc"] <= df["common_last_utc"])
].copy()

print("=" * 70)
print("MULTIVARIATE TEMPORAL QC")
print("=" * 70)

print(
    "Records after common-history filtering:",
    len(df)
)

# ------------------------------------------------------------
# Numeric conversion
# ------------------------------------------------------------

df["value"] = pd.to_numeric(
    df["value"],
    errors="coerce"
)

# ------------------------------------------------------------
# Basic physical validity checks
# ------------------------------------------------------------

invalid_negative = (
    (df["parameter"].isin([
        "pm25",
        "temperature",
        "relativehumidity",
        "wind_speed",
        "wind_direction",
        "no2",
        "o3",
        "so2",
        "co"
    ])) &
    (df["value"] < 0)
)

# PM2.5 and pollutant concentrations:
# exclude clearly impossible >500 values for this model.
extreme_pollution = (
    df["parameter"].isin([
        "pm25",
        "no2",
        "o3",
        "so2",
        "co"
    ]) &
    (df["value"] > 500)
)

# Relative humidity cannot exceed 100%.
invalid_humidity = (
    (df["parameter"] == "relativehumidity") &
    (
        (df["value"] < 0) |
        (df["value"] > 100)
    )
)

# Wind speed cannot be negative.
invalid_wind_speed = (
    (df["parameter"] == "wind_speed") &
    (df["value"] < 0)
)

# Wind direction must be within 0-360.
invalid_wind_direction = (
    (df["parameter"] == "wind_direction") &
    (
        (df["value"] < 0) |
        (df["value"] > 360)
    )
)

invalid = (
    invalid_negative |
    extreme_pollution |
    invalid_humidity |
    invalid_wind_speed |
    invalid_wind_direction
)

print(
    "Invalid values identified:",
    int(invalid.sum())
)

df.loc[invalid, "value"] = np.nan

# ------------------------------------------------------------
# OpenAQ flags
# ------------------------------------------------------------

if "source_flagged" in df.columns:

    flagged = (
        df["source_flagged"]
        .astype(str)
        .str.lower()
        .isin([
            "true",
            "1",
            "yes"
        ])
    )

    print(
        "OpenAQ flagged records:",
        int(flagged.sum())
    )

    df.loc[
        flagged,
        "value"
    ] = np.nan

# ------------------------------------------------------------
# Convert to local calendar date
# ------------------------------------------------------------

df["date"] = (
    df["date_start_utc"]
    .dt.tz_convert("Asia/Kolkata")
    .dt.floor("D")
)

# ------------------------------------------------------------
# Multiple sensors:
# aggregate same location + parameter + day
#
# Circular variables such as wind direction should NOT use
# ordinary arithmetic mean.
# Use circular mean instead.
# ------------------------------------------------------------

def circular_mean(series):

    values = pd.to_numeric(
        series,
        errors="coerce"
    ).dropna().values

    if len(values) == 0:
        return np.nan

    radians = np.deg2rad(values)

    sin_mean = np.mean(
        np.sin(radians)
    )

    cos_mean = np.mean(
        np.cos(radians)
    )

    angle = np.rad2deg(
        np.arctan2(
            sin_mean,
            cos_mean
        )
    )

    return angle % 360


normal_parameters = [
    p for p in PARAMETERS
    if p != "wind_direction"
]

normal = df[
    df["parameter"].isin(
        normal_parameters
    )
].groupby(
    [
        "openaq_location_id",
        "station_name",
        "urban_ward_code",
        "date",
        "parameter"
    ],
    as_index=False
)["value"].mean()

wind = df[
    df["parameter"] == "wind_direction"
].groupby(
    [
        "openaq_location_id",
        "station_name",
        "urban_ward_code",
        "date",
        "parameter"
    ],
    as_index=False
)["value"].agg(
    circular_mean
)

aligned_long = pd.concat(
    [
        normal,
        wind
    ],
    ignore_index=True
)

# ------------------------------------------------------------
# Pivot
# ------------------------------------------------------------

aligned = aligned_long.pivot_table(
    index=[
        "openaq_location_id",
        "station_name",
        "urban_ward_code",
        "date"
    ],
    columns="parameter",
    values="value",
    aggfunc="first"
).reset_index()

aligned.columns.name = None

# Ensure all expected columns exist
for parameter in PARAMETERS:

    if parameter not in aligned.columns:
        aligned[parameter] = np.nan

aligned = aligned[
    [
        "openaq_location_id",
        "station_name",
        "urban_ward_code",
        "date"
    ] + PARAMETERS
]

# ------------------------------------------------------------
# Complete-variable indicator
# ------------------------------------------------------------

aligned["complete_9_variables"] = (
    aligned[PARAMETERS]
    .notna()
    .all(axis=1)
)

aligned["available_variable_count"] = (
    aligned[PARAMETERS]
    .notna()
    .sum(axis=1)
)

# ------------------------------------------------------------
# Save
# ------------------------------------------------------------

OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True
)

aligned.to_csv(
    OUTPUT,
    index=False
)

# ------------------------------------------------------------
# REPORT
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("ALIGNMENT COMPLETE")
print("=" * 70)

print(
    "Station-days:",
    len(aligned)
)

print(
    "Locations:",
    aligned["openaq_location_id"].nunique()
)

print(
    "Wards:",
    aligned["urban_ward_code"].nunique()
)

print(
    "Complete 9-variable station-days:",
    int(
        aligned["complete_9_variables"].sum()
    )
)

print(
    "Complete percentage:",
    round(
        aligned["complete_9_variables"].mean() * 100,
        2
    )
)

print("\nMissingness by variable:")

missing = (
    aligned[PARAMETERS]
    .isna()
    .mean()
    .mul(100)
    .sort_values()
)

print(
    missing.round(2).to_string()
)

print("\nCoverage by location:")

location_coverage = (
    aligned.groupby(
        [
            "openaq_location_id",
            "station_name",
            "urban_ward_code"
        ]
    )
    .agg(
        station_days=(
            "date",
            "count"
        ),
        complete_days=(
            "complete_9_variables",
            "sum"
        )
    )
    .reset_index()
)

location_coverage[
    "complete_pct"
] = (
    location_coverage["complete_days"] /
    location_coverage["station_days"] *
    100
)

print(
    location_coverage[
        [
            "openaq_location_id",
            "urban_ward_code",
            "station_days",
            "complete_days",
            "complete_pct"
        ]
    ]
    .sort_values(
        "complete_pct",
        ascending=False
    )
    .to_string(index=False)
)

print("\nCoverage by ward:")

ward_coverage = (
    aligned.groupby(
        "urban_ward_code"
    )
    .agg(
        station_days=(
            "date",
            "count"
        ),
        complete_days=(
            "complete_9_variables",
            "sum"
        )
    )
    .reset_index()
)

ward_coverage[
    "complete_pct"
] = (
    ward_coverage["complete_days"] /
    ward_coverage["station_days"] *
    100
)

print(
    ward_coverage.to_string(
        index=False
    )
)

print("\nSaved:")
print(OUTPUT)

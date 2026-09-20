import pandas as pd
from pathlib import Path

INPUT = Path(
    "data/processed/mumbai_openaq_sensor_history_audit.csv"
)

OUTPUT = Path(
    "data/processed/mumbai_openaq_multivariate_history_audit_v2.csv"
)

df = pd.read_csv(INPUT)

df["datetime_first_utc"] = pd.to_datetime(
    df["datetime_first_utc"],
    errors="coerce",
    utc=True
)

df["datetime_last_utc"] = pd.to_datetime(
    df["datetime_last_utc"],
    errors="coerce",
    utc=True
)

df["openaq_location_id"] = (
    df["openaq_location_id"].astype(int)
)

parameters = [
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

# ------------------------------------------------------------
# Select current PM2.5 locations
# ------------------------------------------------------------

pm25 = df[
    (df["parameter_name"] == "pm25") &
    (df["datetime_last_utc"] >= pd.Timestamp(
        "2025-01-01",
        tz="UTC"
    ))
].copy()

locations = (
    pm25["openaq_location_id"]
    .astype(int)
    .unique()
)

df = df[
    df["openaq_location_id"].isin(locations) &
    df["parameter_name"].isin(parameters)
].copy()

rows = []

for location_id, group in df.groupby(
    "openaq_location_id"
):

    first_dates = {}
    last_dates = {}

    for parameter in parameters:

        subset = group[
            group["parameter_name"] == parameter
        ]

        if subset.empty:
            continue

        first_dates[parameter] = (
            subset["datetime_first_utc"].min()
        )

        last_dates[parameter] = (
            subset["datetime_last_utc"].max()
        )

    # --------------------------------------------------------
    # Require ALL 9 variables
    # --------------------------------------------------------

    if len(first_dates) != len(parameters):
        continue

    common_first = max(
        first_dates.values()
    )

    common_last = min(
        last_dates.values()
    )

    common_days = (
        common_last - common_first
    ).total_seconds() / 86400

    rows.append({

        "openaq_location_id":
            location_id,

        "station_name":
            group["station_name"].iloc[0],

        "urban_ward_code":
            group["urban_ward_code"].iloc[0],

        "parameter_count":
            len(first_dates),

        "common_first_utc":
            common_first,

        "common_last_utc":
            common_last,

        "common_history_days":
            max(0, common_days)
    })

result = pd.DataFrame(rows)

result = result.sort_values(
    [
        "urban_ward_code",
        "common_history_days"
    ],
    ascending=[True, False]
)

result["usable_multivariate"] = (
    result["common_history_days"] >= 180
)

result.to_csv(
    OUTPUT,
    index=False
)

# ------------------------------------------------------------
# Report
# ------------------------------------------------------------

print("=" * 70)
print("MULTIVARIATE HISTORY AUDIT V2")
print("=" * 70)

print(
    "Locations with all 9 parameters:",
    len(result)
)

print(
    "Locations with >=180 days:",
    result["usable_multivariate"].sum()
)

print("\nAll-parameter locations:")

print(
    result.to_string(index=False)
)

print("\nUsable locations:")

print(
    result[
        result["usable_multivariate"]
    ].to_string(index=False)
)

print("\nUsable wards:")

print(
    result[
        result["usable_multivariate"]
    ]["urban_ward_code"]
    .drop_duplicates()
    .sort_values()
    .to_list()
)

print("\nSaved:")
print(OUTPUT)

import pandas as pd
from pathlib import Path

INPUT = Path(
    "data/processed/mumbai_openaq_sensor_history_audit.csv"
)

OUTPUT = Path(
    "data/processed/mumbai_openaq_multivariate_history_audit.csv"
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

# Current PM2.5 locations
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

df["openaq_location_id"] = (
    df["openaq_location_id"]
    .astype(int)
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

        if len(subset) == 0:
            continue

        first_dates[parameter] = (
            subset["datetime_first_utc"]
            .min()
        )

        last_dates[parameter] = (
            subset["datetime_last_utc"]
            .max()
        )

    # Common overlap across ALL available parameters
    common_first = (
        max(first_dates.values())
        if first_dates
        else pd.NaT
    )

    common_last = (
        min(last_dates.values())
        if last_dates
        else pd.NaT
    )

    row = {

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
            common_last
    }

    for parameter in parameters:

        row[f"{parameter}_first_utc"] = (
            first_dates.get(
                parameter,
                pd.NaT
            )
        )

        row[f"{parameter}_last_utc"] = (
            last_dates.get(
                parameter,
                pd.NaT
            )
        )

    if (
        pd.notna(common_first) and
        pd.notna(common_last)
    ):

        row["common_history_days"] = (
            common_last - common_first
        ).total_seconds() / 86400

    else:

        row["common_history_days"] = 0

    rows.append(row)

result = pd.DataFrame(rows)

result = result.sort_values(
    [
        "urban_ward_code",
        "openaq_location_id"
    ]
)

result.to_csv(
    OUTPUT,
    index=False
)

print("=" * 70)
print("MULTIVARIATE HISTORICAL COVERAGE AUDIT")
print("=" * 70)

print(
    "PM2.5 locations:",
    len(locations)
)

print(
    "Locations audited:",
    len(result)
)

print("\nCommon history:")
print(
    result[
        [
            "openaq_location_id",
            "station_name",
            "urban_ward_code",
            "parameter_count",
            "common_first_utc",
            "common_last_utc",
            "common_history_days"
        ]
    ].to_string(index=False)
)

print("\nCommon history statistics:")

print(
    result["common_history_days"]
    .describe()
    .to_string()
)

print("\nLocations with >= 180 days common history:")

print(
    result[
        result["common_history_days"] >= 180
    ][
        [
            "openaq_location_id",
            "urban_ward_code",
            "common_history_days"
        ]
    ].to_string(index=False)
)

print("\nSaved:")
print(OUTPUT)

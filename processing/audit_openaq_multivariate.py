import pandas as pd
from pathlib import Path

INPUT = Path(
    "data/processed/mumbai_openaq_sensor_inventory.csv"
)

OUTPUT = Path(
    "data/processed/mumbai_openaq_multivariate_sensor_availability.csv"
)

inventory = pd.read_csv(INPUT)

# Current PM2.5 sensors selected for temporal modelling
history = pd.read_csv(
    "data/processed/mumbai_openaq_sensor_history_audit.csv"
)

history["datetime_last_utc"] = pd.to_datetime(
    history["datetime_last_utc"],
    errors="coerce",
    utc=True
)

pm25 = history[
    (history["parameter_name"] == "pm25") &
    (history["datetime_last_utc"] >= pd.Timestamp(
        "2025-01-01",
        tz="UTC"
    ))
].copy()

pm25_sensor_ids = set(
    pm25["sensor_id"].astype(int)
)

# ------------------------------------------------------------
# Get sensors at the same OpenAQ location
# ------------------------------------------------------------

inventory["sensor_id"] = (
    inventory["sensor_id"]
    .astype(int)
)

inventory["openaq_location_id"] = (
    inventory["openaq_location_id"]
    .astype(int)
)

current_inventory = inventory[
    inventory["openaq_location_id"].isin(
        pm25["openaq_location_id"].astype(int)
    )
].copy()

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
# Location × parameter availability
# ------------------------------------------------------------

availability = (
    current_inventory[
        current_inventory["parameter_name"]
        .isin(parameters)
    ]
    .groupby(
        [
            "openaq_location_id",
            "station_name",
            "urban_ward_code"
        ]
    )["parameter_name"]
    .agg(lambda x: sorted(set(x)))
    .reset_index()
)

for parameter in parameters:

    availability[
        f"has_{parameter}"
    ] = availability["parameter_name"].apply(
        lambda x: parameter in x
    )

availability["parameter_count"] = (
    availability[
        [f"has_{p}" for p in parameters]
    ]
    .sum(axis=1)
)

availability = availability.sort_values(
    [
        "urban_ward_code",
        "openaq_location_id"
    ]
)

# ------------------------------------------------------------
# Report
# ------------------------------------------------------------

print("=" * 70)
print("MULTIVARIATE OPENAQ SENSOR AVAILABILITY")
print("=" * 70)

print(
    "PM2.5 locations:",
    availability["openaq_location_id"].nunique()
)

print(
    "Wards:",
    availability["urban_ward_code"].nunique()
)

print("\nParameter availability:")

for parameter in parameters:

    count = availability[
        f"has_{parameter}"
    ].sum()

    print(
        f"{parameter:18s}: "
        f"{count} locations"
    )

print("\nLocation availability:")
print(
    availability[
        [
            "openaq_location_id",
            "station_name",
            "urban_ward_code",
            "parameter_count"
        ] +
        [f"has_{p}" for p in parameters]
    ].to_string(index=False)
)

print("\nLocations with at least 5 parameters:")

print(
    availability[
        availability["parameter_count"] >= 5
    ][
        [
            "openaq_location_id",
            "station_name",
            "urban_ward_code",
            "parameter_count"
        ]
    ].to_string(index=False)
)

OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True
)

availability.to_csv(
    OUTPUT,
    index=False
)

print("\nSaved:")
print(OUTPUT)

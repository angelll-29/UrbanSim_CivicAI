import os
from pathlib import Path

import requests
import pandas as pd
from dotenv import load_dotenv


load_dotenv()

API_KEY = os.getenv("OPENAQ_API_KEY")

if not API_KEY:
    raise RuntimeError(
        "OPENAQ_API_KEY not found in .env"
    )

STATIONS = Path(
    "data/processed/mumbai_air_quality_stations_validated.csv"
)

SENSORS = Path(
    "data/processed/mumbai_openaq_sensor_inventory.csv"
)

OUTPUT = Path(
    "data/processed/mumbai_openaq_latest_measurements.csv"
)

stations = pd.read_csv(STATIONS)
sensors = pd.read_csv(SENSORS)

headers = {
    "X-API-Key": API_KEY
}

# Sensor lookup.
sensor_lookup = sensors[
    [
        "sensor_id",
        "openaq_location_id",
        "parameter_name",
        "parameter_display",
        "parameter_units"
    ]
].drop_duplicates(
    subset=["sensor_id"]
)

rows = []

for _, station in stations.iterrows():

    location_id = int(
        station["openaq_location_id"]
    )

    url = (
        f"https://api.openaq.org/v3/"
        f"locations/{location_id}/latest"
    )

    response = requests.get(
        url,
        headers=headers,
        timeout=30
    )

    print(
        f"{location_id} | "
        f"{station['station_name']} | "
        f"HTTP {response.status_code}"
    )

    if response.status_code != 200:
        continue

    data = response.json()

    for measurement in data.get(
        "results", []
    ):

        sensor_id = measurement.get(
            "sensorsId"
        )

        sensor_match = sensor_lookup[
            sensor_lookup["sensor_id"]
            == sensor_id
        ]

        if sensor_match.empty:
            continue

        sensor = sensor_match.iloc[0]

        datetime_data = (
            measurement.get("datetime")
            or {}
        )

        rows.append({

            "openaq_location_id":
                location_id,

            "station_name":
                station["station_name"],

            "urban_ward_code":
                station["urban_ward_code"],

            "provider":
                station["provider"],

            "sensor_id":
                sensor_id,

            "parameter_name":
                sensor["parameter_name"],

            "parameter_display":
                sensor["parameter_display"],

            "unit":
                sensor["parameter_units"],

            "value":
                measurement.get("value"),

            "datetime_utc":
                datetime_data.get("utc"),

            "datetime_local":
                datetime_data.get("local"),

            "latitude":
                measurement.get(
                    "coordinates",
                    {}
                ).get("latitude"),

            "longitude":
                measurement.get(
                    "coordinates",
                    {}
                ).get("longitude"),

            "source":
                "OpenAQ"
        })


result = pd.DataFrame(rows)

if not result.empty:

    result = result.drop_duplicates(
        subset=[
            "openaq_location_id",
            "sensor_id",
            "datetime_utc"
        ]
    )

    result = result.sort_values(
        [
            "urban_ward_code",
            "station_name",
            "parameter_name"
        ]
    ).reset_index(drop=True)


OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True
)

result.to_csv(
    OUTPUT,
    index=False
)

print("\nOpenAQ Environmental Measurements")
print("---------------------------------")

print(
    "Stations:",
    stations["openaq_location_id"].nunique()
)

print(
    "Measurements:",
    len(result)
)

print("\nParameter distribution:")

if not result.empty:

    print(
        result[
            [
                "parameter_name",
                "unit"
            ]
        ]
        .value_counts()
        .to_string()
    )

    print("\nMeasurement timestamps:")

    print(
        result[
            "datetime_utc"
        ].min(),
        "→",
        result[
            "datetime_utc"
        ].max()
    )

print(
    f"\nOutput: {OUTPUT}"
)

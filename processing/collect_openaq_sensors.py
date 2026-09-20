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

INPUT = Path(
    "data/processed/mumbai_air_quality_stations_validated.csv"
)

OUTPUT = Path(
    "data/processed/mumbai_openaq_sensor_inventory.csv"
)

stations = pd.read_csv(INPUT)

headers = {
    "X-API-Key": API_KEY
}

rows = []

for _, station in stations.iterrows():

    location_id = int(
        station["openaq_location_id"]
    )

    url = (
        f"https://api.openaq.org/v3/"
        f"locations/{location_id}/sensors"
    )

    response = requests.get(
        url,
        headers=headers,
        params={
            "limit": 100
        },
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

    for sensor in data.get(
        "results", []
    ):

        sensor_id = sensor.get("id")

        # OpenAQ sensor metadata can expose
        # parameter information in the parameter object.
        parameter = (
            sensor.get("parameter")
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
                parameter.get("name"),

            "parameter_display":
                parameter.get("displayName"),

            "parameter_units":
                parameter.get("units"),

            "sensor_name":
                sensor.get("name"),

            "sensor_units":
                sensor.get("units"),

            "source":
                "OpenAQ"
        })


inventory = pd.DataFrame(rows)

if not inventory.empty:

    inventory = (
        inventory
        .drop_duplicates(
            subset=[
                "openaq_location_id",
                "sensor_id"
            ]
        )
        .sort_values(
            [
                "station_name",
                "parameter_name"
            ]
        )
        .reset_index(drop=True)
    )

OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True
)

inventory.to_csv(
    OUTPUT,
    index=False
)

print("\nOpenAQ Sensor Inventory")
print("-----------------------")

print(
    "Stations queried:",
    stations["openaq_location_id"].nunique()
)

print(
    "Sensors found:",
    len(inventory)
)

print("\nParameters:")

if not inventory.empty:
    print(
        inventory[
            [
                "parameter_name",
                "parameter_display",
                "parameter_units"
            ]
        ]
        .drop_duplicates()
        .to_string(index=False)
    )

    print("\nSensors by parameter:")

    print(
        inventory["parameter_name"]
        .value_counts(dropna=False)
        .to_string()
    )

print(
    f"\nOutput: {OUTPUT}"
)

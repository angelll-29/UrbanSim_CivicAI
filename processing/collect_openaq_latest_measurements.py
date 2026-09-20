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
    "data/processed/mumbai_openaq_available_measurements.csv"
)

df = pd.read_csv(INPUT)

headers = {
    "X-API-Key": API_KEY
}

rows = []

for _, station in df.iterrows():

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

    if response.status_code != 200:
        print(
            f"Failed {location_id}: "
            f"{response.status_code}"
        )
        continue

    data = response.json()

    for measurement in data.get(
        "results", []
    ):

        parameter = (
            measurement.get("parameter")
            or {}
        )

        unit = (
            measurement.get("unit")
        )

        period = (
            measurement.get("period")
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

            "parameter":
                parameter.get("name"),

            "parameter_display":
                parameter.get("displayName"),

            "unit":
                unit,

            "value":
                measurement.get("value"),

            "datetime_from":
                (
                    period.get("datetimeFrom")
                    or {}
                ).get("utc"),

            "datetime_to":
                (
                    period.get("datetimeTo")
                    or {}
                ).get("utc"),

            "source":
                "OpenAQ"
        })


measurements = pd.DataFrame(rows)

OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True
)

measurements.to_csv(
    OUTPUT,
    index=False
)

print("\nOpenAQ Measurement Inventory")
print("----------------------------")

print(
    "Stations queried:",
    df["openaq_location_id"].nunique()
)

print(
    "Measurements:",
    len(measurements)
)

if not measurements.empty:

    print("\nParameters:")

    print(
        measurements[
            [
                "parameter",
                "parameter_display",
                "unit"
            ]
        ]
        .drop_duplicates()
        .sort_values("parameter")
        .to_string(index=False)
    )

    print("\nMeasurements by parameter:")

    print(
        measurements["parameter"]
        .value_counts()
        .to_string()
    )

print(
    f"\nOutput: {OUTPUT}"
)

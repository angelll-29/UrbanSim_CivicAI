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

URL = "https://api.openaq.org/v3/locations"

# Mumbai metropolitan search envelope.
# We will later spatially join returned stations
# against the actual 24 BMC ward polygons.
BBOX = "72.75,18.85,73.10,19.35"

params = {
    "bbox": BBOX,
    "limit": 1000,
    "page": 1
}

headers = {
    "X-API-Key": API_KEY
}

response = requests.get(
    URL,
    params=params,
    headers=headers,
    timeout=30
)

print("HTTP status:", response.status_code)

response.raise_for_status()

data = response.json()

results = data.get("results", [])

print("OpenAQ locations returned:", len(results))

rows = []

for location in results:

    coordinates = location.get("coordinates") or {}

    rows.append({
        "openaq_location_id":
            location.get("id"),

        "station_name":
            location.get("name"),

        "locality":
            location.get("locality"),

        "country":
            (
                location.get("country") or {}
            ).get("name"),

        "latitude":
            coordinates.get("latitude"),

        "longitude":
            coordinates.get("longitude"),

        "timezone":
            location.get("timezone"),

        "is_mobile":
            location.get("isMobile"),

        "is_monitor":
            location.get("isMonitor"),

        "owner":
            (
                location.get("owner") or {}
            ).get("name"),

        "provider":
            (
                location.get("provider") or {}
            ).get("name"),

        "source":
            "OpenAQ"
    })


df = pd.DataFrame(rows)

if not df.empty:

    df = (
        df
        .drop_duplicates(
            subset=["openaq_location_id"]
        )
        .sort_values(
            ["station_name", "openaq_location_id"]
        )
        .reset_index(drop=True)
    )

OUTPUT = Path(
    "data/processed/mumbai_air_quality_stations.csv"
)

OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True
)

df.to_csv(
    OUTPUT,
    index=False
)

print("\nMumbai Air Quality Stations")
print("---------------------------")
print("Records:", len(df))

if not df.empty:
    print(
        df[
            [
                "openaq_location_id",
                "station_name",
                "latitude",
                "longitude",
                "provider"
            ]
        ].to_string(index=False)
    )

print("\nOutput:")
print(OUTPUT)

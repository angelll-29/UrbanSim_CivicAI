import os
import json
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

df = pd.read_csv(INPUT)

location_id = int(
    df.iloc[0]["openaq_location_id"]
)

url = (
    f"https://api.openaq.org/v3/"
    f"locations/{location_id}/latest"
)

headers = {
    "X-API-Key": API_KEY
}

response = requests.get(
    url,
    headers=headers,
    timeout=30
)

print("Station:")
print(
    df.iloc[0][
        [
            "openaq_location_id",
            "station_name",
            "urban_ward_code"
        ]
    ].to_dict()
)

print("\nHTTP status:", response.status_code)

response.raise_for_status()

data = response.json()

print("\nTop-level keys:")
print(data.keys())

print("\nRaw response:")
print(
    json.dumps(
        data,
        indent=2,
        ensure_ascii=False
    )
)

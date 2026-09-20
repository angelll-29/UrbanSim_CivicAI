import time
from pathlib import Path

import pandas as pd
import requests


# ============================================================
# CONFIG
# ============================================================

INPUT_FILE = Path(
    "data/external/mumbai_metro_monorail_station_list_224.csv"
)

OUTPUT_FILE = Path(
    "data/processed/mumbai_metro_monorail_stations.csv"
)

GEOCODE_CACHE = Path(
    "data/processed/metro_monorail_geocode_cache.csv"
)

USER_AGENT = "UrbanSim-CivicAI/1.0 (Mumbai urban GIS project)"

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 70)
print("URBANSIM - METRO + MONORAIL COORDINATE ENRICHMENT")
print("=" * 70)

df = pd.read_csv(INPUT_FILE)

print(f"\nInput records: {len(df)}")


# ============================================================
# CREATE COORDINATE COLUMNS
# ============================================================

if "latitude" not in df.columns:
    df["latitude"] = pd.NA

if "longitude" not in df.columns:
    df["longitude"] = pd.NA

if "geocode_status" not in df.columns:
    df["geocode_status"] = pd.NA

if "geocode_display_name" not in df.columns:
    df["geocode_display_name"] = pd.NA


# ============================================================
# LOAD CACHE
# ============================================================

if GEOCODE_CACHE.exists():

    cache = pd.read_csv(GEOCODE_CACHE)

    print(f"Existing cache records: {len(cache)}")

    cache_lookup = cache.set_index("station_id").to_dict("index")

    for idx, row in df.iterrows():

        station_id = row["station_id"]

        if station_id in cache_lookup:

            cached = cache_lookup[station_id]

            df.at[idx, "latitude"] = cached.get("latitude")
            df.at[idx, "longitude"] = cached.get("longitude")
            df.at[idx, "geocode_status"] = cached.get(
                "geocode_status"
            )
            df.at[idx, "geocode_display_name"] = cached.get(
                "geocode_display_name"
            )


else:

    cache = pd.DataFrame(
        columns=[
            "station_id",
            "latitude",
            "longitude",
            "geocode_status",
            "geocode_display_name",
        ]
    )

    print("No existing geocoding cache found.")


# ============================================================
# NOMINATIM SESSION
# ============================================================

session = requests.Session()

session.headers.update(
    {
        "User-Agent": USER_AGENT,
        "Accept-Language": "en",
    }
)


# ============================================================
# GEOCODING FUNCTION
# ============================================================

def geocode_station(station_name, transport_mode):

    # Add Mumbai context because many station names
    # exist elsewhere in India.

    query = f"{station_name}, Mumbai, Maharashtra, India"

    try:

        response = session.get(
            NOMINATIM_URL,
            params={
                "q": query,
                "format": "json",
                "limit": 1,
                "countrycodes": "in",
            },
            timeout=20,
        )

        response.raise_for_status()

        results = response.json()

        if not results:

            return None, None, "NOT_FOUND", None

        result = results[0]

        latitude = float(result["lat"])
        longitude = float(result["lon"])

        display_name = result.get("display_name", "")

        return (
            latitude,
            longitude,
            "MATCHED",
            display_name,
        )

    except Exception as e:

        print(f"   ERROR: {e}")

        return None, None, "ERROR", None


# ============================================================
# PROCESS STATIONS
# ============================================================

for idx, row in df.iterrows():

    station_id = row["station_id"]
    station_name = str(row["station_name"])
    transport_mode = str(row["transport_mode"])

    # Skip already successfully geocoded records.

    if (
        pd.notna(row["latitude"])
        and pd.notna(row["longitude"])
        and row["geocode_status"] == "MATCHED"
    ):
        continue

    print(
        f"\n[{idx + 1}/{len(df)}] "
        f"{transport_mode}: {station_name}"
    )

    lat, lon, status, display_name = geocode_station(
        station_name,
        transport_mode,
    )

    df.at[idx, "latitude"] = lat
    df.at[idx, "longitude"] = lon
    df.at[idx, "geocode_status"] = status
    df.at[idx, "geocode_display_name"] = display_name

    print(f"   Status: {status}")

    if lat is not None:

        print(
            f"   Coordinates: "
            f"{lat:.6f}, {lon:.6f}"
        )

    # --------------------------------------------------------
    # Save cache after every station
    # --------------------------------------------------------

    cache_row = pd.DataFrame(
        [
            {
                "station_id": station_id,
                "latitude": lat,
                "longitude": lon,
                "geocode_status": status,
                "geocode_display_name": display_name,
            }
        ]
    )

    cache = cache[
        cache["station_id"] != station_id
    ]

    cache = pd.concat(
        [cache, cache_row],
        ignore_index=True,
    )

    cache.to_csv(
        GEOCODE_CACHE,
        index=False,
    )

    # Nominatim usage policy:
    # approximately one request per second.

    time.sleep(1.1)


# ============================================================
# SAVE FINAL DATASET
# ============================================================

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True,
)

df.to_csv(
    OUTPUT_FILE,
    index=False,
)


# ============================================================
# REPORT
# ============================================================

matched = (
    df["geocode_status"] == "MATCHED"
).sum()

not_found = (
    df["geocode_status"] == "NOT_FOUND"
).sum()

errors = (
    df["geocode_status"] == "ERROR"
).sum()

missing_coordinates = (
    df["latitude"].isna()
    | df["longitude"].isna()
).sum()


print("\n")
print("=" * 70)
print("GEOCODING COMPLETE")
print("=" * 70)

print(f"Total stations       : {len(df)}")
print(f"Matched              : {matched}")
print(f"Not found            : {not_found}")
print(f"Errors               : {errors}")
print(f"Missing coordinates  : {missing_coordinates}")

print("\nTransport mode:")
print(df["transport_mode"].value_counts())

print("\nOutput:")
print(OUTPUT_FILE)

print("\nCache:")
print(GEOCODE_CACHE)

print("=" * 70)
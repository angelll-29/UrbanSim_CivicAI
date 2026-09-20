import os
import time
import requests
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(".env").resolve())

API_KEY = os.getenv("OPENAQ_API_KEY")

if not API_KEY:
    raise RuntimeError("OPENAQ_API_KEY not found in .env")

AUDIT = Path(
    "data/processed/mumbai_openaq_multivariate_history_audit_v2.csv"
)

OUTPUT = Path(
    "data/processed/mumbai_openaq_multivariate_daily.csv"
)

headers = {
    "X-API-Key": API_KEY
}

audit = pd.read_csv(AUDIT)

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

usable = audit[
    audit["usable_multivariate"] == True
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

rows = []

print("=" * 70)
print("OPENAQ MULTIVARIATE DAILY COLLECTION")
print("=" * 70)

print(
    "Usable locations:",
    len(usable)
)

print(
    "Parameters:",
    len(parameters)
)

for idx, station in usable.iterrows():

    location_id = int(
        station["openaq_location_id"]
    )

    ward = station["urban_ward_code"]

    station_name = station["station_name"]

    start = station["common_first_utc"]
    end = station["common_last_utc"]

    print(
        f"\n[{len(rows):,}] "
        f"Location {location_id} | "
        f"Ward {ward} | "
        f"{station_name}"
    )

    for parameter in parameters:

        # Find the sensor for this location/parameter
        # from the inventory.
        inventory = pd.read_csv(
            "data/processed/mumbai_openaq_sensor_inventory.csv"
        )

        match = inventory[
            (
                inventory[
                    "openaq_location_id"
                ].astype(int)
                == location_id
            ) &
            (
                inventory[
                    "parameter_name"
                ] == parameter
            )
        ]

        if match.empty:
            print(
                f"  Missing sensor: {parameter}"
            )
            continue

        sensor_ids = (
            match["sensor_id"]
            .astype(int)
            .tolist()
        )

        # A location may have multiple sensors
        # for the same parameter.
        for sensor_id in sensor_ids:

            page = 1

            while True:

                url = (
                    f"https://api.openaq.org/v3/"
                    f"sensors/{sensor_id}/days"
                )

                params = {
                    "datetime_from":
                        start.strftime(
                            "%Y-%m-%dT%H:%M:%SZ"
                        ),

                    "datetime_to":
                        end.strftime(
                            "%Y-%m-%dT%H:%M:%SZ"
                        ),

                    "limit": 100,

                    "page": page
                }

                success = False

                for attempt in range(3):

                    try:

                        response = requests.get(
                            url,
                            headers=headers,
                            params=params,
                            timeout=60
                        )

                        if response.status_code == 200:
                            success = True
                            break

                        print(
                            f"  HTTP {response.status_code} "
                            f"{parameter} "
                            f"sensor {sensor_id}"
                        )

                        time.sleep(2)

                    except Exception as e:

                        print(
                            f"  Error: {e}"
                        )

                        time.sleep(2)

                if not success:
                    break

                data = response.json()

                results = data.get(
                    "results",
                    []
                )

                if not results:
                    break

                for item in results:

                    period = (
                        item.get("period") or {}
                    )

                    dt_from = (
                        period.get(
                            "datetimeFrom"
                        ) or {}
                    )

                    coverage = (
                        item.get("coverage") or {}
                    )

                    summary = (
                        item.get("summary") or {}
                    )

                    flag_info = (
                        item.get("flagInfo") or {}
                    )

                    rows.append({

                        "openaq_location_id":
                            location_id,

                        "station_name":
                            station_name,

                        "urban_ward_code":
                            ward,

                        "sensor_id":
                            sensor_id,

                        "parameter":
                            parameter,

                        "date_start_utc":
                            dt_from.get("utc"),

                        "value":
                            item.get("value"),

                        "summary_avg":
                            summary.get("avg"),

                        "summary_min":
                            summary.get("min"),

                        "summary_max":
                            summary.get("max"),

                        "summary_sd":
                            summary.get("sd"),

                        "expected_count":
                            coverage.get(
                                "expectedCount"
                            ),

                        "observed_count":
                            coverage.get(
                                "observedCount"
                            ),

                        "coverage_pct":
                            coverage.get(
                                "percentComplete"
                            ),

                        "source_flagged":
                            flag_info.get(
                                "hasFlags"
                            )
                    })

                if len(results) < 100:
                    break

                page += 1

                time.sleep(0.10)

    print(
        f"  Records collected so far: "
        f"{len(rows):,}"
    )

result = pd.DataFrame(rows)

if result.empty:
    raise RuntimeError(
        "No records collected."
    )

result["date_start_utc"] = pd.to_datetime(
    result["date_start_utc"],
    errors="coerce",
    utc=True
)

result["value"] = pd.to_numeric(
    result["value"],
    errors="coerce"
)

result["date"] = (
    result["date_start_utc"]
    .dt.tz_convert("Asia/Kolkata")
    .dt.date
)

# Remove exact duplicates
before = len(result)

result = result.drop_duplicates(
    subset=[
        "openaq_location_id",
        "sensor_id",
        "parameter",
        "date_start_utc"
    ]
)

duplicates_removed = (
    before - len(result)
)

result = result.sort_values(
    [
        "urban_ward_code",
        "openaq_location_id",
        "parameter",
        "date_start_utc"
    ]
)

OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True
)

result.to_csv(
    OUTPUT,
    index=False
)

print("\n" + "=" * 70)
print("COLLECTION COMPLETE")
print("=" * 70)

print(
    "Total records:",
    len(result)
)

print(
    "Locations:",
    result[
        "openaq_location_id"
    ].nunique()
)

print(
    "Sensors:",
    result["sensor_id"].nunique()
)

print(
    "Wards:",
    result["urban_ward_code"].nunique()
)

print(
    "Duplicates removed:",
    duplicates_removed
)

print("\nParameter records:")

print(
    result["parameter"]
    .value_counts()
    .to_string()
)

print("\nRecords by ward:")

print(
    result["urban_ward_code"]
    .value_counts()
    .sort_index()
    .to_string()
)

print("\nDate range:")

print(result["date"].min())
print("→")
print(result["date"].max())

print("\nSaved:")
print(OUTPUT)

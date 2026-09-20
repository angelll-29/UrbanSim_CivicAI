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

INPUT = Path(
    "data/processed/mumbai_openaq_sensor_inventory.csv"
)

OUTPUT = Path(
    "data/processed/mumbai_openaq_sensor_history_audit.csv"
)

sensors = pd.read_csv(INPUT)

headers = {
    "X-API-Key": API_KEY
}

rows = []

print("=" * 70)
print("OPENAQ SENSOR HISTORY AUDIT")
print("=" * 70)

print("Sensors to audit:", len(sensors))

for i, row in sensors.iterrows():

    sensor_id = int(row["sensor_id"])

    url = (
        f"https://api.openaq.org/v3/"
        f"sensors/{sensor_id}"
    )

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=30
        )

        print(
            f"[{i+1}/{len(sensors)}] "
            f"{sensor_id} | "
            f"{row['parameter_name']} | "
            f"{row['urban_ward_code']} | "
            f"HTTP {response.status_code}"
        )

        if response.status_code != 200:
            rows.append({
                "sensor_id": sensor_id,
                "openaq_location_id": row["openaq_location_id"],
                "station_name": row["station_name"],
                "urban_ward_code": row["urban_ward_code"],
                "provider": row["provider"],
                "parameter_name": row["parameter_name"],
                "parameter_units": row["parameter_units"],
                "status_code": response.status_code
            })
            continue

        data = response.json()

        result = data.get("results", [])

        if not result:
            rows.append({
                "sensor_id": sensor_id,
                "openaq_location_id": row["openaq_location_id"],
                "station_name": row["station_name"],
                "urban_ward_code": row["urban_ward_code"],
                "provider": row["provider"],
                "parameter_name": row["parameter_name"],
                "parameter_units": row["parameter_units"],
                "status_code": response.status_code
            })
            continue

        sensor = result[0]

        first = sensor.get("datetimeFirst") or {}
        last = sensor.get("datetimeLast") or {}
        coverage = sensor.get("coverage") or {}

        rows.append({

            "sensor_id": sensor_id,

            "openaq_location_id":
                row["openaq_location_id"],

            "station_name":
                row["station_name"],

            "urban_ward_code":
                row["urban_ward_code"],

            "provider":
                row["provider"],

            "parameter_name":
                row["parameter_name"],

            "parameter_units":
                row["parameter_units"],

            "datetime_first_utc":
                first.get("utc"),

            "datetime_last_utc":
                last.get("utc"),

            "observed_count":
                coverage.get("observedCount"),

            "expected_interval":
                coverage.get("expectedInterval"),

            "coverage_from_utc":
                (
                    coverage.get("datetimeFrom") or {}
                ).get("utc"),

            "coverage_to_utc":
                (
                    coverage.get("datetimeTo") or {}
                ).get("utc"),

            "status_code":
                response.status_code
        })

        # Small pause to avoid aggressive request rate
        time.sleep(0.10)

    except Exception as e:

        print(
            f"ERROR sensor {sensor_id}: {e}"
        )

        rows.append({

            "sensor_id": sensor_id,

            "openaq_location_id":
                row["openaq_location_id"],

            "station_name":
                row["station_name"],

            "urban_ward_code":
                row["urban_ward_code"],

            "provider":
                row["provider"],

            "parameter_name":
                row["parameter_name"],

            "parameter_units":
                row["parameter_units"],

            "error":
                str(e)
        })

result = pd.DataFrame(rows)

# Convert timestamps
for col in [
    "datetime_first_utc",
    "datetime_last_utc",
    "coverage_from_utc",
    "coverage_to_utc"
]:

    if col in result.columns:

        result[col] = pd.to_datetime(
            result[col],
            errors="coerce",
            utc=True
        )

# Calculate duration
result["history_days"] = (
    result["datetime_last_utc"]
    - result["datetime_first_utc"]
).dt.total_seconds() / 86400

# Useful date flags
result["has_2024"] = (
    result["datetime_last_utc"]
    >= pd.Timestamp(
        "2024-01-01",
        tz="UTC"
    )
)

result["has_2025"] = (
    result["datetime_last_utc"]
    >= pd.Timestamp(
        "2025-01-01",
        tz="UTC"
    )
)

result["has_2026"] = (
    result["datetime_last_utc"]
    >= pd.Timestamp(
        "2026-01-01",
        tz="UTC"
    )
)

result = result.sort_values(
    [
        "parameter_name",
        "urban_ward_code",
        "sensor_id"
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
print("AUDIT COMPLETE")
print("=" * 70)

print("Records:", len(result))

print("\nParameter distribution:")
print(
    result["parameter_name"]
    .value_counts()
    .to_string()
)

print("\nSensors with data ending in 2024 or later:")
print(
    result["has_2024"]
    .value_counts()
    .to_string()
)

print("\nSensors with data ending in 2025 or later:")
print(
    result["has_2025"]
    .value_counts()
    .to_string()
)

print("\nSensors with data ending in 2026:")
print(
    result["has_2026"]
    .value_counts()
    .to_string()
)

print("\nPM2.5 history:")
pm25 = result[
    result["parameter_name"] == "pm25"
]

print(
    pm25[
        [
            "sensor_id",
            "urban_ward_code",
            "datetime_first_utc",
            "datetime_last_utc",
            "observed_count",
            "history_days"
        ]
    ].to_string(index=False)
)

print("\nSaved:")
print(OUTPUT)

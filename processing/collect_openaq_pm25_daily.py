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
    "data/processed/mumbai_openaq_sensor_history_audit.csv"
)

OUTPUT = Path(
    "data/processed/mumbai_openaq_pm25_daily_sensor_history.csv"
)

START_DATE = "2025-02-18T00:00:00Z"
END_DATE = "2026-09-18T00:00:00Z"

LIMIT = 100

headers = {
    "X-API-Key": API_KEY
}

audit = pd.read_csv(INPUT)

audit["datetime_last_utc"] = pd.to_datetime(
    audit["datetime_last_utc"],
    errors="coerce",
    utc=True
)

pm25 = audit[
    (audit["parameter_name"] == "pm25") &
    (audit["datetime_last_utc"] >= pd.Timestamp(
        "2025-01-01",
        tz="UTC"
    ))
].copy()

print("=" * 70)
print("OPENAQ PM2.5 DAILY HISTORY COLLECTION")
print("=" * 70)

print("PM2.5 sensors selected:", len(pm25))
print("Period:", START_DATE, "→", END_DATE)

rows = []

for idx, sensor in pm25.iterrows():

    sensor_id = int(sensor["sensor_id"])
    ward = sensor["urban_ward_code"]
    station = sensor["station_name"]

    print(
        f"\n[{len(rows)}] "
        f"Sensor {sensor_id} | "
        f"Ward {ward} | "
        f"{station}"
    )

    page = 1

    while True:

        url = (
            f"https://api.openaq.org/v3/"
            f"sensors/{sensor_id}/days"
        )

        params = {
            "datetime_from": START_DATE,
            "datetime_to": END_DATE,
            "limit": LIMIT,
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
                    f"attempt {attempt + 1}/3"
                )

                time.sleep(2)

            except Exception as e:

                print(
                    f"  Request error: {e}"
                )

                time.sleep(2)

        if not success:
            print(
                f"  FAILED sensor {sensor_id}, "
                f"page {page}"
            )
            break

        data = response.json()

        results = data.get("results", [])

        if not results:
            break

        for item in results:

            period = item.get("period") or {}
            dt_from = period.get("datetimeFrom") or {}
            dt_to = period.get("datetimeTo") or {}

            coverage = item.get("coverage") or {}
            summary = item.get("summary") or {}

            rows.append({

                "sensor_id":
                    sensor_id,

                "openaq_location_id":
                    sensor["openaq_location_id"],

                "station_name":
                    station,

                "urban_ward_code":
                    ward,

                "parameter":
                    "pm25",

                "units":
                    "µg/m³",

                "date_start_utc":
                    dt_from.get("utc"),

                "date_end_utc":
                    dt_to.get("utc"),

                "daily_value":
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
                    coverage.get("expectedCount"),

                "observed_count":
                    coverage.get("observedCount"),

                "coverage_pct":
                    coverage.get("percentComplete"),

                "flagged":
                    (item.get("flagInfo") or {})
                    .get("hasFlags")
            })

        found = data.get("meta", {}).get("found")

        if len(results) < LIMIT:
            break

        if isinstance(found, int):
            if page * LIMIT >= found:
                break

        page += 1

        time.sleep(0.15)

    print(
        f"  Collected so far: {len(rows):,}"
    )

# ------------------------------------------------------------------
# Build dataframe
# ------------------------------------------------------------------

result = pd.DataFrame(rows)

if result.empty:
    raise RuntimeError(
        "No PM2.5 daily records were collected."
    )

result["date_start_utc"] = pd.to_datetime(
    result["date_start_utc"],
    errors="coerce",
    utc=True
)

result["date_end_utc"] = pd.to_datetime(
    result["date_end_utc"],
    errors="coerce",
    utc=True
)

result["date"] = (
    result["date_start_utc"]
    .dt.tz_convert("Asia/Kolkata")
    .dt.date
)

# Remove exact duplicate observations
before = len(result)

result = result.drop_duplicates(
    subset=[
        "sensor_id",
        "date_start_utc",
        "date_end_utc"
    ]
)

duplicates_removed = before - len(result)

# Sort
result = result.sort_values(
    [
        "urban_ward_code",
        "sensor_id",
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

# ------------------------------------------------------------------
# QC summary
# ------------------------------------------------------------------

print("\n" + "=" * 70)
print("COLLECTION COMPLETE")
print("=" * 70)

print("Daily records:", len(result))
print("Sensors:", result["sensor_id"].nunique())
print("Wards:", result["urban_ward_code"].nunique())
print("Duplicates removed:", duplicates_removed)

print(
    "Date range:",
    result["date_start_utc"].min(),
    "→",
    result["date_start_utc"].max()
)

print("\nRecords by ward:")
print(
    result["urban_ward_code"]
    .value_counts()
    .sort_index()
    .to_string()
)

print("\nCoverage statistics:")
print(
    result["coverage_pct"]
    .describe()
    .to_string()
)

print("\nDaily PM2.5 statistics:")
print(
    result["daily_value"]
    .describe()
    .to_string()
)

print("\nFlagged records:")
print(
    result["flagged"]
    .value_counts(dropna=False)
    .to_string()
)

print("\nSaved:")
print(OUTPUT)

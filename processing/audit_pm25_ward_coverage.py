import pandas as pd
from pathlib import Path

INPUT = Path(
    "data/processed/mumbai_openaq_pm25_daily_qc.csv"
)

OUTPUT = Path(
    "data/processed/mumbai_pm25_ward_daily_coverage.csv"
)

df = pd.read_csv(INPUT)

df["date"] = pd.to_datetime(
    df["date"],
    errors="coerce"
)

df = df[
    df["usable_for_lstm"] == True
].copy()

# Unique ward-day observations
ward_day = (
    df.groupby(
        ["urban_ward_code", "date"]
    )
    .agg(
        sensor_count=("sensor_id", "nunique"),
        observation_count=("daily_value", "count"),
        mean_pm25=("daily_value", "mean")
    )
    .reset_index()
)

# Expected calendar period
start = pd.Timestamp("2025-02-18")
end = pd.Timestamp("2026-09-17")

expected_dates = pd.date_range(
    start,
    end,
    freq="D"
)

expected_days = len(expected_dates)

rows = []

for ward in sorted(
    df["urban_ward_code"].unique()
):

    ward_data = ward_day[
        ward_day["urban_ward_code"] == ward
    ]

    dates = set(
        ward_data["date"].dt.normalize()
    )

    expected = set(
        expected_dates
    )

    missing = expected - dates

    covered_days = len(dates)

    coverage_pct = (
        covered_days /
        expected_days *
        100
    )

    # Longest consecutive run
    available_dates = sorted(dates)

    longest_run = 0
    current_run = 0
    previous = None

    for date in available_dates:

        if (
            previous is not None and
            date == previous + pd.Timedelta(days=1)
        ):
            current_run += 1
        else:
            current_run = 1

        longest_run = max(
            longest_run,
            current_run
        )

        previous = date

    rows.append({

        "urban_ward_code": ward,

        "expected_days":
            expected_days,

        "covered_days":
            covered_days,

        "missing_days":
            len(missing),

        "coverage_pct":
            coverage_pct,

        "longest_consecutive_days":
            longest_run,

        "total_sensor_observations":
            len(
                df[
                    df["urban_ward_code"] == ward
                ]
            ),

        "average_sensors_per_day":
            ward_data["sensor_count"].mean(),

        "max_sensors_per_day":
            ward_data["sensor_count"].max()
    })

coverage = pd.DataFrame(rows)

coverage = coverage.sort_values(
    "coverage_pct",
    ascending=False
)

OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True
)

coverage.to_csv(
    OUTPUT,
    index=False
)

print("=" * 70)
print("PM2.5 WARD TEMPORAL COVERAGE AUDIT")
print("=" * 70)

print(
    "Expected calendar days:",
    expected_days
)

print(
    "Monitored wards:",
    len(coverage)
)

print("\nWard coverage:")
print(
    coverage.to_string(index=False)
)

print("\nOverall:")
print(
    "Total usable observations:",
    len(df)
)

print(
    "Unique ward-days:",
    len(ward_day)
)

print(
    "Mean ward coverage:",
    round(
        coverage["coverage_pct"].mean(),
        2
    ),
    "%"
)

print(
    "Minimum ward coverage:",
    round(
        coverage["coverage_pct"].min(),
        2
    ),
    "%"
)

print(
    "Maximum ward coverage:",
    round(
        coverage["coverage_pct"].max(),
        2
    ),
    "%"
)

print("\nSaved:")
print(OUTPUT)

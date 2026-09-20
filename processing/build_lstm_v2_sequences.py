import numpy as np
import pandas as pd
from pathlib import Path

INPUT = Path(
    "data/processed/mumbai_lstm_v2_daily_features.csv"
)

OUTPUT = Path(
    "data/processed/mumbai_lstm_v2_sequences.npz"
)

META = Path(
    "data/processed/mumbai_lstm_v2_sequence_metadata.csv"
)

FEATURES = [
    "pm25",
    "temperature",
    "relativehumidity",
    "wind_speed",
    "no2",
    "o3",
    "so2",
    "co",
    "wind_direction_sin",
    "wind_direction_cos",
    "day_of_year_sin",
    "day_of_year_cos"
]

INPUT_DAYS = 60
FORECAST_DAYS = 7

MIN_INPUT_COVERAGE = 0.80

df = pd.read_csv(INPUT)

df["date"] = pd.to_datetime(
    df["date"],
    errors="coerce"
)

df = df.sort_values(
    [
        "openaq_location_id",
        "date"
    ]
)

X = []
Y = []
metadata = []

for location_id, group in df.groupby(
    "openaq_location_id"
):

    group = group.sort_values(
        "date"
    ).copy()

    station_name = (
        group["station_name"].iloc[0]
    )

    ward = (
        group["urban_ward_code"].iloc[0]
    )

    group = group.set_index("date")

    full_dates = pd.date_range(
        group.index.min(),
        group.index.max(),
        freq="D"
    )

    group = group.reindex(
        full_dates
    )

    group["openaq_location_id"] = location_id
    group["station_name"] = station_name
    group["urban_ward_code"] = ward

    values = group[
        FEATURES
    ].astype(float).values

    dates = group.index

    total_days = len(group)

    for start in range(
        total_days -
        INPUT_DAYS -
        FORECAST_DAYS +
        1
    ):

        input_end = (
            start + INPUT_DAYS
        )

        target_end = (
            input_end +
            FORECAST_DAYS
        )

        input_values = values[
            start:input_end
        ]

        target_values = values[
            input_end:target_end,
            0
        ]

        input_dates = dates[
            start:input_end
        ]

        target_dates = dates[
            input_end:target_end
        ]

        # Coverage before interpolation
        feature_coverage = np.mean(
            ~np.isnan(input_values),
            axis=0
        )

        overall_coverage = np.mean(
            feature_coverage
        )

        target_coverage = np.mean(
            ~np.isnan(target_values)
        )

        if overall_coverage < MIN_INPUT_COVERAGE:
            continue

        # Don't accept windows where one feature
        # is extremely poorly observed.
        if np.min(feature_coverage) < 0.60:
            continue

        # Target PM2.5 must be complete.
        if target_coverage < 1.0:
            continue

        # Interpolate short gaps only.
        frame = pd.DataFrame(
            input_values,
            columns=FEATURES
        )

        frame = frame.interpolate(
            method="linear",
            limit=7,
            limit_direction="both"
        )

        prepared = frame.values

        if np.isnan(prepared).any():
            continue

        X.append(prepared)
        Y.append(target_values)

        metadata.append({

            "openaq_location_id":
                location_id,

            "station_name":
                station_name,

            "urban_ward_code":
                ward,

            "input_start":
                input_dates[0],

            "input_end":
                input_dates[-1],

            "forecast_start":
                target_dates[0],

            "forecast_end":
                target_dates[-1],

            "input_coverage_pct":
                overall_coverage * 100,

            "target_coverage_pct":
                target_coverage * 100
        })

X = np.asarray(
    X,
    dtype=np.float32
)

Y = np.asarray(
    Y,
    dtype=np.float32
)

metadata = pd.DataFrame(
    metadata
)

if len(X) == 0:
    raise RuntimeError(
        "No valid V2 sequences created."
    )

OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True
)

np.savez_compressed(
    OUTPUT,
    X=X,
    y=Y
)

metadata.to_csv(
    META,
    index=False
)

print("=" * 70)
print("LSTM-V2 SEQUENCE DATASET")
print("=" * 70)

print(
    "Locations:",
    metadata[
        "openaq_location_id"
    ].nunique()
)

print(
    "Wards:",
    metadata[
        "urban_ward_code"
    ].nunique()
)

print(
    "X shape:",
    X.shape
)

print(
    "Y shape:",
    Y.shape
)

print(
    "Sequences:",
    len(X)
)

print(
    "Features:",
    len(FEATURES)
)

print(
    "Input coverage mean:",
    round(
        metadata[
            "input_coverage_pct"
        ].mean(),
        2
    )
)

print(
    "Input coverage minimum:",
    round(
        metadata[
            "input_coverage_pct"
        ].min(),
        2
    )
)

print("\nSequences by ward:")

print(
    metadata[
        "urban_ward_code"
    ]
    .value_counts()
    .sort_index()
    .to_string()
)

print("\nSaved:")
print(OUTPUT)
print(META)

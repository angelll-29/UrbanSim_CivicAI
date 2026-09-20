import numpy as np
import pandas as pd
from pathlib import Path

INPUT = Path(
    "data/processed/mumbai_openaq_multivariate_daily_aligned.csv"
)

OUTPUT = Path(
    "data/processed/mumbai_multivariate_lstm_sequences.npz"
)

META = Path(
    "data/processed/mumbai_multivariate_lstm_sequence_metadata.csv"
)

FEATURES = [
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

TARGET = "pm25"

# Exclude severely incomplete stations
EXCLUDED_LOCATIONS = {
    6965,   # RC
    6956,   # S
    12039   # T
}

INPUT_DAYS = 60
FORECAST_DAYS = 7

MIN_INPUT_COVERAGE = 0.80
MIN_TARGET_COVERAGE = 1.00

df = pd.read_csv(INPUT)

df["date"] = pd.to_datetime(
    df["date"],
    errors="coerce"
)

df = df[
    ~df["openaq_location_id"].isin(
        EXCLUDED_LOCATIONS
    )
].copy()

df = df.sort_values(
    [
        "openaq_location_id",
        "date"
    ]
)

# ------------------------------------------------------------
# Local interpolation helper
# ------------------------------------------------------------

def interpolate_window(values):

    frame = pd.DataFrame(
        values,
        columns=FEATURES
    )

    # Time-independent linear interpolation
    # only inside the observed window.
    frame = frame.interpolate(
        method="linear",
        limit_direction="both"
    )

    return frame.values


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

    # --------------------------------------------------------
    # Reindex to continuous daily calendar
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Sliding windows
    # --------------------------------------------------------

    total_days = len(group)

    for start in range(
        total_days -
        INPUT_DAYS -
        FORECAST_DAYS +
        1
    ):

        input_start = start

        input_end = (
            start + INPUT_DAYS
        )

        target_end = (
            input_end +
            FORECAST_DAYS
        )

        input_values = values[
            input_start:input_end
        ]

        target_values = values[
            input_end:target_end,
            0
        ]

        input_dates = dates[
            input_start:input_end
        ]

        target_dates = dates[
            input_end:target_end
        ]

        # ----------------------------------------------------
        # Coverage before interpolation
        # ----------------------------------------------------

        input_coverage = (
            np.mean(
                ~np.isnan(
                    input_values
                ),
                axis=0
            )
        )

        overall_input_coverage = (
            np.mean(input_coverage)
        )

        target_coverage = np.mean(
            ~np.isnan(target_values)
        )

        if (
            overall_input_coverage
            < MIN_INPUT_COVERAGE
        ):
            continue

        if (
            target_coverage
            < MIN_TARGET_COVERAGE
        ):
            continue

        # ----------------------------------------------------
        # Do not allow a feature to have extremely poor
        # coverage inside a window.
        # ----------------------------------------------------

        if np.min(
            input_coverage
        ) < 0.60:
            continue

        # ----------------------------------------------------
        # Interpolate only internal/small gaps.
        #
        # limit=7 means no long missing stretch is silently
        # reconstructed.
        # ----------------------------------------------------

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

        # Any remaining NaN means this window is not suitable.
        if np.isnan(prepared).any():
            continue

        # Target must already be complete.
        if np.isnan(target_values).any():
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
                overall_input_coverage * 100,

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
        "No valid sequences were created."
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
print("MULTIVARIATE LSTM SEQUENCE DATASET")
print("=" * 70)

print(
    "Excluded locations:",
    sorted(EXCLUDED_LOCATIONS)
)

print(
    "Locations used:",
    metadata[
        "openaq_location_id"
    ].nunique()
)

print(
    "Wards used:",
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

print("\nSequences by location:")

print(
    metadata[
        [
            "openaq_location_id",
            "urban_ward_code"
        ]
    ]
    .value_counts()
    .sort_index()
    .to_string()
)

print("\nSaved:")
print(OUTPUT)
print(META)

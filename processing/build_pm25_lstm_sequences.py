import pandas as pd
import numpy as np
from pathlib import Path

INPUT = Path(
    "data/processed/mumbai_pm25_ward_daily.csv"
)

OUTPUT = Path(
    "data/processed/mumbai_pm25_lstm_sequences.npz"
)

META_OUTPUT = Path(
    "data/processed/mumbai_pm25_lstm_sequence_metadata.csv"
)

INPUT_DAYS = 60
FORECAST_DAYS = 7

MIN_INPUT_COVERAGE = 0.80
MIN_TARGET_COVERAGE = 0.80

df = pd.read_csv(INPUT)

df["date"] = pd.to_datetime(
    df["date"],
    errors="coerce"
)

df["pm25_mean"] = pd.to_numeric(
    df["pm25_mean"],
    errors="coerce"
)

df = df.sort_values(
    ["urban_ward_code", "date"]
)

X = []
y = []
metadata = []

for ward, ward_df in df.groupby(
    "urban_ward_code"
):

    ward_df = ward_df.set_index("date")

    # Complete daily calendar
    full_dates = pd.date_range(
        ward_df.index.min(),
        ward_df.index.max(),
        freq="D"
    )

    series = (
        ward_df["pm25_mean"]
        .reindex(full_dates)
    )

    values = series.to_numpy(
        dtype=float
    )

    for i in range(
        INPUT_DAYS,
        len(values) - FORECAST_DAYS + 1
    ):

        input_values = values[
            i - INPUT_DAYS:i
        ]

        target_values = values[
            i:i + FORECAST_DAYS
        ]

        input_valid = np.isfinite(
            input_values
        )

        target_valid = np.isfinite(
            target_values
        )

        input_coverage = (
            input_valid.mean()
        )

        target_coverage = (
            target_valid.mean()
        )

        if (
            input_coverage <
            MIN_INPUT_COVERAGE
        ):
            continue

        if (
            target_coverage <
            MIN_TARGET_COVERAGE
        ):
            continue

        # Store missing values as NaN.
        # They will be handled explicitly
        # during model preprocessing.
        X.append(
            input_values
        )

        y.append(
            target_values
        )

        forecast_start = full_dates[i]

        metadata.append({

            "urban_ward_code":
                ward,

            "input_start":
                full_dates[
                    i - INPUT_DAYS
                ],

            "input_end":
                full_dates[
                    i - 1
                ],

            "forecast_start":
                forecast_start,

            "forecast_end":
                full_dates[
                    i + FORECAST_DAYS - 1
                ],

            "input_coverage_pct":
                input_coverage * 100,

            "target_coverage_pct":
                target_coverage * 100
        })

X = np.array(
    X,
    dtype=np.float32
)

y = np.array(
    y,
    dtype=np.float32
)

metadata = pd.DataFrame(
    metadata
)

# ------------------------------------------------------------
# Save
# ------------------------------------------------------------

OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True
)

np.savez_compressed(
    OUTPUT,
    X=X,
    y=y
)

metadata.to_csv(
    META_OUTPUT,
    index=False
)

# ------------------------------------------------------------
# Report
# ------------------------------------------------------------

print("=" * 70)
print("LSTM SEQUENCE DATASET")
print("=" * 70)

print("Input window:", INPUT_DAYS, "days")
print("Forecast horizon:", FORECAST_DAYS, "days")

print(
    "Minimum input coverage:",
    MIN_INPUT_COVERAGE * 100,
    "%"
)

print(
    "Minimum target coverage:",
    MIN_TARGET_COVERAGE * 100,
    "%"
)

print("\nShapes:")
print("X:", X.shape)
print("y:", y.shape)

print(
    "\nTotal sequences:",
    len(X)
)

print(
    "Wards:",
    metadata["urban_ward_code"].nunique()
)

print("\nSequences by ward:")
print(
    metadata["urban_ward_code"]
    .value_counts()
    .sort_index()
    .to_string()
)

print("\nInput coverage:")
print(
    metadata["input_coverage_pct"]
    .describe()
    .to_string()
)

print("\nTarget coverage:")
print(
    metadata["target_coverage_pct"]
    .describe()
    .to_string()
)

print("\nNaN values in X:")
print(
    np.isnan(X).sum()
)

print("\nNaN values in y:")
print(
    np.isnan(y).sum()
)

print("\nSaved:")
print(OUTPUT)
print(META_OUTPUT)

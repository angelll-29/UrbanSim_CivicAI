import pandas as pd
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

INPUT = ROOT / "data" / "processed" / "stgnn_ward_daily_features.csv"
EDGES = ROOT / "data" / "processed" / "stgnn_ward_edges.csv"

OUT_NPZ = ROOT / "data" / "processed" / "stgnn_sequences.npz"
OUT_META = ROOT / "data" / "processed" / "stgnn_sequence_metadata.csv"

WARDS = [
    "E", "FN", "FS", "GS", "HE", "KE",
    "L", "ME", "N", "PN", "RC"
]

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

INPUT_DAYS = 60
FORECAST_DAYS = 7

MIN_INPUT_COVERAGE = 0.80
MIN_FEATURE_COVERAGE = 0.60

print("Loading ST-GNN ward-day data...")

df = pd.read_csv(INPUT)
df["date"] = pd.to_datetime(df["date"])

df["ward_code"] = (
    df["ward_code"]
    .astype(str)
    .str.strip()
    .str.upper()
)

df = df[df["ward_code"].isin(WARDS)].copy()

df = df.sort_values(
    ["date", "ward_code"]
)

# ---------------------------------------------------------
# Build complete daily calendar
# ---------------------------------------------------------

all_dates = pd.date_range(
    df["date"].min(),
    df["date"].max(),
    freq="D"
)

print(
    f"Date range: "
    f"{all_dates.min().date()} -> {all_dates.max().date()}"
)

# Remove timezone so indexing is consistent
if all_dates.tz is not None:
    all_dates = all_dates.tz_localize(None)

df["date"] = df["date"].dt.tz_localize(None)

# ---------------------------------------------------------
# Create tensors
# ---------------------------------------------------------

date_index = pd.Index(all_dates)

date_to_idx = {
    date: i for i, date in enumerate(date_index)
}

ward_to_idx = {
    ward: i for i, ward in enumerate(WARDS)
}

T = len(all_dates)
N = len(WARDS)
F = len(FEATURES)

data = np.full(
    (T, N, F),
    np.nan,
    dtype=np.float32
)

for _, row in df.iterrows():

    date = row["date"]
    ward = row["ward_code"]

    if date not in date_to_idx:
        continue

    t = date_to_idx[date]
    n = ward_to_idx[ward]

    for f, feature in enumerate(FEATURES):
        value = row[feature]

        if pd.notna(value):
            data[t, n, f] = float(value)

print(f"\nRaw tensor shape: {data.shape}")

# ---------------------------------------------------------
# Missing-data interpolation
#
# Only short temporal gaps are interpolated.
# We do NOT fill long gaps with arbitrary values.
# ---------------------------------------------------------

print("\nInterpolating short temporal gaps...")

MAX_INTERPOLATION_GAP = 7

for n in range(N):

    for f in range(F):

        series = pd.Series(
            data[:, n, f],
            index=date_index
        )

        series = series.interpolate(
            method="linear",
            limit=MAX_INTERPOLATION_GAP,
            limit_direction="both"
        )

        data[:, n, f] = series.values.astype(
            np.float32
        )

# ---------------------------------------------------------
# Build sequences
# ---------------------------------------------------------

X_list = []
Y_list = []
metadata = []

candidate_count = 0
accepted_count = 0

max_start = T - INPUT_DAYS - FORECAST_DAYS + 1

for start in range(max_start):

    candidate_count += 1

    input_start = start
    input_end = start + INPUT_DAYS

    target_start = input_end
    target_end = target_start + FORECAST_DAYS

    X_window = data[
        input_start:input_end
    ].copy()

    Y_window = data[
        target_start:target_end,
        :,
        0
    ].copy()

    # -----------------------------------------------------
    # Input coverage
    # -----------------------------------------------------

    input_valid = np.isfinite(X_window)

    overall_input_coverage = (
        input_valid.mean()
    )

    if overall_input_coverage < MIN_INPUT_COVERAGE:
        continue

    # Each feature must have reasonable coverage
    feature_coverage = input_valid.mean(
        axis=(0, 1)
    )

    if np.any(
        feature_coverage < MIN_FEATURE_COVERAGE
    ):
        continue

    # -----------------------------------------------------
    # Target must be complete
    # -----------------------------------------------------

    if not np.isfinite(Y_window).all():
        continue

    # -----------------------------------------------------
    # Remaining input NaNs
    #
    # After short-gap interpolation, use feature-wise
    # median calculated only inside this input window.
    # This is not used for target values.
    # -----------------------------------------------------

    for f in range(F):

        feature_values = X_window[:, :, f]

        valid_values = feature_values[
            np.isfinite(feature_values)
        ]

        if len(valid_values) == 0:
            continue

        median_value = np.median(
            valid_values
        )

        missing_mask = ~np.isfinite(
            feature_values
        )

        feature_values[missing_mask] = (
            median_value
        )

        X_window[:, :, f] = feature_values

    X_list.append(X_window)
    Y_list.append(Y_window)

    metadata.append({
        "input_start": date_index[input_start],
        "input_end": date_index[input_end - 1],
        "forecast_start": date_index[target_start],
        "forecast_end": date_index[target_end - 1],
        "input_coverage": overall_input_coverage,
        "min_feature_coverage": feature_coverage.min()
    })

    accepted_count += 1

# ---------------------------------------------------------
# Convert to arrays
# ---------------------------------------------------------

X = np.stack(X_list).astype(
    np.float32
)

Y = np.stack(Y_list).astype(
    np.float32
)

metadata_df = pd.DataFrame(
    metadata
)

# ---------------------------------------------------------
# Save
# ---------------------------------------------------------

np.savez_compressed(
    OUT_NPZ,
    X=X,
    Y=Y,
    wards=np.array(WARDS),
    features=np.array(FEATURES)
)

metadata_df.to_csv(
    OUT_META,
    index=False
)

print("\n========================================")
print("ST-GNN SEQUENCE DATASET COMPLETE")
print("========================================")

print(f"Candidate windows : {candidate_count}")
print(f"Accepted sequences: {accepted_count}")

print(f"\nX shape: {X.shape}")
print(f"Y shape: {Y.shape}")

print(
    "\nExpected format:"
    "\nX = [samples, 60 days, 11 wards, 9 features]"
    "\nY = [samples, 11 wards, 7 future PM2.5 days]"
)

print(
    f"\nMean input coverage: "
    f"{metadata_df['input_coverage'].mean():.4f}"
)

print(
    f"Minimum input coverage: "
    f"{metadata_df['input_coverage'].min():.4f}"
)

print(f"\nSaved:")
print(OUT_NPZ)
print(OUT_META)

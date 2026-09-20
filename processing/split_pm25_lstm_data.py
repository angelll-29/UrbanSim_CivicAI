import numpy as np
import pandas as pd
from pathlib import Path

INPUT = Path(
    "data/processed/mumbai_pm25_lstm_sequences.npz"
)

META = Path(
    "data/processed/mumbai_pm25_lstm_sequence_metadata.csv"
)

OUT_DIR = Path(
    "data/processed/lstm"
)

OUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

data = np.load(INPUT)

X = data["X"].astype(np.float32)
y = data["y"].astype(np.float32)

meta = pd.read_csv(META)

meta["forecast_start"] = pd.to_datetime(
    meta["forecast_start"]
)

# ------------------------------------------------------------
# Sort chronologically
# ------------------------------------------------------------

order = np.argsort(
    meta["forecast_start"].values
)

X = X[order]
y = y[order]
meta = meta.iloc[order].reset_index(drop=True)

# ------------------------------------------------------------
# Split based on forecast start date
# ------------------------------------------------------------

dates = meta["forecast_start"]

unique_dates = np.sort(
    dates.unique()
)

n_dates = len(unique_dates)

train_end = unique_dates[
    int(n_dates * 0.70) - 1
]

val_end = unique_dates[
    int(n_dates * 0.85) - 1
]

train_mask = dates <= train_end

val_mask = (
    (dates > train_end) &
    (dates <= val_end)
)

test_mask = dates > val_end

# ------------------------------------------------------------
# Extract splits
# ------------------------------------------------------------

X_train = X[train_mask]
y_train = y[train_mask]

X_val = X[val_mask]
y_val = y[val_mask]

X_test = X[test_mask]
y_test = y[test_mask]

meta_train = meta[train_mask]
meta_val = meta[val_mask]
meta_test = meta[test_mask]

# ------------------------------------------------------------
# Report
# ------------------------------------------------------------

print("=" * 70)
print("TEMPORAL TRAIN / VALIDATION / TEST SPLIT")
print("=" * 70)

print(
    "Train:",
    X_train.shape,
    y_train.shape
)

print(
    "Validation:",
    X_val.shape,
    y_val.shape
)

print(
    "Test:",
    X_test.shape,
    y_test.shape
)

print("\nDate ranges:")

print(
    "Train:",
    meta_train["forecast_start"].min(),
    "→",
    meta_train["forecast_start"].max()
)

print(
    "Validation:",
    meta_val["forecast_start"].min(),
    "→",
    meta_val["forecast_start"].max()
)

print(
    "Test:",
    meta_test["forecast_start"].min(),
    "→",
    meta_test["forecast_start"].max()
)

# ------------------------------------------------------------
# Missing-value report
# ------------------------------------------------------------

print("\nMissing values:")

print(
    "Train X:",
    np.isnan(X_train).sum()
)

print(
    "Train y:",
    np.isnan(y_train).sum()
)

print(
    "Validation X:",
    np.isnan(X_val).sum()
)

print(
    "Validation y:",
    np.isnan(y_val).sum()
)

print(
    "Test X:",
    np.isnan(X_test).sum()
)

print(
    "Test y:",
    np.isnan(y_test).sum()
)

# ------------------------------------------------------------
# Save
# ------------------------------------------------------------

np.savez_compressed(
    OUT_DIR / "train.npz",
    X=X_train,
    y=y_train
)

np.savez_compressed(
    OUT_DIR / "validation.npz",
    X=X_val,
    y=y_val
)

np.savez_compressed(
    OUT_DIR / "test.npz",
    X=X_test,
    y=y_test
)

meta_train.to_csv(
    OUT_DIR / "train_metadata.csv",
    index=False
)

meta_val.to_csv(
    OUT_DIR / "validation_metadata.csv",
    index=False
)

meta_test.to_csv(
    OUT_DIR / "test_metadata.csv",
    index=False
)

print("\nSaved:")
print(OUT_DIR)

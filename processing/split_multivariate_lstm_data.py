import numpy as np
import pandas as pd
from pathlib import Path

INPUT = Path(
    "data/processed/mumbai_multivariate_lstm_sequences.npz"
)

META = Path(
    "data/processed/mumbai_multivariate_lstm_sequence_metadata.csv"
)

OUT_DIR = Path(
    "data/processed/multivariate_lstm"
)

OUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

data = np.load(INPUT)

X = data["X"]
y = data["y"]

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
meta = meta.iloc[order].reset_index(
    drop=True
)

n = len(meta)

# ------------------------------------------------------------
# Chronological 70 / 15 / 15 split
# ------------------------------------------------------------

train_end = int(
    n * 0.70
)

validation_end = int(
    n * 0.85
)

X_train = X[:train_end]
y_train = y[:train_end]
meta_train = meta.iloc[
    :train_end
].copy()

X_val = X[
    train_end:validation_end
]

y_val = y[
    train_end:validation_end
]

meta_val = meta.iloc[
    train_end:validation_end
].copy()

X_test = X[
    validation_end:
]

y_test = y[
    validation_end:
]

meta_test = meta.iloc[
    validation_end:
].copy()

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

# ------------------------------------------------------------
# Report
# ------------------------------------------------------------

print("=" * 70)
print("MULTIVARIATE LSTM CHRONOLOGICAL SPLIT")
print("=" * 70)

print("\nTRAIN")
print(
    "X:",
    X_train.shape,
    "Y:",
    y_train.shape
)

print(
    "Forecast dates:",
    meta_train["forecast_start"].min().date(),
    "→",
    meta_train["forecast_start"].max().date()
)

print("\nVALIDATION")
print(
    "X:",
    X_val.shape,
    "Y:",
    y_val.shape
)

print(
    "Forecast dates:",
    meta_val["forecast_start"].min().date(),
    "→",
    meta_val["forecast_start"].max().date()
)

print("\nTEST")
print(
    "X:",
    X_test.shape,
    "Y:",
    y_test.shape
)

print(
    "Forecast dates:",
    meta_test["forecast_start"].min().date(),
    "→",
    meta_test["forecast_start"].max().date()
)

print("\nTotal sequences:", n)

print(
    "Train:",
    len(X_train),
    f"({len(X_train)/n*100:.2f}%)"
)

print(
    "Validation:",
    len(X_val),
    f"({len(X_val)/n*100:.2f}%)"
)

print(
    "Test:",
    len(X_test),
    f"({len(X_test)/n*100:.2f}%)"
)

print("\nSaved to:")
print(OUT_DIR)

import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.preprocessing import StandardScaler
import joblib

BASE = Path("data/processed/lstm")

# ------------------------------------------------------------
# Load
# ------------------------------------------------------------

train = np.load(BASE / "train.npz")
val = np.load(BASE / "validation.npz")
test = np.load(BASE / "test.npz")

X_train = train["X"].astype(np.float32)
y_train = train["y"].astype(np.float32)

X_val = val["X"].astype(np.float32)
y_val = val["y"].astype(np.float32)

X_test = test["X"].astype(np.float32)
y_test = test["y"].astype(np.float32)

print("=" * 70)
print("LSTM DATA PREPARATION")
print("=" * 70)

# ------------------------------------------------------------
# Remove sequences with missing targets
# ------------------------------------------------------------

train_valid = np.isfinite(y_train).all(axis=1)
val_valid = np.isfinite(y_val).all(axis=1)
test_valid = np.isfinite(y_test).all(axis=1)

X_train = X_train[train_valid]
y_train = y_train[train_valid]

X_val = X_val[val_valid]
y_val = y_val[val_valid]

X_test = X_test[test_valid]
y_test = y_test[test_valid]

print("After target QC:")
print("Train:", X_train.shape, y_train.shape)
print("Validation:", X_val.shape, y_val.shape)
print("Test:", X_test.shape, y_test.shape)

# ------------------------------------------------------------
# Input interpolation
# ------------------------------------------------------------

def interpolate_windows(X):

    X = X.copy()

    for i in range(len(X)):

        row = X[i]

        valid = np.isfinite(row)

        if valid.sum() == 0:
            raise ValueError(
                "Found an input window with no valid observations."
            )

        if not valid.all():

            indices = np.arange(len(row))

            row[~valid] = np.interp(
                indices[~valid],
                indices[valid],
                row[valid]
            )

        X[i] = row

    return X


X_train = interpolate_windows(X_train)
X_val = interpolate_windows(X_val)
X_test = interpolate_windows(X_test)

# ------------------------------------------------------------
# Verify no NaNs
# ------------------------------------------------------------

print("\nNaN check after interpolation:")
print("Train X:", np.isnan(X_train).sum())
print("Validation X:", np.isnan(X_val).sum())
print("Test X:", np.isnan(X_test).sum())

# ------------------------------------------------------------
# Scale using TRAIN ONLY
# ------------------------------------------------------------

scaler = StandardScaler()

# Each observation is a single PM2.5 value.
scaler.fit(
    X_train.reshape(-1, 1)
)

X_train_scaled = scaler.transform(
    X_train.reshape(-1, 1)
).reshape(
    X_train.shape
)

X_val_scaled = scaler.transform(
    X_val.reshape(-1, 1)
).reshape(
    X_val.shape
)

X_test_scaled = scaler.transform(
    X_test.reshape(-1, 1)
).reshape(
    X_test.shape
)

# Scale target using same training-derived scaler.
y_train_scaled = scaler.transform(
    y_train.reshape(-1, 1)
).reshape(
    y_train.shape
)

y_val_scaled = scaler.transform(
    y_val.reshape(-1, 1)
).reshape(
    y_val.shape
)

y_test_scaled = scaler.transform(
    y_test.reshape(-1, 1)
).reshape(
    y_test.shape
)

# ------------------------------------------------------------
# Add LSTM feature dimension
# ------------------------------------------------------------

X_train_scaled = X_train_scaled[..., np.newaxis]
X_val_scaled = X_val_scaled[..., np.newaxis]
X_test_scaled = X_test_scaled[..., np.newaxis]

# ------------------------------------------------------------
# Save
# ------------------------------------------------------------

np.savez_compressed(
    BASE / "train_prepared.npz",
    X=X_train_scaled,
    y=y_train_scaled
)

np.savez_compressed(
    BASE / "validation_prepared.npz",
    X=X_val_scaled,
    y=y_val_scaled
)

np.savez_compressed(
    BASE / "test_prepared.npz",
    X=X_test_scaled,
    y=y_test_scaled
)

joblib.dump(
    scaler,
    BASE / "pm25_lstm_scaler.joblib"
)

print("\nFinal shapes:")
print("Train:", X_train_scaled.shape, y_train_scaled.shape)
print("Validation:", X_val_scaled.shape, y_val_scaled.shape)
print("Test:", X_test_scaled.shape, y_test_scaled.shape)

print("\nScaler:")
print("Mean:", scaler.mean_[0])
print("Scale:", scaler.scale_[0])

print("\nSaved:")
print(BASE / "train_prepared.npz")
print(BASE / "validation_prepared.npz")
print(BASE / "test_prepared.npz")
print(BASE / "pm25_lstm_scaler.joblib")

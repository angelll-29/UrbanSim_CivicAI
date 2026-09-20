import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from sklearn.preprocessing import StandardScaler

BASE = Path("data/processed/multivariate_lstm")

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

# ------------------------------------------------------------
# Feature scaler
# Fit ONLY on training observations
# ------------------------------------------------------------

feature_scaler = StandardScaler()

X_train_2d = X_train.reshape(
    -1,
    X_train.shape[-1]
)

feature_scaler.fit(X_train_2d)

X_train_scaled = feature_scaler.transform(
    X_train_2d
).reshape(X_train.shape)

X_val_scaled = feature_scaler.transform(
    X_val.reshape(-1, X_val.shape[-1])
).reshape(X_val.shape)

X_test_scaled = feature_scaler.transform(
    X_test.reshape(-1, X_test.shape[-1])
).reshape(X_test.shape)

# ------------------------------------------------------------
# Target scaler
# PM2.5 is feature index 0.
# Fit ONLY on training PM2.5.
# ------------------------------------------------------------

target_scaler = StandardScaler()

target_scaler.fit(
    y_train.reshape(-1, 1)
)

y_train_scaled = target_scaler.transform(
    y_train.reshape(-1, 1)
).reshape(y_train.shape)

y_val_scaled = target_scaler.transform(
    y_val.reshape(-1, 1)
).reshape(y_val.shape)

y_test_scaled = target_scaler.transform(
    y_test.reshape(-1, 1)
).reshape(y_test.shape)

# ------------------------------------------------------------
# Save
# ------------------------------------------------------------

np.savez_compressed(
    BASE / "train_prepared.npz",
    X=X_train_scaled.astype(np.float32),
    y=y_train_scaled.astype(np.float32)
)

np.savez_compressed(
    BASE / "validation_prepared.npz",
    X=X_val_scaled.astype(np.float32),
    y=y_val_scaled.astype(np.float32)
)

np.savez_compressed(
    BASE / "test_prepared.npz",
    X=X_test_scaled.astype(np.float32),
    y=y_test_scaled.astype(np.float32)
)

joblib.dump(
    feature_scaler,
    BASE / "multivariate_feature_scaler.joblib"
)

joblib.dump(
    target_scaler,
    BASE / "multivariate_pm25_target_scaler.joblib"
)

# ------------------------------------------------------------
# Report
# ------------------------------------------------------------

print("=" * 70)
print("MULTIVARIATE LSTM DATA PREPARATION")
print("=" * 70)

print("\nFeature scaling:")

for feature, mean, scale in zip(
    FEATURES,
    feature_scaler.mean_,
    feature_scaler.scale_
):
    print(
        f"{feature:20s} "
        f"mean={mean:.4f} "
        f"scale={scale:.4f}"
    )

print("\nPM2.5 target scaling:")
print(
    f"mean={target_scaler.mean_[0]:.4f}"
)

print(
    f"scale={target_scaler.scale_[0]:.4f}"
)

print("\nShapes:")
print(
    "Train:",
    X_train_scaled.shape,
    y_train_scaled.shape
)

print(
    "Validation:",
    X_val_scaled.shape,
    y_val_scaled.shape
)

print(
    "Test:",
    X_test_scaled.shape,
    y_test_scaled.shape
)

print("\nNaN check:")

print(
    "Train X:",
    np.isnan(X_train_scaled).sum()
)

print(
    "Train y:",
    np.isnan(y_train_scaled).sum()
)

print(
    "Validation X:",
    np.isnan(X_val_scaled).sum()
)

print(
    "Validation y:",
    np.isnan(y_val_scaled).sum()
)

print(
    "Test X:",
    np.isnan(X_test_scaled).sum()
)

print(
    "Test y:",
    np.isnan(y_test_scaled).sum()
)

print("\nSaved:")
print(
    BASE / "train_prepared.npz"
)

print(
    BASE / "validation_prepared.npz"
)

print(
    BASE / "test_prepared.npz"
)

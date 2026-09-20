import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from sklearn.preprocessing import StandardScaler

BASE = Path("data/processed/lstm_v2")

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
# Feature scaler — TRAIN ONLY
# ------------------------------------------------------------

feature_scaler = StandardScaler()

feature_scaler.fit(
    X_train.reshape(
        -1,
        X_train.shape[-1]
    )
)

X_train_scaled = feature_scaler.transform(
    X_train.reshape(-1, X_train.shape[-1])
).reshape(X_train.shape)

X_val_scaled = feature_scaler.transform(
    X_val.reshape(-1, X_val.shape[-1])
).reshape(X_val.shape)

X_test_scaled = feature_scaler.transform(
    X_test.reshape(-1, X_test.shape[-1])
).reshape(X_test.shape)

# ------------------------------------------------------------
# PM2.5 target scaler — TRAIN ONLY
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
    BASE / "lstm_v2_feature_scaler.joblib"
)

joblib.dump(
    target_scaler,
    BASE / "lstm_v2_pm25_target_scaler.joblib"
)

print("=" * 70)
print("LSTM-V2 DATA PREPARATION")
print("=" * 70)

print("\nFeature scaling:")

for feature, mean, scale in zip(
    FEATURES,
    feature_scaler.mean_,
    feature_scaler.scale_
):
    print(
        f"{feature:24s} "
        f"mean={mean:.4f} "
        f"scale={scale:.4f}"
    )

print("\nPM2.5 target:")
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

for name, arr in [
    ("Train X", X_train_scaled),
    ("Train y", y_train_scaled),
    ("Validation X", X_val_scaled),
    ("Validation y", y_val_scaled),
    ("Test X", X_test_scaled),
    ("Test y", y_test_scaled)
]:
    print(
        f"{name}: {np.isnan(arr).sum()}"
    )

print("\nSaved:")
print(BASE)

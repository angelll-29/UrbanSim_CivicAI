import numpy as np
import joblib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

INPUT_DIR = ROOT / "data" / "processed" / "stgnn"
OUT_DIR = ROOT / "data" / "processed" / "stgnn"
MODEL_DIR = ROOT / "ml" / "models"

MODEL_DIR.mkdir(
    parents=True,
    exist_ok=True
)

FEATURE_NAMES = [
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

# ---------------------------------------------------------
# Load splits
# ---------------------------------------------------------

train = np.load(INPUT_DIR / "train.npz")
val = np.load(INPUT_DIR / "validation.npz")
test = np.load(INPUT_DIR / "test.npz")

X_train = train["X"].astype(np.float32)
Y_train = train["Y"].astype(np.float32)

X_val = val["X"].astype(np.float32)
Y_val = val["Y"].astype(np.float32)

X_test = test["X"].astype(np.float32)
Y_test = test["Y"].astype(np.float32)

print("Original shapes:")
print("Train:", X_train.shape, Y_train.shape)
print("Val  :", X_val.shape, Y_val.shape)
print("Test :", X_test.shape, Y_test.shape)

# ---------------------------------------------------------
# Fit feature scaler ONLY on training data
#
# Shape:
# [samples, time, wards, features]
# ---------------------------------------------------------

feature_mean = X_train.mean(
    axis=(0, 1, 2)
)

feature_std = X_train.std(
    axis=(0, 1, 2)
)

# Protect against zero variance
feature_std = np.where(
    feature_std < 1e-8,
    1.0,
    feature_std
)

# ---------------------------------------------------------
# Transform features
# ---------------------------------------------------------

X_train_scaled = (
    X_train - feature_mean
) / feature_std

X_val_scaled = (
    X_val - feature_mean
) / feature_std

X_test_scaled = (
    X_test - feature_mean
) / feature_std

# ---------------------------------------------------------
# PM2.5 target scaler
#
# Fit ONLY on training targets
# ---------------------------------------------------------

target_mean = Y_train.mean()
target_std = Y_train.std()

if target_std < 1e-8:
    target_std = 1.0

Y_train_scaled = (
    Y_train - target_mean
) / target_std

Y_val_scaled = (
    Y_val - target_mean
) / target_std

Y_test_scaled = (
    Y_test - target_mean
) / target_std

# ---------------------------------------------------------
# Save prepared datasets
# ---------------------------------------------------------

np.savez_compressed(
    OUT_DIR / "train_prepared.npz",
    X=X_train_scaled.astype(np.float32),
    Y=Y_train_scaled.astype(np.float32),
    wards=train["wards"],
    features=train["features"]
)

np.savez_compressed(
    OUT_DIR / "validation_prepared.npz",
    X=X_val_scaled.astype(np.float32),
    Y=Y_val_scaled.astype(np.float32),
    wards=val["wards"],
    features=val["features"]
)

np.savez_compressed(
    OUT_DIR / "test_prepared.npz",
    X=X_test_scaled.astype(np.float32),
    Y=Y_test_scaled.astype(np.float32),
    wards=test["wards"],
    features=test["features"]
)

# ---------------------------------------------------------
# Save scaler
# ---------------------------------------------------------

scaler = {
    "feature_names": FEATURE_NAMES,
    "feature_mean": feature_mean,
    "feature_std": feature_std,
    "target_mean": float(target_mean),
    "target_std": float(target_std)
}

joblib.dump(
    scaler,
    MODEL_DIR / "stgnn_scaler.joblib"
)

# ---------------------------------------------------------
# Validation report
# ---------------------------------------------------------

print("\n========================================")
print("ST-GNN SCALING COMPLETE")
print("========================================")

print("\nTraining feature statistics:")

for name, mean, std in zip(
    FEATURE_NAMES,
    feature_mean,
    feature_std
):
    print(
        f"{name:20s} "
        f"mean={mean:.6f} "
        f"std={std:.6f}"
    )

print("\nPM2.5 target:")
print(f"mean={target_mean:.6f}")
print(f"std ={target_std:.6f}")

print("\nScaled training feature mean:")
print(
    f"{X_train_scaled.mean():.8f}"
)

print("Scaled training feature std:")
print(
    f"{X_train_scaled.std():.8f}"
)

print("\nPrepared shapes:")
print(
    "Train:",
    X_train_scaled.shape,
    Y_train_scaled.shape
)

print(
    "Val  :",
    X_val_scaled.shape,
    Y_val_scaled.shape
)

print(
    "Test :",
    X_test_scaled.shape,
    Y_test_scaled.shape
)

print("\nSaved:")
print(OUT_DIR / "train_prepared.npz")
print(OUT_DIR / "validation_prepared.npz")
print(OUT_DIR / "test_prepared.npz")
print(MODEL_DIR / "stgnn_scaler.joblib")

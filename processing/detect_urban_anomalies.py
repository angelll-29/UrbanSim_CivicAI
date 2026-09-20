from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from tensorflow import keras


# =========================================================
# URBANSIM — AUTOENCODER ANOMALY DETECTION
# =========================================================

BASE = Path(__file__).resolve().parents[1]

FEATURE_FILE = BASE / "data" / "processed" / "urban_ai_features.csv"
MODEL_FILE = BASE / "ml" / "models" / "urban_autoencoder.keras"
SCALER_FILE = BASE / "ml" / "models" / "urban_autoencoder_scaler.joblib"

OUTPUT_FILE = (
    BASE
    / "data"
    / "processed"
    / "urban_ward_anomaly_scores.csv"
)


print("=" * 60)
print("URBANSIM AUTOENCODER ANOMALY DETECTION")
print("=" * 60)


# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------

df = pd.read_csv(FEATURE_FILE)

ward_codes = df["ward_code"].astype(str)

feature_columns = [
    c for c in df.columns
    if c != "ward_code"
]

X = df[feature_columns].astype(float).values

print(f"\nWards: {len(df)}")
print(f"Features: {len(feature_columns)}")


# ---------------------------------------------------------
# LOAD MODEL + SCALER
# ---------------------------------------------------------

print("\nLoading Autoencoder...")

model = keras.models.load_model(MODEL_FILE)
scaler = joblib.load(SCALER_FILE)

X_scaled = scaler.transform(X)


# ---------------------------------------------------------
# RECONSTRUCTION
# ---------------------------------------------------------

X_reconstructed = model.predict(
    X_scaled,
    verbose=0
)


# ---------------------------------------------------------
# ANOMALY SCORE
# ---------------------------------------------------------

# Mean squared reconstruction error per ward

reconstruction_error = np.mean(
    np.square(X_scaled - X_reconstructed),
    axis=1
)


# Mean absolute reconstruction error

reconstruction_mae = np.mean(
    np.abs(X_scaled - X_reconstructed),
    axis=1
)


# ---------------------------------------------------------
# DATA-DRIVEN THRESHOLD
# ---------------------------------------------------------

threshold = np.percentile(
    reconstruction_error,
    90
)


anomaly_flag = (
    reconstruction_error >= threshold
)


# ---------------------------------------------------------
# PERCENTILE SCORE
# ---------------------------------------------------------

percentile_score = (
    pd.Series(reconstruction_error)
    .rank(pct=True)
    * 100
).values


# ---------------------------------------------------------
# RESULT
# ---------------------------------------------------------

result = pd.DataFrame({
    "ward_code": ward_codes,
    "reconstruction_mse": reconstruction_error,
    "reconstruction_mae": reconstruction_mae,
    "anomaly_percentile": percentile_score,
    "anomaly_threshold_mse": threshold,
    "anomaly_candidate": anomaly_flag
})


result = result.sort_values(
    "reconstruction_mse",
    ascending=False
).reset_index(drop=True)


# ---------------------------------------------------------
# SAVE
# ---------------------------------------------------------

result.to_csv(
    OUTPUT_FILE,
    index=False
)


# ---------------------------------------------------------
# REPORT
# ---------------------------------------------------------

print("\n" + "=" * 60)
print("ANOMALY DETECTION RESULTS")
print("=" * 60)

print(f"\nThreshold MSE: {threshold:.6f}")

print(
    f"Anomaly candidates: "
    f"{anomaly_flag.sum()} / {len(result)}"
)

print("\nTop anomaly candidates:")

print(
    result[
        [
            "ward_code",
            "reconstruction_mse",
            "reconstruction_mae",
            "anomaly_percentile",
            "anomaly_candidate"
        ]
    ]
    .head(10)
    .to_string(index=False)
)


print("\nSaved:")
print(OUTPUT_FILE)

print("\n" + "=" * 60)
print("ANOMALY DETECTION COMPLETE")
print("=" * 60)

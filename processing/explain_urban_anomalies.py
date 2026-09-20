from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from tensorflow import keras


# =========================================================
# URBANSIM — FEATURE-LEVEL ANOMALY EXPLANATION
# =========================================================

BASE = Path(__file__).resolve().parents[1]

FEATURE_FILE = BASE / "data" / "processed" / "urban_ai_features.csv"
ANOMALY_FILE = BASE / "data" / "processed" / "urban_ward_anomaly_scores.csv"
MODEL_FILE = BASE / "ml" / "models" / "urban_autoencoder.keras"
SCALER_FILE = BASE / "ml" / "models" / "urban_autoencoder_scaler.joblib"

OUTPUT_FILE = (
    BASE
    / "data"
    / "processed"
    / "urban_ward_anomaly_feature_evidence.csv"
)


print("=" * 60)
print("URBANSIM FEATURE-LEVEL ANOMALY EXPLANATION")
print("=" * 60)


# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------

df = pd.read_csv(FEATURE_FILE)
anomalies = pd.read_csv(ANOMALY_FILE)

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

model = keras.models.load_model(MODEL_FILE)
scaler = joblib.load(SCALER_FILE)

X_scaled = scaler.transform(
    pd.DataFrame(X, columns=feature_columns)
)

X_reconstructed = model.predict(
    X_scaled,
    verbose=0
)


# ---------------------------------------------------------
# FEATURE-LEVEL ERROR
# ---------------------------------------------------------

feature_squared_error = (
    X_scaled - X_reconstructed
) ** 2

feature_abs_error = np.abs(
    X_scaled - X_reconstructed
)


# ---------------------------------------------------------
# ONLY ANOMALY CANDIDATES
# ---------------------------------------------------------

candidate_wards = anomalies.loc[
    anomalies["anomaly_candidate"] == True,
    "ward_code"
].astype(str).tolist()


print("\nAnomaly candidates:")
print(candidate_wards)


# ---------------------------------------------------------
# BUILD EVIDENCE TABLE
# ---------------------------------------------------------

records = []

for ward in candidate_wards:

    idx = df.index[
        df["ward_code"].astype(str) == ward
    ]

    if len(idx) == 0:
        continue

    i = idx[0]

    errors = feature_squared_error[i]
    abs_errors = feature_abs_error[i]

    # Rank features by reconstruction error
    order = np.argsort(
        errors
    )[::-1]

    for rank, feature_idx in enumerate(order, start=1):

        records.append({
            "ward_code": ward,
            "feature_rank": rank,
            "feature": feature_columns[feature_idx],
            "standardized_squared_error": errors[feature_idx],
            "standardized_absolute_error": abs_errors[feature_idx],
            "actual_value": X[i, feature_idx],
            "reconstructed_standardized_value": (
                X_reconstructed[i, feature_idx]
            )
        })


result = pd.DataFrame(records)


# ---------------------------------------------------------
# SAVE
# ---------------------------------------------------------

result.to_csv(
    OUTPUT_FILE,
    index=False
)


# ---------------------------------------------------------
# DISPLAY TOP CONTRIBUTORS
# ---------------------------------------------------------

print("\n" + "=" * 60)
print("TOP ANOMALY CONTRIBUTORS")
print("=" * 60)

for ward in candidate_wards:

    print(f"\n--- Ward {ward} ---")

    subset = result[
        result["ward_code"] == ward
    ].head(10)

    print(
        subset[
            [
                "feature_rank",
                "feature",
                "standardized_squared_error",
                "actual_value"
            ]
        ].to_string(index=False)
    )


print("\nSaved:")
print(OUTPUT_FILE)

print("\n" + "=" * 60)
print("FEATURE-LEVEL ANALYSIS COMPLETE")
print("=" * 60)

import numpy as np
import pandas as pd
from pathlib import Path

from sklearn.metrics import mean_squared_error, mean_absolute_error
from sklearn.decomposition import PCA

import tensorflow as tf
import joblib

FEATURE_FILE = Path("data/processed/urban_ai_features.csv")
MODEL_FILE = Path("ml/models/urban_autoencoder.keras")
ENCODER_FILE = Path("ml/models/urban_ward_encoder.keras")
SCALER_FILE = Path("ml/models/urban_autoencoder_scaler.joblib")

df = pd.read_csv(FEATURE_FILE)

wards = df["ward_code"].copy()
X = df.drop(columns=["ward_code"]).astype(float)

scaler = joblib.load(SCALER_FILE)
X_scaled = scaler.transform(X)

autoencoder = tf.keras.models.load_model(MODEL_FILE)
encoder = tf.keras.models.load_model(ENCODER_FILE)

# Reconstruction
X_reconstructed = autoencoder.predict(X_scaled, verbose=0)

overall_mse = mean_squared_error(X_scaled, X_reconstructed)
overall_mae = mean_absolute_error(X_scaled, X_reconstructed)

# Per-ward error
ward_mse = np.mean(
    np.square(X_scaled - X_reconstructed),
    axis=1
)

ward_mae = np.mean(
    np.abs(X_scaled - X_reconstructed),
    axis=1
)

ward_results = pd.DataFrame({
    "ward_code": wards,
    "reconstruction_mse": ward_mse,
    "reconstruction_mae": ward_mae
})

# Per-feature error
feature_mse = np.mean(
    np.square(X_scaled - X_reconstructed),
    axis=0
)

feature_mae = np.mean(
    np.abs(X_scaled - X_reconstructed),
    axis=0
)

feature_results = pd.DataFrame({
    "feature": X.columns,
    "mse": feature_mse,
    "mae": feature_mae
}).sort_values("mse", ascending=False)

# Embeddings
embeddings = encoder.predict(X_scaled, verbose=0)

embedding_df = pd.DataFrame(
    embeddings,
    columns=[
        "embedding_1",
        "embedding_2",
        "embedding_3",
        "embedding_4"
    ]
)

embedding_df.insert(0, "ward_code", wards.values)

# PCA visualization coordinates
pca = PCA(n_components=2, random_state=42)
embedding_2d = pca.fit_transform(embeddings)

embedding_df["pca_1"] = embedding_2d[:, 0]
embedding_df["pca_2"] = embedding_2d[:, 1]

# Save validation outputs
Path("data/processed").mkdir(parents=True, exist_ok=True)

ward_results.to_csv(
    "data/processed/autoencoder_ward_reconstruction.csv",
    index=False
)

feature_results.to_csv(
    "data/processed/autoencoder_feature_reconstruction.csv",
    index=False
)

embedding_df.to_csv(
    "data/processed/urban_ward_embeddings_validated.csv",
    index=False
)

print("=" * 60)
print("URBANSIM AUTOENCODER VALIDATION")
print("=" * 60)

print(f"\nSamples: {len(X)}")
print(f"Input features: {X.shape[1]}")
print(f"Latent dimensions: {embeddings.shape[1]}")

print("\nOverall reconstruction:")
print(f"MSE: {overall_mse:.6f}")
print(f"MAE: {overall_mae:.6f}")

print("\nWard reconstruction error:")
print(
    ward_results
    .sort_values("reconstruction_mse", ascending=False)
    .to_string(index=False)
)

print("\nTop feature reconstruction errors:")
print(
    feature_results
    .head(10)
    .to_string(index=False)
)

print("\nPCA explained variance:")
print(
    "PC1:",
    round(pca.explained_variance_ratio_[0], 4)
)

print(
    "PC2:",
    round(pca.explained_variance_ratio_[1], 4)
)

print(
    "PC1 + PC2:",
    round(
        pca.explained_variance_ratio_[:2].sum(),
        4
    )
)

print("\nSaved:")
print("data/processed/autoencoder_ward_reconstruction.csv")
print("data/processed/autoencoder_feature_reconstruction.csv")
print("data/processed/urban_ward_embeddings_validated.csv")

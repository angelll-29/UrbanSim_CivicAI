import numpy as np
import pandas as pd
from pathlib import Path

from sklearn.preprocessing import StandardScaler

import tensorflow as tf
from tensorflow.keras import Model, Input
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras.regularizers import l2
from tensorflow.keras.callbacks import EarlyStopping

INPUT = Path("data/processed/urban_ai_features.csv")
MODEL_DIR = Path("ml/models")
OUTPUT = Path("data/processed/urban_ward_embeddings.csv")

MODEL_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------
# Reproducibility
# --------------------------------------------------
np.random.seed(42)
tf.random.set_seed(42)

# --------------------------------------------------
# Load data
# --------------------------------------------------
df = pd.read_csv(INPUT)

ward_codes = df["ward_code"].copy()
X = df.drop(columns=["ward_code"]).astype(float)

print("UrbanSim Autoencoder")
print("-" * 50)
print("Samples:", X.shape[0])
print("Input features:", X.shape[1])

# --------------------------------------------------
# Scale features
# --------------------------------------------------
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Save scaler
import joblib
joblib.dump(
    scaler,
    MODEL_DIR / "urban_autoencoder_scaler.joblib"
)

# --------------------------------------------------
# Autoencoder architecture
# --------------------------------------------------
input_dim = X_scaled.shape[1]

inputs = Input(shape=(input_dim,), name="urban_features")

x = Dense(
    16,
    activation="relu",
    kernel_regularizer=l2(1e-4),
    name="encoder_dense_16"
)(inputs)

x = Dropout(0.10, name="encoder_dropout")(x)

x = Dense(
    8,
    activation="relu",
    kernel_regularizer=l2(1e-4),
    name="encoder_dense_8"
)(x)

latent = Dense(
    4,
    activation="linear",
    name="urban_embedding"
)(x)

x = Dense(
    8,
    activation="relu",
    kernel_regularizer=l2(1e-4),
    name="decoder_dense_8"
)(latent)

x = Dense(
    16,
    activation="relu",
    kernel_regularizer=l2(1e-4),
    name="decoder_dense_16"
)(x)

outputs = Dense(
    input_dim,
    activation="linear",
    name="reconstruction"
)(x)

autoencoder = Model(inputs, outputs, name="UrbanSim_Autoencoder")

encoder = Model(
    inputs,
    latent,
    name="UrbanSim_Ward_Encoder"
)

# --------------------------------------------------
# Compile
# --------------------------------------------------
autoencoder.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
    loss="mse"
)

print("\nArchitecture:")
autoencoder.summary()

# --------------------------------------------------
# Train
# --------------------------------------------------
early_stopping = EarlyStopping(
    monitor="loss",
    patience=40,
    restore_best_weights=True,
    min_delta=1e-5
)

history = autoencoder.fit(
    X_scaled,
    X_scaled,
    epochs=500,
    batch_size=8,
    shuffle=True,
    verbose=1,
    callbacks=[early_stopping]
)

# --------------------------------------------------
# Reconstruction
# --------------------------------------------------
X_reconstructed = autoencoder.predict(
    X_scaled,
    verbose=0
)

reconstruction_mse = np.mean(
    np.square(X_scaled - X_reconstructed),
    axis=1
)

# --------------------------------------------------
# Generate embeddings
# --------------------------------------------------
embeddings = encoder.predict(
    X_scaled,
    verbose=0
)

embedding_df = pd.DataFrame(
    embeddings,
    columns=[
        "embedding_1",
        "embedding_2",
        "embedding_3",
        "embedding_4"
    ]
)

embedding_df.insert(0, "ward_code", ward_codes.values)
embedding_df["reconstruction_mse"] = reconstruction_mse

embedding_df.to_csv(
    OUTPUT,
    index=False
)

# --------------------------------------------------
# Save model
# --------------------------------------------------
autoencoder.save(
    MODEL_DIR / "urban_autoencoder.keras"
)

encoder.save(
    MODEL_DIR / "urban_ward_encoder.keras"
)

# --------------------------------------------------
# Report
# --------------------------------------------------
print("\n" + "=" * 50)
print("AUTOENCODER TRAINING COMPLETE")
print("=" * 50)

print("Epochs trained:", len(history.history["loss"]))
print("Final loss:", history.history["loss"][-1])
print("Best loss:", min(history.history["loss"]))

print("\nEmbedding shape:", embeddings.shape)

print("\nWard embeddings:")
print(embedding_df.to_string(index=False))

print("\nReconstruction MSE:")
print(
    embedding_df[
        ["ward_code", "reconstruction_mse"]
    ].sort_values(
        "reconstruction_mse",
        ascending=False
    ).to_string(index=False)
)

print("\nSaved:")
print(OUTPUT)
print(MODEL_DIR / "urban_autoencoder.keras")
print(MODEL_DIR / "urban_ward_encoder.keras")
print(MODEL_DIR / "urban_autoencoder_scaler.joblib")

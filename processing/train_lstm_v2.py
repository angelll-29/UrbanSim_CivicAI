import numpy as np
import tensorflow as tf
import pandas as pd
from pathlib import Path
from tensorflow.keras import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from tensorflow.keras.optimizers import Adam

BASE = Path("data/processed/lstm_v2")
MODEL_DIR = Path("ml/models")
MODEL_DIR.mkdir(parents=True, exist_ok=True)

SEED = 42
np.random.seed(SEED)
tf.random.set_seed(SEED)

train = np.load(BASE / "train_prepared.npz")
val = np.load(BASE / "validation_prepared.npz")

X_train = train["X"]
y_train = train["y"]

X_val = val["X"]
y_val = val["y"]

print("=" * 70)
print("LSTM-V2 TRAINING")
print("=" * 70)

print("Training:", X_train.shape, y_train.shape)
print("Validation:", X_val.shape, y_val.shape)

model = Sequential([
    LSTM(
        64,
        input_shape=(
            X_train.shape[1],
            X_train.shape[2]
        )
    ),
    Dropout(0.20),
    Dense(32, activation="relu"),
    Dense(7, activation="linear")
])

model.compile(
    optimizer=Adam(learning_rate=0.001),
    loss="mse",
    metrics=["mae"]
)

model.summary()

checkpoint_path = (
    MODEL_DIR /
    "multivariate_pm25_lstm_v2_60to7.keras"
)

early_stopping = EarlyStopping(
    monitor="val_loss",
    patience=20,
    min_delta=1e-4,
    restore_best_weights=True,
    verbose=1
)

checkpoint = ModelCheckpoint(
    checkpoint_path,
    monitor="val_loss",
    save_best_only=True,
    verbose=1
)

history = model.fit(
    X_train,
    y_train,
    validation_data=(X_val, y_val),
    epochs=100,
    batch_size=32,
    shuffle=False,
    callbacks=[
        early_stopping,
        checkpoint
    ],
    verbose=1
)

history_df = pd.DataFrame(
    history.history
)

history_df.insert(
    0,
    "epoch",
    range(1, len(history_df) + 1)
)

history_df.to_csv(
    BASE / "lstm_v2_training_history.csv",
    index=False
)

print("\n" + "=" * 70)
print("LSTM-V2 TRAINING COMPLETE")
print("=" * 70)

print(
    "Epochs trained:",
    len(history.history["loss"])
)

print(
    "Best validation loss:",
    min(history.history["val_loss"])
)

print(
    "Best validation MAE:",
    min(history.history["val_mae"])
)

print("\nModel saved:")
print(checkpoint_path)

print("\nHistory saved:")
print(
    BASE / "lstm_v2_training_history.csv"
)

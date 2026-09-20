import numpy as np
import pandas as pd
from pathlib import Path
import tensorflow as tf
from tensorflow.keras import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib

BASE = Path("data/processed/lstm")
MODEL_DIR = Path("ml/models")

MODEL_DIR.mkdir(
    parents=True,
    exist_ok=True
)

# ------------------------------------------------------------
# Reproducibility
# ------------------------------------------------------------

np.random.seed(42)
tf.random.set_seed(42)

# ------------------------------------------------------------
# Load prepared data
# ------------------------------------------------------------

train = np.load(BASE / "train_prepared.npz")
val = np.load(BASE / "validation_prepared.npz")
test = np.load(BASE / "test_prepared.npz")

X_train = train["X"]
y_train = train["y"]

X_val = val["X"]
y_val = val["y"]

X_test = test["X"]
y_test = test["y"]

print("=" * 70)
print("URBANSIM LSTM — PM2.5 FORECASTING")
print("=" * 70)

print("Train:", X_train.shape, y_train.shape)
print("Validation:", X_val.shape, y_val.shape)
print("Test:", X_test.shape, y_test.shape)

# ------------------------------------------------------------
# Model
# ------------------------------------------------------------

model = Sequential([

    LSTM(
        64,
        input_shape=(
            X_train.shape[1],
            X_train.shape[2]
        )
    ),

    Dropout(0.20),

    Dense(
        32,
        activation="relu"
    ),

    Dense(
        7,
        activation="linear"
    )
])

model.compile(
    optimizer=tf.keras.optimizers.Adam(
        learning_rate=0.001
    ),
    loss="mse",
    metrics=["mae"]
)

model.summary()

# ------------------------------------------------------------
# Callbacks
# ------------------------------------------------------------

model_path = (
    MODEL_DIR /
    "pm25_lstm_60to7.keras"
)

callbacks = [

    EarlyStopping(
        monitor="val_loss",
        patience=20,
        restore_best_weights=True,
        verbose=1
    ),

    ModelCheckpoint(
        model_path,
        monitor="val_loss",
        save_best_only=True,
        verbose=1
    )
]

# ------------------------------------------------------------
# Train
# ------------------------------------------------------------

history = model.fit(

    X_train,
    y_train,

    validation_data=(
        X_val,
        y_val
    ),

    epochs=100,

    batch_size=32,

    callbacks=callbacks,

    verbose=1,

    shuffle=False
)

# ------------------------------------------------------------
# Load best model
# ------------------------------------------------------------

model = tf.keras.models.load_model(
    model_path
)

# ------------------------------------------------------------
# Predictions
# ------------------------------------------------------------

pred_scaled = model.predict(
    X_test,
    verbose=0
)

# ------------------------------------------------------------
# Inverse scaling
# ------------------------------------------------------------

scaler = joblib.load(
    BASE / "pm25_lstm_scaler.joblib"
)

y_test_actual = scaler.inverse_transform(
    y_test.reshape(-1, 1)
).reshape(
    y_test.shape
)

pred_actual = scaler.inverse_transform(
    pred_scaled.reshape(-1, 1)
).reshape(
    pred_scaled.shape
)

# ------------------------------------------------------------
# Overall metrics
# ------------------------------------------------------------

y_true_flat = y_test_actual.flatten()
y_pred_flat = pred_actual.flatten()

mae = mean_absolute_error(
    y_true_flat,
    y_pred_flat
)

rmse = np.sqrt(
    mean_squared_error(
        y_true_flat,
        y_pred_flat
    )
)

r2 = r2_score(
    y_true_flat,
    y_pred_flat
)

print("\n" + "=" * 70)
print("LSTM TEST PERFORMANCE")
print("=" * 70)

print("MAE :", round(mae, 4))
print("RMSE:", round(rmse, 4))
print("R²  :", round(r2, 4))

# ------------------------------------------------------------
# Horizon-wise metrics
# ------------------------------------------------------------

print("\nHorizon-wise performance:")

horizon_rows = []

for h in range(7):

    true_h = y_test_actual[:, h]
    pred_h = pred_actual[:, h]

    h_mae = mean_absolute_error(
        true_h,
        pred_h
    )

    h_rmse = np.sqrt(
        mean_squared_error(
            true_h,
            pred_h
        )
    )

    h_r2 = r2_score(
        true_h,
        pred_h
    )

    horizon_rows.append({

        "forecast_day":
            h + 1,

        "mae":
            h_mae,

        "rmse":
            h_rmse,

        "r2":
            h_r2
    })

    print(
        f"Day {h+1}: "
        f"MAE={h_mae:.4f}, "
        f"RMSE={h_rmse:.4f}, "
        f"R2={h_r2:.4f}"
    )

horizon_df = pd.DataFrame(
    horizon_rows
)

horizon_df.to_csv(
    BASE / "lstm_horizon_metrics.csv",
    index=False
)

# ------------------------------------------------------------
# Persistence baseline
# ------------------------------------------------------------

# Baseline:
# Predict every future day using the final
# observed value in the 60-day input window.

last_observed_scaled = (
    X_test[:, -1, 0]
)

baseline_scaled = np.repeat(
    last_observed_scaled[:, np.newaxis],
    7,
    axis=1
)

baseline_actual = scaler.inverse_transform(
    baseline_scaled.reshape(-1, 1)
).reshape(
    baseline_scaled.shape
)

baseline_true = y_test_actual.flatten()
baseline_pred = baseline_actual.flatten()

baseline_mae = mean_absolute_error(
    baseline_true,
    baseline_pred
)

baseline_rmse = np.sqrt(
    mean_squared_error(
        baseline_true,
        baseline_pred
    )
)

baseline_r2 = r2_score(
    baseline_true,
    baseline_pred
)

print("\n" + "=" * 70)
print("PERSISTENCE BASELINE")
print("=" * 70)

print(
    "MAE :",
    round(baseline_mae, 4)
)

print(
    "RMSE:",
    round(baseline_rmse, 4)
)

print(
    "R²  :",
    round(baseline_r2, 4)
)

# ------------------------------------------------------------
# Improvement
# ------------------------------------------------------------

mae_improvement = (
    (baseline_mae - mae)
    / baseline_mae
    * 100
)

rmse_improvement = (
    (baseline_rmse - rmse)
    / baseline_rmse
    * 100
)

print("\n" + "=" * 70)
print("LSTM vs BASELINE")
print("=" * 70)

print(
    "MAE improvement:",
    round(mae_improvement, 2),
    "%"
)

print(
    "RMSE improvement:",
    round(rmse_improvement, 2),
    "%"
)

# ------------------------------------------------------------
# Save predictions
# ------------------------------------------------------------

pred_rows = []

for i in range(
    len(y_test_actual)
):

    for h in range(7):

        pred_rows.append({

            "sequence":
                i,

            "forecast_day":
                h + 1,

            "actual_pm25":
                y_test_actual[i, h],

            "predicted_pm25":
                pred_actual[i, h],

            "baseline_pm25":
                baseline_actual[i, h]
        })

predictions = pd.DataFrame(
    pred_rows
)

predictions.to_csv(
    BASE / "lstm_test_predictions.csv",
    index=False
)

# ------------------------------------------------------------
# Save training history
# ------------------------------------------------------------

history_df = pd.DataFrame(
    history.history
)

history_df.to_csv(
    BASE / "lstm_training_history.csv",
    index=False
)

print("\nSaved:")
print(model_path)
print(BASE / "lstm_horizon_metrics.csv")
print(BASE / "lstm_test_predictions.csv")
print(BASE / "lstm_training_history.csv")

print("\nLSTM experiment complete.")

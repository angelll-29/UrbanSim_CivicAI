import numpy as np
import pandas as pd
import joblib
import tensorflow as tf
from pathlib import Path
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score
)

BASE = Path(
    "data/processed/multivariate_lstm"
)

MODEL_PATH = Path(
    "ml/models/multivariate_pm25_lstm_60to7.keras"
)

SCALER_PATH = (
    BASE /
    "multivariate_pm25_target_scaler.joblib"
)

META_PATH = (
    BASE /
    "test_metadata.csv"
)

TEST_PATH = (
    BASE /
    "test_prepared.npz"
)

OUTPUT_HORIZON = (
    BASE /
    "multivariate_lstm_error_by_horizon.csv"
)

OUTPUT_WARD = (
    BASE /
    "multivariate_lstm_error_by_ward.csv"
)

# ------------------------------------------------------------
# Load
# ------------------------------------------------------------

data = np.load(
    TEST_PATH
)

X_test = data["X"]
y_test_scaled = data["y"]

target_scaler = joblib.load(
    SCALER_PATH
)

metadata = pd.read_csv(
    META_PATH
)

# ------------------------------------------------------------
# Load best model
# ------------------------------------------------------------

model = tf.keras.models.load_model(
    MODEL_PATH
)

# ------------------------------------------------------------
# Prediction
# ------------------------------------------------------------

pred_scaled = model.predict(
    X_test,
    verbose=0
)

# ------------------------------------------------------------
# Inverse transform
# ------------------------------------------------------------

y_test = target_scaler.inverse_transform(
    y_test_scaled.reshape(-1, 1)
).reshape(y_test_scaled.shape)

pred = target_scaler.inverse_transform(
    pred_scaled.reshape(-1, 1)
).reshape(pred_scaled.shape
)

# ------------------------------------------------------------
# Persistence baseline
#
# Last observed PM2.5 value in the 60-day input
# is repeated for all seven forecast days.
# ------------------------------------------------------------

last_pm25_scaled = X_test[:, -1, 0]

last_pm25 = target_scaler.inverse_transform(
    last_pm25_scaled.reshape(-1, 1)
).ravel()

persistence = np.repeat(
    last_pm25[:, None],
    7,
    axis=1
)

# ------------------------------------------------------------
# Overall metrics
# ------------------------------------------------------------

actual_flat = y_test.ravel()
pred_flat = pred.ravel()
persist_flat = persistence.ravel()

lstm_mae = mean_absolute_error(
    actual_flat,
    pred_flat
)

lstm_rmse = np.sqrt(
    mean_squared_error(
        actual_flat,
        pred_flat
    )
)

lstm_r2 = r2_score(
    actual_flat,
    pred_flat
)

base_mae = mean_absolute_error(
    actual_flat,
    persist_flat
)

base_rmse = np.sqrt(
    mean_squared_error(
        actual_flat,
        persist_flat
    )
)

base_r2 = r2_score(
    actual_flat,
    persist_flat
)

# ------------------------------------------------------------
# Horizon metrics
# ------------------------------------------------------------

horizon_rows = []

for h in range(7):

    actual = y_test[:, h]
    forecast = pred[:, h]
    baseline = persistence[:, h]

    horizon_rows.append({

        "horizon_day":
            h + 1,

        "lstm_mae":
            mean_absolute_error(
                actual,
                forecast
            ),

        "lstm_rmse":
            np.sqrt(
                mean_squared_error(
                    actual,
                    forecast
                )
            ),

        "lstm_r2":
            r2_score(
                actual,
                forecast
            ),

        "persistence_mae":
            mean_absolute_error(
                actual,
                baseline
            ),

        "persistence_rmse":
            np.sqrt(
                mean_squared_error(
                    actual,
                    baseline
                )
            ),

        "persistence_r2":
            r2_score(
                actual,
                baseline
            )
    })

horizon_df = pd.DataFrame(
    horizon_rows
)

horizon_df[
    "mae_improvement_pct"
] = (
    1 -
    horizon_df["lstm_mae"] /
    horizon_df["persistence_mae"]
) * 100

horizon_df[
    "rmse_improvement_pct"
] = (
    1 -
    horizon_df["lstm_rmse"] /
    horizon_df["persistence_rmse"]
) * 100

horizon_df.to_csv(
    OUTPUT_HORIZON,
    index=False
)

# ------------------------------------------------------------
# Ward metrics
# ------------------------------------------------------------

ward_rows = []

metadata = metadata.reset_index(
    drop=True
)

for ward, indices in metadata.groupby(
    "urban_ward_code"
).groups.items():

    indices = np.asarray(
        list(indices)
    )

    actual = y_test[
        indices
    ].ravel()

    forecast = pred[
        indices
    ].ravel()

    baseline = persistence[
        indices
    ].ravel()

    ward_rows.append({

        "urban_ward_code":
            ward,

        "samples":
            len(indices),

        "lstm_mae":
            mean_absolute_error(
                actual,
                forecast
            ),

        "lstm_rmse":
            np.sqrt(
                mean_squared_error(
                    actual,
                    forecast
                )
            ),

        "lstm_r2":
            r2_score(
                actual,
                forecast
            ),

        "persistence_mae":
            mean_absolute_error(
                actual,
                baseline
            ),

        "mae_improvement_pct":
            (
                1 -
                mean_absolute_error(
                    actual,
                    forecast
                ) /
                mean_absolute_error(
                    actual,
                    baseline
                )
            ) * 100
    })

ward_df = pd.DataFrame(
    ward_rows
)

ward_df = ward_df.sort_values(
    "lstm_mae"
)

ward_df.to_csv(
    OUTPUT_WARD,
    index=False
)

# ------------------------------------------------------------
# Bias
# ------------------------------------------------------------

error = pred - y_test

mean_error = error.mean()
median_error = np.median(error)
mean_abs_error = np.abs(error).mean()

# ------------------------------------------------------------
# Report
# ------------------------------------------------------------

print("=" * 70)
print("MULTIVARIATE LSTM TEST EVALUATION")
print("=" * 70)

print(
    "\nTest samples:",
    len(X_test)
)

print(
    "Forecast horizon:",
    "7 days"
)

print("\nOverall LSTM:")
print(
    f"MAE  : {lstm_mae:.4f} µg/m³"
)

print(
    f"RMSE : {lstm_rmse:.4f} µg/m³"
)

print(
    f"R²   : {lstm_r2:.4f}"
)

print("\nPersistence baseline:")
print(
    f"MAE  : {base_mae:.4f} µg/m³"
)

print(
    f"RMSE : {base_rmse:.4f} µg/m³"
)

print(
    f"R²   : {base_r2:.4f}"
)

print("\nLSTM vs persistence:")

print(
    f"MAE improvement : "
    f"{(1 - lstm_mae/base_mae)*100:.2f}%"
)

print(
    f"RMSE improvement: "
    f"{(1 - lstm_rmse/base_rmse)*100:.2f}%"
)

print("\nMean error:")
print(
    f"{mean_error.mean():.4f} µg/m³"
)

print(
    "Median error:",
    f"{np.median(error):.4f} µg/m³"
)

print(
    "Mean absolute error:",
    f"{mean_abs_error:.4f} µg/m³"
)

print("\nHorizon performance:")

print(
    horizon_df.to_string(
        index=False
    )
)

print("\nWard performance:")

print(
    ward_df.to_string(
        index=False
    )
)

print("\nSaved:")
print(
    OUTPUT_HORIZON
)

print(
    OUTPUT_WARD
)

import numpy as np
import pandas as pd
from pathlib import Path
from tensorflow.keras.models import load_model
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

BASE = Path(__file__).resolve().parents[1]

DATA_DIR = BASE / "data" / "processed" / "lstm_v2"
MODEL_PATH = BASE / "ml" / "models" / "multivariate_pm25_lstm_v2_60to7.keras"

TEST_X = DATA_DIR / "test_prepared.npz"
TEST_META = DATA_DIR / "test_metadata.csv"

OUTPUT = BASE / "data" / "processed" / "lstm_v2_test_evaluation.csv"

print("=" * 70)
print("LSTM-V2 TEST EVALUATION")
print("=" * 70)

# ---------------------------------------------------------
# Load test data
# ---------------------------------------------------------
test = np.load(TEST_X)

X_test = test["X"]
y_test_scaled = test["y"]

print(f"Test X shape: {X_test.shape}")
print(f"Test y shape: {y_test_scaled.shape}")

# ---------------------------------------------------------
# Load target scaler
# ---------------------------------------------------------
import joblib

target_scaler_path = DATA_DIR / "lstm_v2_pm25_target_scaler.joblib"
target_scaler = joblib.load(target_scaler_path)

# Convert scaled target back to µg/m³
y_test = target_scaler.inverse_transform(
    y_test_scaled.reshape(-1, 1)
).reshape(y_test_scaled.shape)

# ---------------------------------------------------------
# Load model
# ---------------------------------------------------------
model = load_model(MODEL_PATH)

print("Model loaded successfully.")

# ---------------------------------------------------------
# Prediction
# ---------------------------------------------------------
pred_scaled = model.predict(X_test, verbose=0)

y_pred = target_scaler.inverse_transform(
    pred_scaled.reshape(-1, 1)
).reshape(pred_scaled.shape)

# ---------------------------------------------------------
# Persistence baseline
# Last observed PM2.5 value in input window
# ---------------------------------------------------------
pm25_scaled = X_test[:, :, 0]

last_pm25_scaled = pm25_scaled[:, -1]

last_pm25 = target_scaler.inverse_transform(
    last_pm25_scaled.reshape(-1, 1)
).ravel()

y_persistence = np.repeat(
    last_pm25[:, None],
    y_test.shape[1],
    axis=1
)

# ---------------------------------------------------------
# Overall metrics
# ---------------------------------------------------------
def metrics(y_true, y_pred):
    return {
        "MAE": mean_absolute_error(
            y_true.ravel(),
            y_pred.ravel()
        ),
        "RMSE": np.sqrt(
            mean_squared_error(
                y_true.ravel(),
                y_pred.ravel()
            )
        ),
        "R2": r2_score(
            y_true.ravel(),
            y_pred.ravel()
        )
    }

lstm_metrics = metrics(y_test, y_pred)
persistence_metrics = metrics(y_test, y_persistence)

mae_improvement = (
    (persistence_metrics["MAE"] - lstm_metrics["MAE"])
    / persistence_metrics["MAE"]
) * 100

rmse_improvement = (
    (persistence_metrics["RMSE"] - lstm_metrics["RMSE"])
    / persistence_metrics["RMSE"]
) * 100

print("\n" + "=" * 70)
print("OVERALL TEST PERFORMANCE")
print("=" * 70)

print(
    f"LSTM-V2       MAE : {lstm_metrics['MAE']:.4f} µg/m³"
)
print(
    f"Persistence   MAE : {persistence_metrics['MAE']:.4f} µg/m³"
)

print(
    f"LSTM-V2       RMSE: {lstm_metrics['RMSE']:.4f} µg/m³"
)
print(
    f"Persistence   RMSE: {persistence_metrics['RMSE']:.4f} µg/m³"
)

print(
    f"LSTM-V2       R²  : {lstm_metrics['R2']:.4f}"
)
print(
    f"Persistence   R²  : {persistence_metrics['R2']:.4f}"
)

print(
    f"\nMAE improvement vs persistence : {mae_improvement:.2f}%"
)
print(
    f"RMSE improvement vs persistence: {rmse_improvement:.2f}%"
)

# ---------------------------------------------------------
# Horizon-wise evaluation
# ---------------------------------------------------------
print("\n" + "=" * 70)
print("HORIZON-WISE PERFORMANCE")
print("=" * 70)

rows = []

for h in range(7):

    true_h = y_test[:, h]
    pred_h = y_pred[:, h]
    pers_h = y_persistence[:, h]

    lstm_mae = mean_absolute_error(true_h, pred_h)
    lstm_rmse = np.sqrt(mean_squared_error(true_h, pred_h))
    lstm_r2 = r2_score(true_h, pred_h)

    pers_mae = mean_absolute_error(true_h, pers_h)
    pers_rmse = np.sqrt(mean_squared_error(true_h, pers_h))
    pers_r2 = r2_score(true_h, pers_h)

    mae_imp = ((pers_mae - lstm_mae) / pers_mae) * 100
    rmse_imp = ((pers_rmse - lstm_rmse) / pers_rmse) * 100

    rows.append({
        "horizon_day": h + 1,
        "lstm_mae": lstm_mae,
        "lstm_rmse": lstm_rmse,
        "lstm_r2": lstm_r2,
        "persistence_mae": pers_mae,
        "persistence_rmse": pers_rmse,
        "persistence_r2": pers_r2,
        "mae_improvement_pct": mae_imp,
        "rmse_improvement_pct": rmse_imp
    })

    print(
        f"Day {h+1}: "
        f"LSTM MAE={lstm_mae:.4f}, "
        f"Persistence MAE={pers_mae:.4f}, "
        f"Improvement={mae_imp:.2f}%"
    )

horizon_df = pd.DataFrame(rows)

# ---------------------------------------------------------
# Ward-level evaluation
# ---------------------------------------------------------
print("\n" + "=" * 70)
print("WARD-LEVEL PERFORMANCE")
print("=" * 70)

if TEST_META.exists():

    meta = pd.read_csv(TEST_META)

    # Make sure metadata length matches test samples
    if len(meta) == len(y_test):

        ward_rows = []

        for ward, idx in meta.groupby("urban_ward_code").groups.items():

            idx = np.asarray(list(idx))

            true_w = y_test[idx]
            pred_w = y_pred[idx]
            pers_w = y_persistence[idx]

            lstm_mae = mean_absolute_error(
                true_w.ravel(),
                pred_w.ravel()
            )

            pers_mae = mean_absolute_error(
                true_w.ravel(),
                pers_w.ravel()
            )

            improvement = (
                (pers_mae - lstm_mae)
                / pers_mae
            ) * 100

            ward_rows.append({
                "ward_code": ward,
                "samples": len(idx),
                "lstm_mae": lstm_mae,
                "persistence_mae": pers_mae,
                "mae_improvement_pct": improvement
            })

            print(
                f"{ward}: "
                f"samples={len(idx)}, "
                f"LSTM MAE={lstm_mae:.4f}, "
                f"Persistence MAE={pers_mae:.4f}, "
                f"Improvement={improvement:.2f}%"
            )

        ward_df = pd.DataFrame(ward_rows)

    else:
        print(
            "\nWARNING: Metadata length does not match test samples."
        )
        ward_df = pd.DataFrame()

else:
    print("\nWARNING: Test metadata file not found.")
    ward_df = pd.DataFrame()

# ---------------------------------------------------------
# Save horizon results
# ---------------------------------------------------------
horizon_output = DATA_DIR / "lstm_v2_horizon_evaluation.csv"
horizon_df.to_csv(horizon_output, index=False)

if not ward_df.empty:
    ward_output = DATA_DIR / "lstm_v2_ward_evaluation.csv"
    ward_df.to_csv(ward_output, index=False)

# ---------------------------------------------------------
# Save summary
# ---------------------------------------------------------
summary = pd.DataFrame([{
    "model": "LSTM-V2",
    "test_samples": len(y_test),
    "overall_mae": lstm_metrics["MAE"],
    "overall_rmse": lstm_metrics["RMSE"],
    "overall_r2": lstm_metrics["R2"],
    "persistence_mae": persistence_metrics["MAE"],
    "persistence_rmse": persistence_metrics["RMSE"],
    "persistence_r2": persistence_metrics["R2"],
    "mae_improvement_pct": mae_improvement,
    "rmse_improvement_pct": rmse_improvement
}])

summary.to_csv(OUTPUT, index=False)

print("\n" + "=" * 70)
print("EVALUATION COMPLETE")
print("=" * 70)

print(f"Summary : {OUTPUT}")
print(f"Horizon : {horizon_output}")

if not ward_df.empty:
    print(f"Ward    : {DATA_DIR / 'lstm_v2_ward_evaluation.csv'}")


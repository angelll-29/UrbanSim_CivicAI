import numpy as np
import pandas as pd
import torch
import joblib
from pathlib import Path
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from stgnn_model import STGNN

ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = ROOT / "data" / "processed" / "stgnn_residual"
MODEL_DIR = ROOT / "ml" / "models"

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

WARDS = [
    "E", "FN", "FS", "GS", "HE", "KE",
    "L", "ME", "N", "PN", "RC"
]

NUM_NODES = 11
INPUT_FEATURES = 9
FORECAST_DAYS = 7

# =========================================================
# LOAD TEST DATA
# =========================================================

test = np.load(
    DATA_DIR / "test_prepared.npz"
)

X_test = torch.tensor(
    test["X"],
    dtype=torch.float32
).to(DEVICE)

residual_actual_scaled = test["Y"].astype(
    np.float32
)

baseline_scaled = test["baseline"].astype(
    np.float32
)

print("========================================")
print("RESIDUAL ST-GNN TEST EVALUATION")
print("========================================")

print("\nRaw shapes:")
print("X test:", X_test.shape)
print("Residual target:", residual_actual_scaled.shape)
print("Baseline:", baseline_scaled.shape)

# =========================================================
# LOAD SCALER
# =========================================================

scaler = joblib.load(
    MODEL_DIR / "stgnn_scaler.joblib"
)

target_mean = float(
    scaler["target_mean"]
)

target_std = float(
    scaler["target_std"]
)

# =========================================================
# BUILD GRAPH
# =========================================================

edges = pd.read_csv(
    ROOT /
    "data" /
    "processed" /
    "stgnn_ward_edges.csv"
)

ward_to_idx = {
    ward: i
    for i, ward in enumerate(WARDS)
}

adjacency = torch.zeros(
    (NUM_NODES, NUM_NODES),
    dtype=torch.float32
)

for _, row in edges.iterrows():

    source = row["source"]
    target = row["target"]

    if (
        source in ward_to_idx
        and target in ward_to_idx
    ):

        i = ward_to_idx[source]
        j = ward_to_idx[target]

        adjacency[i, j] = 1.0

adjacency = adjacency.to(DEVICE)

# =========================================================
# LOAD MODEL
# =========================================================

checkpoint = torch.load(
    MODEL_DIR /
    "urban_stgnn_pm25_residual_60to7.pt",
    map_location=DEVICE,
    weights_only=False
)

model = STGNN(
    num_nodes=NUM_NODES,
    input_features=INPUT_FEATURES,
    spatial_hidden=32,
    temporal_hidden=32,
    forecast_days=FORECAST_DAYS
).to(DEVICE)

model.load_state_dict(
    checkpoint["model_state_dict"]
)

model.eval()

# =========================================================
# PREDICT RESIDUAL
# =========================================================

with torch.no_grad():

    predicted_residual_scaled = (
        model(
            X_test,
            adjacency
        )
        .cpu()
        .numpy()
    )

print("\nPrediction shape:")
print(
    "Predicted residual:",
    predicted_residual_scaled.shape
)

# =========================================================
# CONVERT TO ORIGINAL PM2.5 UNITS
#
# residual_scaled =
# residual / target_std
#
# residual =
# residual_scaled * target_std
#
# baseline PM2.5 =
# baseline_scaled * target_std + target_mean
# =========================================================

baseline_pm25 = (
    baseline_scaled *
    target_std
    +
    target_mean
)

actual_residual = (
    residual_actual_scaled *
    target_std
)

predicted_residual = (
    predicted_residual_scaled *
    target_std
)

# IMPORTANT:
# baseline_pm25 shape is:
# (samples, nodes)
#
# Convert to:
# (samples, 1, nodes)
#
# before broadcasting across 7 days.

baseline_pm25_7 = (
    np.repeat(baseline_pm25, 7, axis=1)
)

actual_pm25 = (
    baseline_pm25_7
    +
    actual_residual
)

predicted_pm25 = (
    baseline_pm25_7
    +
    predicted_residual
)

persistence_pm25 = np.repeat(
    baseline_pm25_7,
    FORECAST_DAYS,
    axis=1
)

print("\nFinal shapes:")
print("Actual PM2.5:", actual_pm25.shape)
print("Predicted PM2.5:", predicted_pm25.shape)
print("Persistence:", persistence_pm25.shape)

# =========================================================
# OVERALL METRICS
# =========================================================

y_true = actual_pm25.reshape(-1)
y_pred = predicted_pm25.reshape(-1)
y_persist = persistence_pm25.reshape(-1)

print("\nFlattened shapes:")
print("Actual:", y_true.shape)
print("Prediction:", y_pred.shape)
print("Persistence:", y_persist.shape)

mae = mean_absolute_error(
    y_true,
    y_pred
)

rmse = np.sqrt(
    mean_squared_error(
        y_true,
        y_pred
    )
)

r2 = r2_score(
    y_true,
    y_pred
)

p_mae = mean_absolute_error(
    y_true,
    y_persist
)

p_rmse = np.sqrt(
    mean_squared_error(
        y_true,
        y_persist
    )
)

p_r2 = r2_score(
    y_true,
    y_persist
)

bias = (
    predicted_pm25 -
    actual_pm25
).mean()

print("\n========================================")
print("OVERALL RESULTS")
print("========================================")

print(
    f"\nResidual ST-GNN"
    f"\nMAE : {mae:.4f} µg/m³"
    f"\nRMSE: {rmse:.4f} µg/m³"
    f"\nR²  : {r2:.4f}"
    f"\nBias: {bias:+.4f} µg/m³"
)

print(
    f"\nPersistence"
    f"\nMAE : {p_mae:.4f} µg/m³"
    f"\nRMSE: {p_rmse:.4f} µg/m³"
    f"\nR²  : {p_r2:.4f}"
)

print(
    f"\nResidual ST-GNN vs persistence:"
    f"\nMAE improvement : "
    f"{(p_mae - mae) / p_mae * 100:+.2f}%"
    f"\nRMSE improvement: "
    f"{(p_rmse - rmse) / p_rmse * 100:+.2f}%"
)

# =========================================================
# HORIZON METRICS
# =========================================================

horizon_rows = []

for h in range(FORECAST_DAYS):

    true_h = actual_pm25[:, h, :].reshape(-1)
    pred_h = predicted_pm25[:, h, :].reshape(-1)
    pers_h = persistence_pm25[:, h, :].reshape(-1)

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

    hp_mae = mean_absolute_error(
        true_h,
        pers_h
    )

    horizon_rows.append({
        "forecast_day": h + 1,
        "mae": h_mae,
        "rmse": h_rmse,
        "r2": h_r2,
        "persistence_mae": hp_mae,
        "mae_improvement_pct": (
            (hp_mae - h_mae)
            / hp_mae
            * 100
        )
    })

horizon_df = pd.DataFrame(
    horizon_rows
)

print("\n========================================")
print("HORIZON RESULTS")
print("========================================")

print(
    horizon_df.to_string(
        index=False,
        float_format=lambda x: f"{x:.4f}"
    )
)

horizon_df.to_csv(
    DATA_DIR /
    "residual_stgnn_horizon_metrics.csv",
    index=False
)

# =========================================================
# WARD METRICS
# =========================================================

ward_rows = []

for i, ward in enumerate(WARDS):

    true_w = actual_pm25[:, :, i].reshape(-1)
    pred_w = predicted_pm25[:, :, i].reshape(-1)
    pers_w = persistence_pm25[:, :, i].reshape(-1)

    w_mae = mean_absolute_error(
        true_w,
        pred_w
    )

    w_rmse = np.sqrt(
        mean_squared_error(
            true_w,
            pred_w
        )
    )

    wp_mae = mean_absolute_error(
        true_w,
        pers_w
    )

    ward_rows.append({
        "ward_code": ward,
        "mae": w_mae,
        "rmse": w_rmse,
        "persistence_mae": wp_mae,
        "mae_improvement_pct": (
            (wp_mae - w_mae)
            / wp_mae
            * 100
        )
    })

ward_df = pd.DataFrame(
    ward_rows
)

print("\n========================================")
print("WARD RESULTS")
print("========================================")

print(
    ward_df.to_string(
        index=False,
        float_format=lambda x: f"{x:.4f}"
    )
)

ward_df.to_csv(
    DATA_DIR /
    "residual_stgnn_ward_metrics.csv",
    index=False
)

# =========================================================
# SAVE PREDICTIONS
# =========================================================

rows = []

for s in range(
    predicted_pm25.shape[0]
):

    for h in range(
        FORECAST_DAYS
    ):

        for n, ward in enumerate(
            WARDS
        ):

            rows.append({
                "sample": s,
                "forecast_day": h + 1,
                "ward_code": ward,
                "actual_pm25": actual_pm25[
                    s, h, n
                ],
                "residual_stgnn_pm25": predicted_pm25[
                    s, h, n
                ],
                "persistence_pm25": persistence_pm25[
                    s, h, n
                ]
            })

prediction_df = pd.DataFrame(
    rows
)

prediction_df.to_csv(
    DATA_DIR /
    "residual_stgnn_test_predictions.csv",
    index=False
)

print("\nSaved:")
print(
    DATA_DIR /
    "residual_stgnn_horizon_metrics.csv"
)

print(
    DATA_DIR /
    "residual_stgnn_ward_metrics.csv"
)

print(
    DATA_DIR /
    "residual_stgnn_test_predictions.csv"
)

print("\nResidual evaluation complete.")

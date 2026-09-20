import numpy as np
import pandas as pd
import torch
from pathlib import Path
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from stgnn_model import STGNN

ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = ROOT / "data" / "processed" / "stgnn"
MODEL_DIR = ROOT / "ml" / "models"

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

WARDS = [
    "E", "FN", "FS", "GS", "HE", "KE",
    "L", "ME", "N", "PN", "RC"
]

NUM_NODES = 11
INPUT_FEATURES = 9
FORECAST_DAYS = 7

# =========================================================
# Load test data
# =========================================================

test = np.load(
    DATA_DIR / "test_prepared.npz"
)

X_test = torch.tensor(
    test["X"],
    dtype=torch.float32
).to(DEVICE)

Y_test_scaled = test["Y"].astype(
    np.float32
)

# =========================================================
# Load scaler
# =========================================================

import joblib

scaler = joblib.load(
    MODEL_DIR / "stgnn_scaler.joblib"
)

target_mean = scaler["target_mean"]
target_std = scaler["target_std"]

# =========================================================
# Build graph
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

    if source in ward_to_idx and target in ward_to_idx:

        i = ward_to_idx[source]
        j = ward_to_idx[target]

        adjacency[i, j] = 1.0

adjacency = adjacency.to(DEVICE)

# =========================================================
# Load best model
# =========================================================

checkpoint = torch.load(
    MODEL_DIR /
    "urban_stgnn_pm25_60to7.pt",
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
# Predict
# =========================================================

with torch.no_grad():

    predictions_scaled = model(
        X_test,
        adjacency
    ).cpu().numpy()

# =========================================================
# Inverse transform
# =========================================================

predictions = (
    predictions_scaled *
    target_std
    +
    target_mean
)

actual = (
    Y_test_scaled *
    target_std
    +
    target_mean
)

# =========================================================
# Persistence baseline
#
# Last observed PM2.5 value repeated for all
# seven forecast days.
# =========================================================

last_pm25_scaled = test["X"][
    :, -1, :, 0
]

persistence_scaled = np.repeat(
    last_pm25_scaled[:, None, :],
    FORECAST_DAYS,
    axis=1
)

persistence = (
    persistence_scaled *
    target_std
    +
    target_mean
)

# =========================================================
# Overall metrics
# =========================================================

y_true = actual.reshape(-1)
y_pred = predictions.reshape(-1)
y_persist = persistence.reshape(-1)

stgnn_mae = mean_absolute_error(
    y_true,
    y_pred
)

stgnn_rmse = np.sqrt(
    mean_squared_error(
        y_true,
        y_pred
    )
)

stgnn_r2 = r2_score(
    y_true,
    y_pred
)

persist_mae = mean_absolute_error(
    y_true,
    y_persist
)

persist_rmse = np.sqrt(
    mean_squared_error(
        y_true,
        y_persist
    )
)

persist_r2 = r2_score(
    y_true,
    y_persist
)

# =========================================================
# Print overall
# =========================================================

print("========================================")
print("ST-GNN HELD-OUT TEST EVALUATION")
print("========================================")

print(
    f"\nST-GNN"
    f"\nMAE : {stgnn_mae:.4f} µg/m³"
    f"\nRMSE: {stgnn_rmse:.4f} µg/m³"
    f"\nR²  : {stgnn_r2:.4f}"
)

print(
    f"\nPersistence"
    f"\nMAE : {persist_mae:.4f} µg/m³"
    f"\nRMSE: {persist_rmse:.4f} µg/m³"
    f"\nR²  : {persist_r2:.4f}"
)

mae_change = (
    (persist_mae - stgnn_mae)
    / persist_mae
    * 100
)

rmse_change = (
    (persist_rmse - stgnn_rmse)
    / persist_rmse
    * 100
)

print(
    f"\nST-GNN vs persistence:"
    f"\nMAE change : {mae_change:+.2f}%"
    f"\nRMSE change: {rmse_change:+.2f}%"
)

# =========================================================
# Horizon metrics
# =========================================================

horizon_rows = []

for h in range(FORECAST_DAYS):

    true_h = actual[:, h, :].reshape(-1)
    pred_h = predictions[:, h, :].reshape(-1)
    pers_h = persistence[:, h, :].reshape(-1)

    mae = mean_absolute_error(
        true_h,
        pred_h
    )

    rmse = np.sqrt(
        mean_squared_error(
            true_h,
            pred_h
        )
    )

    r2 = r2_score(
        true_h,
        pred_h
    )

    p_mae = mean_absolute_error(
        true_h,
        pers_h
    )

    p_rmse = np.sqrt(
        mean_squared_error(
            true_h,
            pers_h
        )
    )

    horizon_rows.append({
        "horizon_day": h + 1,
        "stgnn_mae": mae,
        "stgnn_rmse": rmse,
        "stgnn_r2": r2,
        "persistence_mae": p_mae,
        "persistence_rmse": p_rmse,
        "mae_improvement_pct": (
            (p_mae - mae) / p_mae * 100
        ),
        "rmse_improvement_pct": (
            (p_rmse - rmse) / p_rmse * 100
        )
    })

horizon_df = pd.DataFrame(
    horizon_rows
)

print("\n========================================")
print("HORIZON PERFORMANCE")
print("========================================")

print(
    horizon_df.to_string(
        index=False,
        float_format=lambda x: f"{x:.4f}"
    )
)

horizon_df.to_csv(
    DATA_DIR /
    "stgnn_horizon_metrics.csv",
    index=False
)

# =========================================================
# Ward-level metrics
# =========================================================

ward_rows = []

for i, ward in enumerate(WARDS):

    true_w = actual[:, :, i].reshape(-1)
    pred_w = predictions[:, :, i].reshape(-1)
    pers_w = persistence[:, :, i].reshape(-1)

    mae = mean_absolute_error(
        true_w,
        pred_w
    )

    rmse = np.sqrt(
        mean_squared_error(
            true_w,
            pred_w
        )
    )

    p_mae = mean_absolute_error(
        true_w,
        pers_w
    )

    ward_rows.append({
        "ward_code": ward,
        "samples": actual.shape[0],
        "stgnn_mae": mae,
        "stgnn_rmse": rmse,
        "persistence_mae": p_mae,
        "mae_improvement_pct": (
            (p_mae - mae) / p_mae * 100
        )
    })

ward_df = pd.DataFrame(
    ward_rows
)

print("\n========================================")
print("WARD PERFORMANCE")
print("========================================")

print(
    ward_df.to_string(
        index=False,
        float_format=lambda x: f"{x:.4f}"
    )
)

ward_df.to_csv(
    DATA_DIR /
    "stgnn_ward_metrics.csv",
    index=False
)

# =========================================================
# Save predictions
# =========================================================

prediction_rows = []

meta = pd.read_csv(
    DATA_DIR /
    "test_metadata.csv"
)

for sample_idx in range(
    len(predictions)
):

    for h in range(
        FORECAST_DAYS
    ):

        for node_idx, ward in enumerate(
            WARDS
        ):

            prediction_rows.append({
                "sample": sample_idx,
                "forecast_day": h + 1,
                "ward_code": ward,
                "actual_pm25": actual[
                    sample_idx,
                    h,
                    node_idx
                ],
                "stgnn_pm25": predictions[
                    sample_idx,
                    h,
                    node_idx
                ],
                "persistence_pm25": persistence[
                    sample_idx,
                    h,
                    node_idx
                ]
            })

prediction_df = pd.DataFrame(
    prediction_rows
)

prediction_df.to_csv(
    DATA_DIR /
    "stgnn_test_predictions.csv",
    index=False
)

print("\nSaved:")
print(DATA_DIR / "stgnn_horizon_metrics.csv")
print(DATA_DIR / "stgnn_ward_metrics.csv")
print(DATA_DIR / "stgnn_test_predictions.csv")

print("\nTest evaluation complete.")

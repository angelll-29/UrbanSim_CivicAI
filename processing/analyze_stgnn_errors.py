import pandas as pd
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

INPUT = (
    ROOT /
    "data" /
    "processed" /
    "stgnn" /
    "stgnn_test_predictions.csv"
)

OUT = (
    ROOT /
    "data" /
    "processed" /
    "stgnn" /
    "stgnn_error_analysis.csv"
)

df = pd.read_csv(INPUT)

# ---------------------------------------------------------
# Prediction errors
# ---------------------------------------------------------

df["error"] = (
    df["stgnn_pm25"] -
    df["actual_pm25"]
)

df["absolute_error"] = (
    df["error"].abs()
)

df["squared_error"] = (
    df["error"] ** 2
)

df["persistence_error"] = (
    df["persistence_pm25"] -
    df["actual_pm25"]
)

df["persistence_absolute_error"] = (
    df["persistence_error"].abs()
)

# ---------------------------------------------------------
# Overall
# ---------------------------------------------------------

overall = {
    "samples": len(df),

    "actual_mean": df["actual_pm25"].mean(),
    "prediction_mean": df["stgnn_pm25"].mean(),

    "bias": df["error"].mean(),
    "mae": df["absolute_error"].mean(),
    "rmse": np.sqrt(
        df["squared_error"].mean()
    ),

    "overprediction_pct": (
        (df["error"] > 0).mean() * 100
    ),

    "underprediction_pct": (
        (df["error"] < 0).mean() * 100
    ),

    "exact_or_zero_pct": (
        (df["error"] == 0).mean() * 100
    )
}

print("========================================")
print("ST-GNN ERROR ANALYSIS")
print("========================================")

print("\nOVERALL")

for key, value in overall.items():

    if isinstance(value, float):
        print(
            f"{key:25s}: {value:.4f}"
        )
    else:
        print(
            f"{key:25s}: {value}"
        )

# ---------------------------------------------------------
# Ward analysis
# ---------------------------------------------------------

ward = (
    df.groupby("ward_code")
    .agg(
        observations=("error", "size"),
        actual_mean=("actual_pm25", "mean"),
        prediction_mean=("stgnn_pm25", "mean"),
        bias=("error", "mean"),
        mae=("absolute_error", "mean"),
        rmse=("squared_error", lambda x: np.sqrt(x.mean())),
        persistence_mae=(
            "persistence_absolute_error",
            "mean"
        )
    )
    .reset_index()
)

ward["mae_improvement_pct"] = (
    (
        ward["persistence_mae"] -
        ward["mae"]
    )
    /
    ward["persistence_mae"]
    * 100
)

ward = ward.sort_values(
    "mae_improvement_pct",
    ascending=False
)

print("\n========================================")
print("WARD ERROR ANALYSIS")
print("========================================")

print(
    ward.to_string(
        index=False,
        float_format=lambda x: f"{x:.4f}"
    )
)

# ---------------------------------------------------------
# Horizon analysis
# ---------------------------------------------------------

horizon = (
    df.groupby("forecast_day")
    .agg(
        observations=("error", "size"),
        actual_mean=("actual_pm25", "mean"),
        prediction_mean=("stgnn_pm25", "mean"),
        bias=("error", "mean"),
        mae=("absolute_error", "mean"),
        rmse=("squared_error", lambda x: np.sqrt(x.mean())),
        persistence_mae=(
            "persistence_absolute_error",
            "mean"
        )
    )
    .reset_index()
)

horizon["mae_improvement_pct"] = (
    (
        horizon["persistence_mae"] -
        horizon["mae"]
    )
    /
    horizon["persistence_mae"]
    * 100
)

print("\n========================================")
print("HORIZON ERROR ANALYSIS")
print("========================================")

print(
    horizon.to_string(
        index=False,
        float_format=lambda x: f"{x:.4f}"
    )
)

# ---------------------------------------------------------
# Save combined detailed record
# ---------------------------------------------------------

df.to_csv(
    OUT,
    index=False
)

ward.to_csv(
    ROOT /
    "data" /
    "processed" /
    "stgnn" /
    "stgnn_error_by_ward.csv",
    index=False
)

horizon.to_csv(
    ROOT /
    "data" /
    "processed" /
    "stgnn" /
    "stgnn_error_by_horizon.csv",
    index=False
)

print("\nSaved:")
print(OUT)

print(
    ROOT /
    "data" /
    "processed" /
    "stgnn" /
    "stgnn_error_by_ward.csv"
)

print(
    ROOT /
    "data" /
    "processed" /
    "stgnn" /
    "stgnn_error_by_horizon.csv"
)

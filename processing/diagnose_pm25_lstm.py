import pandas as pd
import numpy as np
from pathlib import Path

PRED = Path(
    "data/processed/lstm/lstm_test_predictions.csv"
)

META = Path(
    "data/processed/lstm/test_metadata.csv"
)

pred = pd.read_csv(PRED)
meta = pd.read_csv(META)

# ------------------------------------------------------------
# Attach ward information
# ------------------------------------------------------------

pred["sequence"] = pred["sequence"].astype(int)

meta = meta.reset_index()
meta = meta.rename(
    columns={"index": "sequence"}
)

pred = pred.merge(
    meta[
        [
            "sequence",
            "urban_ward_code",
            "forecast_start"
        ]
    ],
    on="sequence",
    how="left"
)

# ------------------------------------------------------------
# Errors
# ------------------------------------------------------------

pred["error"] = (
    pred["predicted_pm25"]
    - pred["actual_pm25"]
)

pred["absolute_error"] = (
    pred["error"].abs()
)

pred["squared_error"] = (
    pred["error"] ** 2
)

# ------------------------------------------------------------
# Horizon performance
# ------------------------------------------------------------

horizon = (
    pred.groupby("forecast_day")
    .agg(
        mae=("absolute_error", "mean"),
        rmse=(
            "squared_error",
            lambda x: np.sqrt(x.mean())
        ),
        mean_error=("error", "mean"),
        actual_mean=("actual_pm25", "mean"),
        predicted_mean=("predicted_pm25", "mean")
    )
    .reset_index()
)

# ------------------------------------------------------------
# Ward performance
# ------------------------------------------------------------

ward = (
    pred.groupby("urban_ward_code")
    .agg(
        mae=("absolute_error", "mean"),
        rmse=(
            "squared_error",
            lambda x: np.sqrt(x.mean())
        ),
        mean_error=("error", "mean"),
        actual_mean=("actual_pm25", "mean"),
        predicted_mean=("predicted_pm25", "mean"),
        observations=("actual_pm25", "count")
    )
    .reset_index()
    .sort_values("mae", ascending=False)
)

# ------------------------------------------------------------
# Overall bias
# ------------------------------------------------------------

print("=" * 70)
print("LSTM ERROR DIAGNOSTIC")
print("=" * 70)

print("\nOverall:")
print(
    "Mean error:",
    round(pred["error"].mean(), 4)
)

print(
    "Mean absolute error:",
    round(pred["absolute_error"].mean(), 4)
)

print(
    "Actual mean:",
    round(pred["actual_pm25"].mean(), 4)
)

print(
    "Predicted mean:",
    round(pred["predicted_pm25"].mean(), 4)
)

print("\nHorizon:")
print(
    horizon.to_string(index=False)
)

print("\nWard:")
print(
    ward.to_string(index=False)
)

# ------------------------------------------------------------
# Error distribution
# ------------------------------------------------------------

print("\nError quantiles:")

print(
    pred["error"].quantile(
        [0, .05, .25, .50, .75, .95, 1]
    ).to_string()
)

print("\nAbsolute-error quantiles:")

print(
    pred["absolute_error"].quantile(
        [0, .25, .50, .75, .90, .95, 1]
    ).to_string()
)

# ------------------------------------------------------------
# Save
# ------------------------------------------------------------

horizon.to_csv(
    "data/processed/lstm/lstm_error_by_horizon.csv",
    index=False
)

ward.to_csv(
    "data/processed/lstm/lstm_error_by_ward.csv",
    index=False
)

print("\nSaved:")
print(
    "data/processed/lstm/lstm_error_by_horizon.csv"
)

print(
    "data/processed/lstm/lstm_error_by_ward.csv"
)

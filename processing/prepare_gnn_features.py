import pandas as pd
import numpy as np
import torch
import joblib

from pathlib import Path
from sklearn.preprocessing import StandardScaler

BASE = Path(__file__).resolve().parents[1]

INPUT = BASE / "data" / "processed" / "urban_gnn_node_features.csv"
GRAPH = BASE / "data" / "processed" / "urban_gnn_dataset.pt"

OUTPUT = BASE / "data" / "processed" / "urban_gnn_features_scaled.csv"
SCALER_OUTPUT = BASE / "data" / "processed" / "urban_gnn_feature_scaler.joblib"
DATA_OUTPUT = BASE / "data" / "processed" / "urban_gnn_data_prepared.pt"

print("=" * 70)
print("URBANSIM GNN FEATURE PREPARATION")
print("=" * 70)

# ---------------------------------------------------------
# Load
# ---------------------------------------------------------
df = pd.read_csv(INPUT)
graph = torch.load(GRAPH, weights_only=False)

feature_columns = graph["feature_columns"]
ward_codes = graph["ward_codes"]
edge_index = graph["edge_index"]

print(f"Wards: {len(df)}")
print(f"Features: {len(feature_columns)}")
print(f"Edges: {edge_index.shape[1]}")

# ---------------------------------------------------------
# Validate
# ---------------------------------------------------------
if len(df) != 24:
    raise ValueError(f"Expected 24 wards, found {len(df)}")

if len(feature_columns) != 29:
    raise ValueError(
        f"Expected 29 features, found {len(feature_columns)}"
    )

if df[feature_columns].isna().sum().sum() > 0:
    raise ValueError("Missing feature values detected.")

# ---------------------------------------------------------
# Scale
# ---------------------------------------------------------
scaler = StandardScaler()

X_scaled = scaler.fit_transform(
    df[feature_columns].values
)

# ---------------------------------------------------------
# Validation
# ---------------------------------------------------------
print("\nScaled feature statistics:")

print(
    f"Mean absolute feature mean: "
    f"{np.abs(X_scaled.mean(axis=0)).mean():.8f}"
)

print(
    f"Mean feature standard deviation: "
    f"{X_scaled.std(axis=0).mean():.8f}"
)

# ---------------------------------------------------------
# Save scaled CSV
# ---------------------------------------------------------
scaled_df = pd.DataFrame(
    X_scaled,
    columns=feature_columns
)

scaled_df.insert(
    0,
    "ward_code",
    df["ward_code"]
)

scaled_df.to_csv(
    OUTPUT,
    index=False
)

# ---------------------------------------------------------
# Save scaler
# ---------------------------------------------------------
joblib.dump(
    scaler,
    SCALER_OUTPUT
)

# ---------------------------------------------------------
# Create PyTorch tensors
# ---------------------------------------------------------
X_tensor = torch.tensor(
    X_scaled,
    dtype=torch.float32
)

# ---------------------------------------------------------
# PyTorch Geometric-compatible dataset
# ---------------------------------------------------------
prepared = {
    "x": X_tensor,
    "edge_index": edge_index,
    "ward_codes": ward_codes,
    "feature_columns": feature_columns
}

torch.save(
    prepared,
    DATA_OUTPUT
)

# ---------------------------------------------------------
# Report
# ---------------------------------------------------------
print("\n" + "=" * 70)
print("GNN FEATURE PREPARATION COMPLETE")
print("=" * 70)

print(f"Node matrix: {tuple(X_tensor.shape)}")
print(f"Edge index: {tuple(edge_index.shape)}")
print(f"Missing values: {torch.isnan(X_tensor).sum().item()}")

print(f"\nScaled features:")
print(OUTPUT)

print(f"\nScaler:")
print(SCALER_OUTPUT)

print(f"\nPrepared dataset:")
print(DATA_OUTPUT)

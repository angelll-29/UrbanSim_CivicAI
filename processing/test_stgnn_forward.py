import numpy as np
import pandas as pd
import torch

from stgnn_model import STGNN

ROOT = "data/processed"

# Load prepared training data
data = np.load(
    f"{ROOT}/stgnn/train_prepared.npz"
)

X = torch.tensor(
    data["X"][:4],
    dtype=torch.float32
)

# Load graph
edges = pd.read_csv(
    f"{ROOT}/stgnn_ward_edges.csv"
)

wards = [
    "E", "FN", "FS", "GS", "HE", "KE",
    "L", "ME", "N", "PN", "RC"
]

ward_to_idx = {
    ward: i
    for i, ward in enumerate(wards)
}

adjacency = torch.zeros(
    (len(wards), len(wards)),
    dtype=torch.float32
)

for _, row in edges.iterrows():

    source = ward_to_idx[row["source"]]
    target = ward_to_idx[row["target"]]

    adjacency[source, target] = 1.0

# Add self connections
adjacency += torch.eye(
    len(wards)
)

# ---------------------------------------------------------
# Create model
# ---------------------------------------------------------

model = STGNN(
    num_nodes=11,
    input_features=9,
    spatial_hidden=32,
    temporal_hidden=32,
    forecast_days=7
)

model.eval()

# ---------------------------------------------------------
# Forward pass
# ---------------------------------------------------------

with torch.no_grad():

    output = model(
        X,
        adjacency
    )

print("========================================")
print("ST-GNN FORWARD PASS TEST")
print("========================================")

print("Input shape :", tuple(X.shape))
print("Graph shape :", tuple(adjacency.shape))
print("Output shape:", tuple(output.shape))

print("\nExpected:")
print("Input  : (4, 60, 11, 9)")
print("Graph  : (11, 11)")
print("Output : (4, 7, 11)")

print("\nModel parameters:")
print(
    sum(
        p.numel()
        for p in model.parameters()
    )
)

print("\nForward pass: SUCCESS")

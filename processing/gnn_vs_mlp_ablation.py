import torch
import torch.nn as nn
import torch.nn.functional as F
import pandas as pd
import numpy as np

from pathlib import Path
from torch_geometric.nn import SAGEConv
from sklearn.metrics import mean_squared_error, mean_absolute_error

BASE = Path(__file__).resolve().parents[1]

DATA_PATH = BASE / "data" / "processed" / "urban_gnn_data_prepared.pt"
OUTPUT = BASE / "data" / "processed" / "gnn_vs_mlp_ablation.csv"

torch.manual_seed(42)
np.random.seed(42)

print("=" * 70)
print("URBANSIM GNN VS MLP ABLATION")
print("=" * 70)

data = torch.load(
    DATA_PATH,
    weights_only=False
)

x = data["x"]
edge_index = data["edge_index"]
ward_codes = data["ward_codes"]

print(f"Nodes: {x.shape[0]}")
print(f"Features: {x.shape[1]}")
print(f"Edges: {edge_index.shape[1]}")

# ---------------------------------------------------------
# MLP baseline
# ---------------------------------------------------------
class MLPEncoder(nn.Module):

    def __init__(
        self,
        input_dim=29,
        hidden_dim=64,
        embedding_dim=32
    ):
        super().__init__()

        self.encoder = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.20),
            nn.Linear(hidden_dim, embedding_dim)
        )

        self.decoder = nn.Sequential(
            nn.Linear(embedding_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.20),
            nn.Linear(hidden_dim, input_dim)
        )

    def forward(self, x):

        z = self.encoder(x)
        reconstruction = self.decoder(z)

        return z, reconstruction


# ---------------------------------------------------------
# GraphSAGE baseline
# ---------------------------------------------------------
class GraphSAGEEncoder(nn.Module):

    def __init__(
        self,
        input_dim=29,
        hidden_dim=64,
        embedding_dim=32
    ):
        super().__init__()

        self.conv1 = SAGEConv(
            input_dim,
            hidden_dim
        )

        self.conv2 = SAGEConv(
            hidden_dim,
            embedding_dim
        )

        self.decoder = nn.Sequential(
            nn.Linear(embedding_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.20),
            nn.Linear(hidden_dim, input_dim)
        )

    def forward(self, x, edge_index):

        z = self.conv1(
            x,
            edge_index
        )

        z = F.relu(z)

        z = F.dropout(
            z,
            p=0.20,
            training=self.training
        )

        z = self.conv2(
            z,
            edge_index
        )

        reconstruction = self.decoder(z)

        return z, reconstruction


# ---------------------------------------------------------
# Training helper
# ---------------------------------------------------------
def train_mlp():

    model = MLPEncoder()

    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=0.001,
        weight_decay=1e-4
    )

    best_loss = float("inf")
    best_state = None
    best_epoch = 0

    patience = 50
    wait = 0

    for epoch in range(1, 501):

        model.train()

        optimizer.zero_grad()

        z, reconstruction = model(x)

        loss = F.mse_loss(
            reconstruction,
            x
        )

        loss.backward()
        optimizer.step()

        current = loss.item()

        if current < best_loss:

            best_loss = current
            best_epoch = epoch
            wait = 0

            best_state = {
                k: v.detach().cpu().clone()
                for k, v in model.state_dict().items()
            }

        else:
            wait += 1

        if wait >= patience:
            break

    model.load_state_dict(best_state)

    model.eval()

    with torch.no_grad():

        z, reconstruction = model(x)

    return (
        model,
        z,
        reconstruction,
        best_epoch,
        best_loss
    )


def train_gnn():

    model = GraphSAGEEncoder()

    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=0.001,
        weight_decay=1e-4
    )

    best_loss = float("inf")
    best_state = None
    best_epoch = 0

    patience = 50
    wait = 0

    for epoch in range(1, 501):

        model.train()

        optimizer.zero_grad()

        z, reconstruction = model(
            x,
            edge_index
        )

        loss = F.mse_loss(
            reconstruction,
            x
        )

        loss.backward()
        optimizer.step()

        current = loss.item()

        if current < best_loss:

            best_loss = current
            best_epoch = epoch
            wait = 0

            best_state = {
                k: v.detach().cpu().clone()
                for k, v in model.state_dict().items()
            }

        else:
            wait += 1

        if wait >= patience:
            break

    model.load_state_dict(best_state)

    model.eval()

    with torch.no_grad():

        z, reconstruction = model(
            x,
            edge_index
        )

    return (
        model,
        z,
        reconstruction,
        best_epoch,
        best_loss
    )


# ---------------------------------------------------------
# Run MLP
# ---------------------------------------------------------
print("\nTraining MLP baseline...")

mlp_model, mlp_z, mlp_recon, mlp_epoch, mlp_loss = train_mlp()

mlp_mse = mean_squared_error(
    x.numpy().ravel(),
    mlp_recon.detach().numpy().ravel()
)

mlp_mae = mean_absolute_error(
    x.numpy().ravel(),
    mlp_recon.detach().numpy().ravel()
)

print(
    f"MLP best epoch: {mlp_epoch}"
)

print(
    f"MLP MSE: {mlp_mse:.6f}"
)

print(
    f"MLP MAE: {mlp_mae:.6f}"
)

# ---------------------------------------------------------
# Run GraphSAGE
# ---------------------------------------------------------
print("\nTraining GraphSAGE baseline...")

gnn_model, gnn_z, gnn_recon, gnn_epoch, gnn_loss = train_gnn()

gnn_mse = mean_squared_error(
    x.numpy().ravel(),
    gnn_recon.detach().numpy().ravel()
)

gnn_mae = mean_absolute_error(
    x.numpy().ravel(),
    gnn_recon.detach().numpy().ravel()
)

print(
    f"GraphSAGE best epoch: {gnn_epoch}"
)

print(
    f"GraphSAGE MSE: {gnn_mse:.6f}"
)

print(
    f"GraphSAGE MAE: {gnn_mae:.6f}"
)

# ---------------------------------------------------------
# Comparison
# ---------------------------------------------------------
mse_change = (
    (mlp_mse - gnn_mse)
    / mlp_mse
) * 100

mae_change = (
    (mlp_mae - gnn_mae)
    / mlp_mae
) * 100

print("\n" + "=" * 70)
print("ABLATION RESULT")
print("=" * 70)

print(
    f"MLP MSE:       {mlp_mse:.6f}"
)

print(
    f"GraphSAGE MSE: {gnn_mse:.6f}"
)

print(
    f"MSE change:    {mse_change:+.2f}%"
)

print()

print(
    f"MLP MAE:       {mlp_mae:.6f}"
)

print(
    f"GraphSAGE MAE: {gnn_mae:.6f}"
)

print(
    f"MAE change:    {mae_change:+.2f}%"
)

# ---------------------------------------------------------
# Save result
# ---------------------------------------------------------
results = pd.DataFrame([
    {
        "model": "MLP",
        "uses_spatial_graph": False,
        "best_epoch": mlp_epoch,
        "mse": mlp_mse,
        "mae": mlp_mae
    },
    {
        "model": "GraphSAGE",
        "uses_spatial_graph": True,
        "best_epoch": gnn_epoch,
        "mse": gnn_mse,
        "mae": gnn_mae
    }
])

results.to_csv(
    OUTPUT,
    index=False
)

print(f"\nResults saved:")
print(OUTPUT)

print("\nGNN vs MLP ablation complete.")

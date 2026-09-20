import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import SAGEConv
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]

INPUT = BASE / "data" / "processed" / "urban_gnn_data_prepared.pt"
MODEL_OUTPUT = BASE / "ml" / "models" / "urban_graphsage_encoder.pt"

print("=" * 70)
print("URBANSIM GRAPH SAGE MODEL")
print("=" * 70)

# ---------------------------------------------------------
# Load graph
# ---------------------------------------------------------
data = torch.load(
    INPUT,
    weights_only=False
)

x = data["x"]
edge_index = data["edge_index"]
ward_codes = data["ward_codes"]
feature_columns = data["feature_columns"]

print(f"Input nodes: {x.shape[0]}")
print(f"Input features: {x.shape[1]}")
print(f"Edges: {edge_index.shape[1]}")

# ---------------------------------------------------------
# GraphSAGE encoder
# ---------------------------------------------------------
class UrbanGraphSAGE(nn.Module):

    def __init__(
        self,
        input_dim=29,
        hidden_dim=64,
        embedding_dim=32,
        dropout=0.20
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

        self.dropout = dropout

    def forward(
        self,
        x,
        edge_index
    ):

        x = self.conv1(
            x,
            edge_index
        )

        x = F.relu(x)

        x = F.dropout(
            x,
            p=self.dropout,
            training=self.training
        )

        x = self.conv2(
            x,
            edge_index
        )

        return x


# ---------------------------------------------------------
# Create model
# ---------------------------------------------------------
model = UrbanGraphSAGE(
    input_dim=29,
    hidden_dim=64,
    embedding_dim=32,
    dropout=0.20
)

print("\nModel architecture:")
print(model)

parameter_count = sum(
    p.numel()
    for p in model.parameters()
)

print(f"\nTrainable parameters: {parameter_count:,}")

# ---------------------------------------------------------
# Self-supervised reconstruction objective
#
# The decoder attempts to reconstruct the standardized
# node features from the spatial embedding.
# ---------------------------------------------------------
decoder = nn.Sequential(
    nn.Linear(32, 64),
    nn.ReLU(),
    nn.Dropout(0.20),
    nn.Linear(64, 29)
)

parameters = list(model.parameters()) + list(
    decoder.parameters()
)

optimizer = torch.optim.Adam(
    parameters,
    lr=0.001,
    weight_decay=1e-4
)

# ---------------------------------------------------------
# Training
# ---------------------------------------------------------
epochs = 500
patience = 50
best_loss = float("inf")
best_epoch = 0
patience_counter = 0

best_model_state = None
best_decoder_state = None

print("\nTraining GraphSAGE...")
print("-" * 70)

for epoch in range(1, epochs + 1):

    model.train()
    decoder.train()

    optimizer.zero_grad()

    embedding = model(
        x,
        edge_index
    )

    reconstruction = decoder(
        embedding
    )

    loss = F.mse_loss(
        reconstruction,
        x
    )

    loss.backward()

    optimizer.step()

    current_loss = loss.item()

    # -----------------------------------------------------
    # Early stopping
    # -----------------------------------------------------
    if current_loss < best_loss:

        best_loss = current_loss
        best_epoch = epoch
        patience_counter = 0

        best_model_state = {
            k: v.detach().cpu().clone()
            for k, v in model.state_dict().items()
        }

        best_decoder_state = {
            k: v.detach().cpu().clone()
            for k, v in decoder.state_dict().items()
        }

    else:

        patience_counter += 1

    if epoch == 1 or epoch % 25 == 0:

        print(
            f"Epoch {epoch:03d} | "
            f"Loss: {current_loss:.6f} | "
            f"Best: {best_loss:.6f}"
        )

    if patience_counter >= patience:

        print(
            f"\nEarly stopping at epoch {epoch}."
        )

        break

# ---------------------------------------------------------
# Restore best model
# ---------------------------------------------------------
model.load_state_dict(
    best_model_state
)

decoder.load_state_dict(
    best_decoder_state
)

# ---------------------------------------------------------
# Generate final embeddings
# ---------------------------------------------------------
model.eval()
decoder.eval()

with torch.no_grad():

    embeddings = model(
        x,
        edge_index
    )

    reconstruction = decoder(
        embeddings
    )

    final_loss = F.mse_loss(
        reconstruction,
        x
    ).item()

# ---------------------------------------------------------
# Save model
# ---------------------------------------------------------
torch.save(
    {
        "model_state_dict": model.state_dict(),
        "decoder_state_dict": decoder.state_dict(),
        "input_dim": 29,
        "hidden_dim": 64,
        "embedding_dim": 32,
        "dropout": 0.20,
        "feature_columns": feature_columns,
        "ward_codes": ward_codes
    },
    MODEL_OUTPUT
)

# ---------------------------------------------------------
# Save embeddings
# ---------------------------------------------------------
embedding_columns = [
    f"gnn_embedding_{i+1}"
    for i in range(32)
]

embedding_df = embeddings.numpy()

import pandas as pd

embedding_df = pd.DataFrame(
    embedding_df,
    columns=embedding_columns
)

embedding_df.insert(
    0,
    "ward_code",
    ward_codes
)

embedding_output = (
    BASE
    / "data"
    / "processed"
    / "urban_gnn_embeddings.csv"
)

embedding_df.to_csv(
    embedding_output,
    index=False
)

# ---------------------------------------------------------
# Final report
# ---------------------------------------------------------
print("\n" + "=" * 70)
print("GRAPH SAGE TRAINING COMPLETE")
print("=" * 70)

print(f"Best epoch: {best_epoch}")
print(f"Best reconstruction loss: {best_loss:.6f}")
print(f"Final reconstruction loss: {final_loss:.6f}")

print(
    f"\nEmbedding shape: "
    f"{tuple(embeddings.shape)}"
)

print(f"\nModel saved:")
print(MODEL_OUTPUT)

print(f"\nEmbeddings saved:")
print(embedding_output)

print("\nGNN spatial representation complete.")

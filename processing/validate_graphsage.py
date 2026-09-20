import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from pathlib import Path
from torch_geometric.nn import SAGEConv
from sklearn.metrics import mean_squared_error, mean_absolute_error
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

BASE = Path(__file__).resolve().parents[1]

DATA_PATH = BASE / "data" / "processed" / "urban_gnn_data_prepared.pt"
MODEL_PATH = BASE / "ml" / "models" / "urban_graphsage_encoder.pt"
AE_PATH = BASE / "data" / "processed" / "urban_ward_embeddings_validated.csv"

OUTPUT_RECON = BASE / "data" / "processed" / "urban_gnn_reconstruction.csv"
OUTPUT_EMBED = BASE / "data" / "processed" / "urban_gnn_embeddings_validated.csv"

print("=" * 70)
print("URBANSIM GRAPHSAGE VALIDATION")
print("=" * 70)

# ---------------------------------------------------------
# GraphSAGE architecture
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

    def forward(self, x, edge_index):

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
# Load data
# ---------------------------------------------------------
data = torch.load(
    DATA_PATH,
    weights_only=False
)

x = data["x"]
edge_index = data["edge_index"]
ward_codes = data["ward_codes"]
feature_columns = data["feature_columns"]

print(f"Nodes: {x.shape[0]}")
print(f"Features: {x.shape[1]}")
print(f"Edges: {edge_index.shape[1]}")

# ---------------------------------------------------------
# Load trained model
# ---------------------------------------------------------
checkpoint = torch.load(
    MODEL_PATH,
    weights_only=False
)

model = UrbanGraphSAGE(
    input_dim=checkpoint["input_dim"],
    hidden_dim=checkpoint["hidden_dim"],
    embedding_dim=checkpoint["embedding_dim"],
    dropout=checkpoint["dropout"]
)

model.load_state_dict(
    checkpoint["model_state_dict"]
)

# ---------------------------------------------------------
# Decoder
# ---------------------------------------------------------
decoder = nn.Sequential(
    nn.Linear(32, 64),
    nn.ReLU(),
    nn.Dropout(0.20),
    nn.Linear(64, 29)
)

decoder.load_state_dict(
    checkpoint["decoder_state_dict"]
)

model.eval()
decoder.eval()

# ---------------------------------------------------------
# Generate embeddings
# ---------------------------------------------------------
with torch.no_grad():

    embeddings = model(
        x,
        edge_index
    )

    reconstruction = decoder(
        embeddings
    )

# ---------------------------------------------------------
# Reconstruction metrics
# ---------------------------------------------------------
x_np = x.numpy()
reconstruction_np = reconstruction.numpy()

mse = mean_squared_error(
    x_np.ravel(),
    reconstruction_np.ravel()
)

mae = mean_absolute_error(
    x_np.ravel(),
    reconstruction_np.ravel()
)

ward_mse = np.mean(
    (x_np - reconstruction_np) ** 2,
    axis=1
)

# ---------------------------------------------------------
# Feature reconstruction
# ---------------------------------------------------------
feature_mse = np.mean(
    (x_np - reconstruction_np) ** 2,
    axis=0
)

feature_mae = np.mean(
    np.abs(x_np - reconstruction_np),
    axis=0
)

feature_df = pd.DataFrame({
    "feature": feature_columns,
    "mse": feature_mse,
    "mae": feature_mae
}).sort_values(
    "mse",
    ascending=False
)

# ---------------------------------------------------------
# Ward reconstruction
# ---------------------------------------------------------
ward_df = pd.DataFrame({
    "ward_code": ward_codes,
    "reconstruction_mse": ward_mse
}).sort_values(
    "reconstruction_mse",
    ascending=False
)

ward_df.to_csv(
    OUTPUT_RECON,
    index=False
)

# ---------------------------------------------------------
# Save validated embeddings
# ---------------------------------------------------------
embedding_columns = [
    f"gnn_embedding_{i+1}"
    for i in range(32)
]

embedding_df = pd.DataFrame(
    embeddings.numpy(),
    columns=embedding_columns
)

embedding_df.insert(
    0,
    "ward_code",
    ward_codes
)

embedding_df.to_csv(
    OUTPUT_EMBED,
    index=False
)

# ---------------------------------------------------------
# PCA on GNN embeddings
# ---------------------------------------------------------
pca = PCA(
    n_components=2
)

gnn_pca = pca.fit_transform(
    embeddings.numpy()
)

explained = pca.explained_variance_ratio_

# ---------------------------------------------------------
# KMeans exploratory structure
# ---------------------------------------------------------
kmeans_results = []

for k in range(2, 6):

    km = KMeans(
        n_clusters=k,
        random_state=42,
        n_init=50
    )

    labels = km.fit_predict(
        embeddings.numpy()
    )

    score = silhouette_score(
        embeddings.numpy(),
        labels
    )

    kmeans_results.append({
        "k": k,
        "silhouette": score
    })

kmeans_df = pd.DataFrame(
    kmeans_results
)

best_k_row = kmeans_df.loc[
    kmeans_df["silhouette"].idxmax()
]

# ---------------------------------------------------------
# Compare with Autoencoder embeddings
# ---------------------------------------------------------
ae_available = AE_PATH.exists()

if ae_available:

    ae = pd.read_csv(
        AE_PATH
    )

    ae_embedding_cols = [
        c for c in ae.columns
        if c.startswith("embedding_")
    ]

    if len(ae_embedding_cols) == 0:

        ae_available = False

    else:

        ae_merged = ae[
            ["ward_code"] + ae_embedding_cols
        ].copy()

        gnn_merged = embedding_df.merge(
            ae_merged,
            on="ward_code",
            how="inner"
        )

        print(
            f"Autoencoder comparison wards: "
            f"{len(gnn_merged)}"
        )

# ---------------------------------------------------------
# Report
# ---------------------------------------------------------
print("\n" + "=" * 70)
print("RECONSTRUCTION VALIDATION")
print("=" * 70)

print(
    f"Overall MSE: {mse:.6f}"
)

print(
    f"Overall MAE: {mae:.6f}"
)

print(
    f"Ward MSE min: {ward_mse.min():.6f}"
)

print(
    f"Ward MSE max: {ward_mse.max():.6f}"
)

print(
    f"Ward MSE mean: {ward_mse.mean():.6f}"
)

print("\nTop 10 feature reconstruction errors:")

print(
    feature_df.head(10).to_string(
        index=False
    )
)

print("\nHighest ward reconstruction errors:")

print(
    ward_df.head(10).to_string(
        index=False
    )
)

print("\n" + "=" * 70)
print("GNN EMBEDDING VALIDATION")
print("=" * 70)

print(
    f"Embedding shape: "
    f"{tuple(embeddings.shape)}"
)

print(
    f"PCA PC1 variance: "
    f"{explained[0]:.4f}"
)

print(
    f"PCA PC2 variance: "
    f"{explained[1]:.4f}"
)

print(
    f"First 2 PCs total: "
    f"{explained.sum():.4f}"
)

print("\nExploratory KMeans silhouette:")

print(
    kmeans_df.to_string(
        index=False
    )
)

print(
    f"\nBest exploratory K: "
    f"{int(best_k_row['k'])}"
)

print(
    f"Best silhouette: "
    f"{best_k_row['silhouette']:.4f}"
)

print("\n" + "=" * 70)
print("GNN VALIDATION COMPLETE")
print("=" * 70)

print(f"Reconstruction file:")
print(OUTPUT_RECON)

print(f"\nValidated embeddings:")
print(OUTPUT_EMBED)


import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader
from pathlib import Path

from stgnn_model import STGNN

ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = ROOT / "data" / "processed" / "stgnn"
GRAPH_FILE = ROOT / "data" / "processed" / "stgnn_ward_edges.csv"
MODEL_DIR = ROOT / "ml" / "models"

MODEL_DIR.mkdir(parents=True, exist_ok=True)

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

SEED = 42
np.random.seed(SEED)
torch.manual_seed(SEED)

WARDS = [
    "E", "FN", "FS", "GS", "HE", "KE",
    "L", "ME", "N", "PN", "RC"
]

NUM_NODES = len(WARDS)
INPUT_FEATURES = 9
FORECAST_DAYS = 7

BATCH_SIZE = 8
LEARNING_RATE = 0.001
MAX_EPOCHS = 200
PATIENCE = 30

# =========================================================
# Load data
# =========================================================

train = np.load(DATA_DIR / "train_prepared.npz")
val = np.load(DATA_DIR / "validation_prepared.npz")

X_train = torch.tensor(
    train["X"],
    dtype=torch.float32
)

Y_train = torch.tensor(
    train["Y"],
    dtype=torch.float32
)

X_val = torch.tensor(
    val["X"],
    dtype=torch.float32
)

Y_val = torch.tensor(
    val["Y"],
    dtype=torch.float32
)

print("========================================")
print("ST-GNN TRAINING")
print("========================================")

print(f"Device: {DEVICE}")

print("\nTrain:")
print("X:", tuple(X_train.shape))
print("Y:", tuple(Y_train.shape))

print("\nValidation:")
print("X:", tuple(X_val.shape))
print("Y:", tuple(Y_val.shape))

# =========================================================
# Build adjacency matrix
# =========================================================

edges = pd.read_csv(GRAPH_FILE)

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

    if source not in ward_to_idx:
        continue

    if target not in ward_to_idx:
        continue

    i = ward_to_idx[source]
    j = ward_to_idx[target]

    adjacency[i, j] = 1.0

# Self loops are handled inside the model.
adjacency = adjacency.to(DEVICE)

print("\nGraph:")
print("Nodes:", NUM_NODES)
print(
    "Directed edges:",
    int(adjacency.sum().item())
)

# =========================================================
# DataLoaders
# =========================================================

train_dataset = TensorDataset(
    X_train,
    Y_train
)

val_dataset = TensorDataset(
    X_val,
    Y_val
)

train_loader = DataLoader(
    train_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False
)

val_loader = DataLoader(
    val_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False
)

# =========================================================
# Model
# =========================================================

model = STGNN(
    num_nodes=NUM_NODES,
    input_features=INPUT_FEATURES,
    spatial_hidden=32,
    temporal_hidden=32,
    forecast_days=FORECAST_DAYS
).to(DEVICE)

parameter_count = sum(
    p.numel()
    for p in model.parameters()
    if p.requires_grad
)

print("\nModel parameters:", parameter_count)

optimizer = torch.optim.Adam(
    model.parameters(),
    lr=LEARNING_RATE,
    weight_decay=1e-4
)

criterion = nn.MSELoss()

# =========================================================
# Training
# =========================================================

best_val_loss = float("inf")
best_epoch = 0
patience_counter = 0

model_path = (
    MODEL_DIR /
    "urban_stgnn_pm25_60to7.pt"
)

history = []

for epoch in range(1, MAX_EPOCHS + 1):

    # -----------------------------------------------------
    # Train
    # -----------------------------------------------------

    model.train()

    train_losses = []

    for batch_X, batch_Y in train_loader:

        batch_X = batch_X.to(DEVICE)
        batch_Y = batch_Y.to(DEVICE)

        optimizer.zero_grad()

        predictions = model(
            batch_X,
            adjacency
        )

        loss = criterion(
            predictions,
            batch_Y
        )

        loss.backward()

        torch.nn.utils.clip_grad_norm_(
            model.parameters(),
            max_norm=1.0
        )

        optimizer.step()

        train_losses.append(
            loss.item()
        )

    train_loss = np.mean(
        train_losses
    )

    # -----------------------------------------------------
    # Validation
    # -----------------------------------------------------

    model.eval()

    val_losses = []

    with torch.no_grad():

        for batch_X, batch_Y in val_loader:

            batch_X = batch_X.to(DEVICE)
            batch_Y = batch_Y.to(DEVICE)

            predictions = model(
                batch_X,
                adjacency
            )

            loss = criterion(
                predictions,
                batch_Y
            )

            val_losses.append(
                loss.item()
            )

    val_loss = np.mean(
        val_losses
    )

    history.append({
        "epoch": epoch,
        "train_loss": train_loss,
        "validation_loss": val_loss
    })

    # -----------------------------------------------------
    # Best model
    # -----------------------------------------------------

    if val_loss < best_val_loss:

        best_val_loss = val_loss
        best_epoch = epoch
        patience_counter = 0

        torch.save(
            {
                "model_state_dict": model.state_dict(),
                "num_nodes": NUM_NODES,
                "input_features": INPUT_FEATURES,
                "spatial_hidden": 32,
                "temporal_hidden": 32,
                "forecast_days": FORECAST_DAYS,
                "wards": WARDS
            },
            model_path
        )

    else:

        patience_counter += 1

    # -----------------------------------------------------
    # Progress
    # -----------------------------------------------------

    if (
        epoch == 1
        or epoch % 10 == 0
        or val_loss == best_val_loss
    ):
        print(
            f"Epoch {epoch:03d} | "
            f"Train {train_loss:.6f} | "
            f"Val {val_loss:.6f} | "
            f"Best {best_val_loss:.6f}"
        )

    if patience_counter >= PATIENCE:

        print(
            f"\nEarly stopping at epoch {epoch}."
        )

        break

# =========================================================
# Save history
# =========================================================

history_df = pd.DataFrame(history)

history_df.to_csv(
    DATA_DIR / "stgnn_training_history.csv",
    index=False
)

# =========================================================
# Final report
# =========================================================

print("\n========================================")
print("ST-GNN TRAINING COMPLETE")
print("========================================")

print(f"Best epoch       : {best_epoch}")
print(f"Best validation  : {best_val_loss:.6f}")
print(f"Parameters       : {parameter_count}")

print("\nSaved model:")
print(model_path)

print("\nSaved history:")
print(
    DATA_DIR /
    "stgnn_training_history.csv"
)

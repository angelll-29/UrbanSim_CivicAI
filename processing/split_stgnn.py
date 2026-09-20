import numpy as np
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

INPUT = ROOT / "data" / "processed" / "stgnn_sequences.npz"
META = ROOT / "data" / "processed" / "stgnn_sequence_metadata.csv"

OUT_DIR = ROOT / "data" / "processed" / "stgnn"

OUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

# ---------------------------------------------------------
# Load
# ---------------------------------------------------------

data = np.load(INPUT)

X = data["X"]
Y = data["Y"]
wards = data["wards"]
features = data["features"]

meta = pd.read_csv(META)

meta["forecast_start"] = pd.to_datetime(
    meta["forecast_start"]
)

# Sort chronologically
order = np.argsort(
    meta["forecast_start"].values
)

X = X[order]
Y = Y[order]
meta = meta.iloc[order].reset_index(drop=True)

n = len(X)

# ---------------------------------------------------------
# Chronological split
# ---------------------------------------------------------

train_end = int(n * 0.70)
val_end = int(n * 0.85)

X_train = X[:train_end]
Y_train = Y[:train_end]

X_val = X[train_end:val_end]
Y_val = Y[train_end:val_end]

X_test = X[val_end:]
Y_test = Y[val_end:]

meta_train = meta.iloc[:train_end]
meta_val = meta.iloc[train_end:val_end]
meta_test = meta.iloc[val_end:]

# ---------------------------------------------------------
# Save
# ---------------------------------------------------------

np.savez_compressed(
    OUT_DIR / "train.npz",
    X=X_train,
    Y=Y_train,
    wards=wards,
    features=features
)

np.savez_compressed(
    OUT_DIR / "validation.npz",
    X=X_val,
    Y=Y_val,
    wards=wards,
    features=features
)

np.savez_compressed(
    OUT_DIR / "test.npz",
    X=X_test,
    Y=Y_test,
    wards=wards,
    features=features
)

meta_train.to_csv(
    OUT_DIR / "train_metadata.csv",
    index=False
)

meta_val.to_csv(
    OUT_DIR / "validation_metadata.csv",
    index=False
)

meta_test.to_csv(
    OUT_DIR / "test_metadata.csv",
    index=False
)

# ---------------------------------------------------------
# Report
# ---------------------------------------------------------

print("========================================")
print("ST-GNN CHRONOLOGICAL SPLIT")
print("========================================")

print(f"Total sequences : {n}")

print(f"\nTRAIN")
print(f"Samples: {len(X_train)}")
print(
    f"Forecast dates: "
    f"{meta_train.forecast_start.min().date()} -> "
    f"{meta_train.forecast_start.max().date()}"
)

print(f"\nVALIDATION")
print(f"Samples: {len(X_val)}")
print(
    f"Forecast dates: "
    f"{meta_val.forecast_start.min().date()} -> "
    f"{meta_val.forecast_start.max().date()}"
)

print(f"\nTEST")
print(f"Samples: {len(X_test)}")
print(
    f"Forecast dates: "
    f"{meta_test.forecast_start.min().date()} -> "
    f"{meta_test.forecast_start.max().date()}"
)

print("\nShapes:")
print("Train X:", X_train.shape)
print("Train Y:", Y_train.shape)
print("Val X  :", X_val.shape)
print("Val Y  :", Y_val.shape)
print("Test X :", X_test.shape)
print("Test Y :", Y_test.shape)

print("\nSaved to:")
print(OUT_DIR)

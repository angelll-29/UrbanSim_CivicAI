import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

INPUT_DIR = ROOT / "data" / "processed" / "stgnn"
OUT_DIR = ROOT / "data" / "processed" / "stgnn_residual"

OUT_DIR.mkdir(parents=True, exist_ok=True)

for split in ["train", "validation", "test"]:

    data = np.load(
        INPUT_DIR / f"{split}_prepared.npz"
    )

    X = data["X"].astype(np.float32)
    Y = data["Y"].astype(np.float32)

    # Last observed PM2.5 in the 60-day input window.
    # Feature 0 = PM2.5.
    last_pm25 = X[:, -1, :, 0]

    # IMPORTANT:
    # X is standardized, so Y and last_pm25 are both
    # in standardized PM2.5 units.
    #
    # Residual target:
    # future PM2.5 - current PM2.5
    baseline = last_pm25[:, None, :]

    residual = Y - baseline

    np.savez_compressed(
        OUT_DIR / f"{split}_prepared.npz",
        X=X,
        Y=residual.astype(np.float32),
        baseline=baseline.astype(np.float32),
        wards=data["wards"],
        features=data["features"]
    )

    print(f"{split.upper()}")
    print(f"X shape       : {X.shape}")
    print(f"Residual shape: {residual.shape}")
    print(
        f"Residual mean : {residual.mean():.6f}"
    )
    print(
        f"Residual std  : {residual.std():.6f}"
    )
    print()

print("========================================")
print("RESIDUAL ST-GNN DATASET COMPLETE")
print("========================================")
print(f"Saved to: {OUT_DIR}")

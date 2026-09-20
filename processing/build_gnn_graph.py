import pandas as pd
import geopandas as gpd
import numpy as np
import torch
from pathlib import Path
from libpysal.weights import Queen

BASE = Path(__file__).resolve().parents[1]

FEATURE_FILE = BASE / "data" / "processed" / "urban_ai_features.csv"
WARD_FILE = BASE / "data" / "spatial" / "mumbai_wards.geojson"

NODE_OUTPUT = BASE / "data" / "processed" / "urban_gnn_node_features.csv"
EDGE_OUTPUT = BASE / "data" / "processed" / "urban_gnn_adjacency.csv"
PT_OUTPUT = BASE / "data" / "processed" / "urban_gnn_dataset.pt"

print("=" * 70)
print("URBANSIM GNN GRAPH BUILDER")
print("=" * 70)

# ---------------------------------------------------------
# Load data
# ---------------------------------------------------------
features = pd.read_csv(FEATURE_FILE)
wards = gpd.read_file(WARD_FILE)

print(f"AI feature rows: {len(features)}")
print(f"AI feature columns: {len(features.columns)}")
print(f"Ward polygons: {len(wards)}")
print(f"CRS: {wards.crs}")

# ---------------------------------------------------------
# Normalize ward codes
# ---------------------------------------------------------
def normalize_ward(value):
    if pd.isna(value):
        return None

    value = str(value)

    # Remove actual whitespace/newline/tab characters
    value = " ".join(value.split()).upper().strip()

    mapping = {
        "F/N": "FN",
        "F/S": "FS",
        "G/N": "GN",
        "G/S": "GS",
        "H/E": "HE",
        "H/W": "HW",
        "K/E": "KE",
        "K/W": "KW",
        "M/E": "ME",
        "M/W": "MW",
        "P/N": "PN",
        "P/S": "PS",
        "R/C": "RC",
        "R/N": "RN",
        "R/S": "RS",
    }

    return mapping.get(value, value)


features["ward_code"] = features["ward_code"].apply(normalize_ward)
wards["ward_code"] = wards["NAME2"].apply(normalize_ward)

feature_wards = set(features["ward_code"])
gis_wards = set(wards["ward_code"])

print(f"Feature wards: {len(feature_wards)}")
print(f"GIS wards: {len(gis_wards)}")

if feature_wards != gis_wards:
    print("Missing from features:", sorted(gis_wards - feature_wards))
    print("Missing from GIS:", sorted(feature_wards - gis_wards))
    raise ValueError("Ward sets do not match.")

# ---------------------------------------------------------
# Sort identically
# ---------------------------------------------------------
features = features.sort_values("ward_code").reset_index(drop=True)
wards = wards.sort_values("ward_code").reset_index(drop=True)

ward_codes = wards["ward_code"].tolist()

# ---------------------------------------------------------
# Select 29 numeric AI features
# ---------------------------------------------------------
feature_columns = [
    c for c in features.columns
    if c != "ward_code"
    and pd.api.types.is_numeric_dtype(features[c])
]

print(f"\nNumeric node features: {len(feature_columns)}")

if len(feature_columns) != 29:
    raise ValueError(
        f"Expected 29 numeric features, found {len(feature_columns)}"
    )

# ---------------------------------------------------------
# Missing-value validation
# ---------------------------------------------------------
missing = features[feature_columns].isna().sum()

if missing.sum() > 0:
    print("\nMissing values:")
    print(missing[missing > 0])
    raise ValueError("Missing node features detected.")

print("Missing feature values: 0")

# ---------------------------------------------------------
# Save node features
# ---------------------------------------------------------
node_features = features[["ward_code"] + feature_columns].copy()
node_features.to_csv(NODE_OUTPUT, index=False)

# ---------------------------------------------------------
# Prepare geometries
# ---------------------------------------------------------
invalid_count = (~wards.geometry.is_valid).sum()

if invalid_count > 0:
    print(f"Invalid geometries detected: {invalid_count}")
    wards["geometry"] = wards.geometry.make_valid()

# ---------------------------------------------------------
# Queen contiguity using libpysal
# ---------------------------------------------------------
print("\nBuilding Queen-contiguity graph using libpysal...")

weights = Queen.from_dataframe(
    wards,
    use_index=False
)

n = len(wards)

edges = []

for source, neighbors in weights.neighbors.items():
    for target in neighbors:
        edges.append((source, target))

edges = sorted(set(edges))

# ---------------------------------------------------------
# Edge table
# ---------------------------------------------------------
edge_rows = []

for source, target in edges:
    edge_rows.append({
        "source_index": source,
        "source_ward": ward_codes[source],
        "target_index": target,
        "target_ward": ward_codes[target],
        "adjacent": 1
    })

edge_df = pd.DataFrame(edge_rows)
edge_df.to_csv(EDGE_OUTPUT, index=False)

# ---------------------------------------------------------
# Graph validation
# ---------------------------------------------------------
degree = np.zeros(n, dtype=int)

for source, target in edges:
    degree[source] += 1

isolated = np.where(degree == 0)[0]

print("\n" + "=" * 70)
print("GRAPH VALIDATION")
print("=" * 70)

print(f"Nodes: {n}")
print(f"Directed edges: {len(edges)}")
print(f"Undirected edges: {len(edges) // 2}")
print(f"Minimum degree: {degree.min()}")
print(f"Maximum degree: {degree.max()}")
print(f"Mean degree: {degree.mean():.2f}")
print(f"Isolated nodes: {len(isolated)}")

if len(isolated) > 0:
    print(
        "Isolated wards:",
        [ward_codes[i] for i in isolated]
    )

# ---------------------------------------------------------
# PyTorch tensors
# ---------------------------------------------------------
X = torch.tensor(
    features[feature_columns].values,
    dtype=torch.float32
)

edge_index = torch.tensor(
    np.array(edges).T,
    dtype=torch.long
)

dataset = {
    "x": X,
    "edge_index": edge_index,
    "ward_codes": ward_codes,
    "feature_columns": feature_columns
}

torch.save(dataset, PT_OUTPUT)

# ---------------------------------------------------------
# Final output
# ---------------------------------------------------------
print("\n" + "=" * 70)
print("GNN DATASET CREATED")
print("=" * 70)

print(f"Nodes: {X.shape[0]}")
print(f"Features per node: {X.shape[1]}")
print(f"Edge index shape: {tuple(edge_index.shape)}")

print(f"\nNode features:")
print(NODE_OUTPUT)

print(f"\nAdjacency:")
print(EDGE_OUTPUT)

print(f"\nPyTorch dataset:")
print(PT_OUTPUT)

print("\nWard order:")
print(", ".join(ward_codes))

print("\nGNN graph preparation complete.")

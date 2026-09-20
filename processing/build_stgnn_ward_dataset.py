import pandas as pd
import geopandas as gpd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

INPUT = ROOT / "data" / "processed" / "mumbai_openaq_multivariate_daily_aligned.csv"
WARDS = ROOT / "data" / "spatial" / "mumbai_wards.geojson"

OUT_DATA = ROOT / "data" / "processed" / "stgnn_ward_daily_features.csv"
OUT_EDGES = ROOT / "data" / "processed" / "stgnn_ward_edges.csv"

MODEL_WARDS = [
    "E", "FN", "FS", "GS", "HE", "KE",
    "L", "ME", "N", "PN", "RC"
]

FEATURES = [
    "pm25",
    "temperature",
    "relativehumidity",
    "wind_speed",
    "wind_direction",
    "no2",
    "o3",
    "so2",
    "co"
]

# =========================================================
# 1. LOAD OPENAQ DATA
# =========================================================

print("Loading environmental data...")

df = pd.read_csv(INPUT)

required_columns = [
    "openaq_location_id",
    "station_name",
    "urban_ward_code",
    "date"
] + FEATURES

missing = [c for c in required_columns if c not in df.columns]

if missing:
    raise ValueError(f"Missing required columns: {missing}")

df["date"] = pd.to_datetime(df["date"], errors="coerce")

df["urban_ward_code"] = (
    df["urban_ward_code"]
    .astype(str)
    .str.strip()
    .str.upper()
)

df = df[df["urban_ward_code"].isin(MODEL_WARDS)].copy()

print(f"Input rows: {len(df):,}")
print(f"Locations: {df['openaq_location_id'].nunique()}")
print(f"Wards: {sorted(df['urban_ward_code'].unique())}")
print(
    f"Date range: "
    f"{df['date'].min().date()} -> {df['date'].max().date()}"
)

# =========================================================
# 2. AGGREGATE MULTIPLE LOCATIONS → WARD-DAY
# =========================================================

print("\nAggregating OpenAQ locations to ward-day level...")

agg = (
    df.groupby(
        ["urban_ward_code", "date"],
        as_index=False
    )[FEATURES]
    .mean()
    .sort_values(["urban_ward_code", "date"])
)

agg = agg.rename(
    columns={"urban_ward_code": "ward_code"}
)

print(f"Ward-day rows: {len(agg):,}")
print(f"Wards represented: {agg['ward_code'].nunique()}")

# =========================================================
# 3. WARD TEMPORAL COVERAGE
# =========================================================

coverage = (
    agg.groupby("ward_code")
    .agg(
        days=("date", "nunique"),
        first_date=("date", "min"),
        last_date=("date", "max")
    )
    .reindex(MODEL_WARDS)
)

print("\nWard temporal coverage:")
print(coverage.to_string())

# =========================================================
# 4. BUILD QUEEN SPATIAL GRAPH
# =========================================================

print("\nBuilding Queen adjacency graph...")

wards = gpd.read_file(WARDS)

def normalize_ward(value):
    value = str(value).strip().upper()

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

wards["ward_code"] = wards["NAME2"].apply(normalize_ward)

wards = wards[
    wards["ward_code"].isin(MODEL_WARDS)
].copy()

print(f"Spatial polygons used: {len(wards)}")

edges = []

for i, row_i in wards.iterrows():

    for j, row_j in wards.iterrows():

        if i >= j:
            continue

        if row_i.geometry.intersects(row_j.geometry):

            a = row_i["ward_code"]
            b = row_j["ward_code"]

            edges.append((a, b))
            edges.append((b, a))

edges_df = pd.DataFrame(
    edges,
    columns=["source", "target"]
)

edges_df = (
    edges_df
    .drop_duplicates()
    .reset_index(drop=True)
)

print(f"Observed wards: {len(MODEL_WARDS)}")
print(f"Directed edges: {len(edges_df)}")
print(f"Undirected edges: {len(edges_df) // 2}")

# =========================================================
# 5. GRAPH DEGREE CHECK
# =========================================================

degree = (
    edges_df.groupby("source")
    .size()
    .reindex(MODEL_WARDS)
    .fillna(0)
)

print("\nGraph degree:")
print(degree.to_string())

isolated = degree[degree == 0].index.tolist()

if isolated:
    print("\nWARNING — isolated wards:")
    print(isolated)
else:
    print("\nNo isolated observed wards.")

# =========================================================
# 6. SAVE
# =========================================================

OUT_DATA.parent.mkdir(
    parents=True,
    exist_ok=True
)

agg.to_csv(
    OUT_DATA,
    index=False
)

edges_df.to_csv(
    OUT_EDGES,
    index=False
)

print("\n========================================")
print("ST-GNN DATASET PREPARATION COMPLETE")
print("========================================")

print(f"\nWard-day dataset:")
print(OUT_DATA)

print(f"\nSpatial graph:")
print(OUT_EDGES)

print("\nFeatures:")
for feature in FEATURES:
    print(f"  - {feature}")

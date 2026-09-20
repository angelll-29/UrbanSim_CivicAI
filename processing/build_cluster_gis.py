import geopandas as gpd
import pandas as pd
from pathlib import Path

WARD_FILE = Path("data/spatial/mumbai_wards.geojson")
CLUSTER_FILE = Path("data/processed/mumbai_ward_clusters.csv")
PROFILE_FILE = Path("data/processed/urban_cluster_profiles.csv")

OUTPUT = Path("data/spatial/mumbai_ward_clusters.geojson")

# --------------------------------------------------
# Load
# --------------------------------------------------
wards = gpd.read_file(WARD_FILE)
clusters = pd.read_csv(CLUSTER_FILE)

print("=" * 60)
print("URBANSIM GIS CLUSTER LAYER")
print("=" * 60)

print("\nWard polygons:", len(wards))
print("Cluster records:", len(clusters))

# --------------------------------------------------
# Normalize GIS ward code
# --------------------------------------------------
def normalize_ward(value):
    if pd.isna(value):
        return None

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

# --------------------------------------------------
# Validate cluster codes
# --------------------------------------------------
cluster_codes = set(clusters["ward_code"])
gis_codes = set(wards["ward_code"])

missing_in_gis = cluster_codes - gis_codes
missing_in_clusters = gis_codes - cluster_codes

print("\nMissing cluster wards in GIS:", missing_in_gis)
print("Missing GIS wards in clusters:", missing_in_clusters)

if missing_in_gis or missing_in_clusters:
    raise ValueError("Ward-code mismatch detected.")

# --------------------------------------------------
# Merge
# --------------------------------------------------
cluster_fields = clusters[
    [
        "ward_code",
        "cluster_id",
        "cluster"
    ]
].copy()

result = wards.merge(
    cluster_fields,
    on="ward_code",
    how="left",
    validate="one_to_one"
)

# --------------------------------------------------
# Validation
# --------------------------------------------------
if result["cluster"].isna().any():
    raise ValueError("Some wards have no cluster assignment.")

if len(result) != 24:
    raise ValueError(
        f"Expected 24 wards, found {len(result)}"
    )

# --------------------------------------------------
# Save
# --------------------------------------------------
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

result.to_file(
    OUTPUT,
    driver="GeoJSON"
)

print("\nCluster distribution:")
print(
    result["cluster"]
    .value_counts()
    .sort_index()
    .to_string()
)

print("\nCRS:", result.crs)
print("Wards:", len(result))

print("\nSaved:")
print(OUTPUT)

print("\nGIS CLUSTER LAYER COMPLETE")

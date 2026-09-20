from pathlib import Path

import geopandas as gpd
import pandas as pd


# =========================================================
# URBANSIM — GIS ANOMALY LAYER
# =========================================================

BASE = Path(__file__).resolve().parents[1]

WARD_FILE = BASE / "data" / "spatial" / "mumbai_wards.geojson"
ANOMALY_FILE = BASE / "data" / "processed" / "urban_ward_anomaly_scores.csv"
EVIDENCE_FILE = (
    BASE / "data" / "processed"
    / "urban_ward_anomaly_feature_evidence.csv"
)

OUTPUT_FILE = (
    BASE / "data" / "spatial"
    / "mumbai_urban_anomalies.geojson"
)


print("=" * 60)
print("URBANSIM GIS ANOMALY LAYER")
print("=" * 60)


# ---------------------------------------------------------
# LOAD WARD POLYGONS
# ---------------------------------------------------------

wards = gpd.read_file(WARD_FILE)

print(f"\nWard polygons: {len(wards)}")


# ---------------------------------------------------------
# NORMALIZE WARD CODES
# ---------------------------------------------------------

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


wards["urban_ward_code"] = wards["NAME2"].apply(
    normalize_ward
)


# ---------------------------------------------------------
# LOAD ANOMALY SCORES
# ---------------------------------------------------------

anomalies = pd.read_csv(ANOMALY_FILE)

anomalies["ward_code"] = (
    anomalies["ward_code"]
    .astype(str)
    .str.strip()
    .str.upper()
)


# ---------------------------------------------------------
# TOP FEATURE EVIDENCE
# ---------------------------------------------------------

evidence = pd.read_csv(EVIDENCE_FILE)

evidence["ward_code"] = (
    evidence["ward_code"]
    .astype(str)
    .str.strip()
    .str.upper()
)

# Keep top 5 contributors per ward

top_evidence = (
    evidence
    .sort_values(
        ["ward_code", "feature_rank"]
    )
    .groupby("ward_code")
    .head(5)
)


# Create compact explanation text

explanation_records = []

for ward, group in top_evidence.groupby("ward_code"):

    features = group["feature"].tolist()

    explanation_records.append({
        "ward_code": ward,
        "top_anomaly_features": " | ".join(features)
    })


explanations = pd.DataFrame(
    explanation_records
)


# ---------------------------------------------------------
# MERGE
# ---------------------------------------------------------

result = wards.merge(
    anomalies,
    left_on="urban_ward_code",
    right_on="ward_code",
    how="left"
)

result = result.merge(
    explanations,
    left_on="urban_ward_code",
    right_on="ward_code",
    how="left",
    suffixes=("", "_evidence")
)


# ---------------------------------------------------------
# CLEAN COLUMNS
# ---------------------------------------------------------

if "ward_code_evidence" in result.columns:
    result = result.drop(
        columns=["ward_code_evidence"]
    )


# Ensure anomaly flag is boolean

result["anomaly_candidate"] = (
    result["anomaly_candidate"]
    .fillna(False)
    .astype(bool)
)


# ---------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------

print("\nValidation:")

print(
    f"Ward polygons: {len(result)}"
)

print(
    f"Anomaly records matched: "
    f"{result['reconstruction_mse'].notna().sum()}"
)

print(
    f"Anomaly candidates: "
    f"{result['anomaly_candidate'].sum()}"
)

print(
    f"CRS: {result.crs}"
)


missing_scores = result[
    result["reconstruction_mse"].isna()
]

if len(missing_scores) > 0:
    print(
        f"Wards without anomaly scores: "
        f"{len(missing_scores)}"
    )


# ---------------------------------------------------------
# SAVE
# ---------------------------------------------------------

result.to_file(
    OUTPUT_FILE,
    driver="GeoJSON"
)


print("\nSaved:")
print(OUTPUT_FILE)

print("\n" + "=" * 60)
print("GIS ANOMALY LAYER COMPLETE")
print("=" * 60)

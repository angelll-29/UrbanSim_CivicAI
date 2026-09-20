from pathlib import Path
import geopandas as gpd
import pandas as pd


# =========================================================
# URBANSIM — COMBINED INTELLIGENCE GIS LAYER
# =========================================================

BASE = Path(__file__).resolve().parents[1]

WARD_FILE = BASE / "data" / "spatial" / "mumbai_wards.geojson"
STRESS_FILE = BASE / "data" / "processed" / "mumbai_ward_domain_stress_v2.csv"
CLUSTER_FILE = BASE / "data" / "spatial" / "mumbai_ward_clusters.geojson"
ANOMALY_FILE = BASE / "data" / "processed" / "urban_ward_anomaly_scores.csv"
ANOMALY_EVIDENCE = BASE / "data" / "processed" / "urban_ward_anomaly_feature_evidence.csv"
SCENARIO_FILE = BASE / "data" / "processed" / "urban_scenario_results_v2.csv"

OUTPUT_FILE = BASE / "data" / "spatial" / "mumbai_urbansim_intelligence.geojson"


print("=" * 65)
print("URBANSIM COMBINED INTELLIGENCE GIS LAYER")
print("=" * 65)


# ---------------------------------------------------------
# LOAD
# ---------------------------------------------------------

wards = gpd.read_file(WARD_FILE)
stress = pd.read_csv(STRESS_FILE)
clusters = gpd.read_file(CLUSTER_FILE)
anomalies = pd.read_csv(ANOMALY_FILE)
evidence = pd.read_csv(ANOMALY_EVIDENCE)
scenarios = pd.read_csv(SCENARIO_FILE)


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


wards["ward_code"] = wards["NAME2"].apply(normalize_ward)

stress["ward_code"] = (
    stress["ward_code"]
    .astype(str)
    .str.strip()
    .str.upper()
)

clusters["ward_code"] = (
    clusters["ward_code"]
    .astype(str)
    .str.strip()
    .str.upper()
)

anomalies["ward_code"] = (
    anomalies["ward_code"]
    .astype(str)
    .str.strip()
    .str.upper()
)

evidence["ward_code"] = (
    evidence["ward_code"]
    .astype(str)
    .str.strip()
    .str.upper()
)

scenarios["ward_code"] = (
    scenarios["ward_code"]
    .astype(str)
    .str.strip()
    .str.upper()
)


# ---------------------------------------------------------
# STRESS FIELDS
# ---------------------------------------------------------

stress_keep = [
    "ward_code",
    "healthcare_stress",
    "education_stress",
    "sanitation_stress",
    "safety_stress",
    "transport_stress",
    "civic_stress",
    "green_space_stress",
]

# Find overall stress field
overall_candidates = [
    "urban_stress_index",
    "overall_stress",
    "overall_pressure",
]

overall_column = next(
    (
        c for c in overall_candidates
        if c in stress.columns
    ),
    None
)

if overall_column:
    stress_keep.append(overall_column)

stress_small = stress[
    [
        c for c in stress_keep
        if c in stress.columns
    ]
].copy()


# ---------------------------------------------------------
# CLUSTER
# ---------------------------------------------------------

cluster_keep = [
    "ward_code",
    "cluster_id",
    "cluster",
]

cluster_small = clusters[
    [
        c for c in cluster_keep
        if c in clusters.columns
    ]
].copy()


# ---------------------------------------------------------
# ANOMALY
# ---------------------------------------------------------

anomaly_keep = [
    "ward_code",
    "reconstruction_mse",
    "reconstruction_mae",
    "anomaly_percentile",
    "anomaly_candidate",
]

anomaly_small = anomalies[
    [
        c for c in anomaly_keep
        if c in anomalies.columns
    ]
].copy()


# ---------------------------------------------------------
# TOP ANOMALY FEATURES
# ---------------------------------------------------------

top_features = (
    evidence
    .sort_values(
        ["ward_code", "feature_rank"]
    )
    .groupby("ward_code")
    .head(5)
)

feature_text = (
    top_features
    .groupby("ward_code")["feature"]
    .apply(lambda x: " | ".join(x.astype(str)))
    .reset_index()
    .rename(
        columns={
            "feature":
                "top_anomaly_features"
        }
    )
)


# ---------------------------------------------------------
# SCENARIO SUMMARY
# ---------------------------------------------------------

best_scenario = (
    scenarios
    .sort_values(
        ["ward_code", "pressure_change"]
    )
    .groupby("ward_code")
    .head(1)
    [
        [
            "ward_code",
            "scenario",
            "pressure_change"
        ]
    ]
    .rename(
        columns={
            "scenario":
                "best_scenario",
            "pressure_change":
                "best_scenario_change"
        }
    )
)


# ---------------------------------------------------------
# MERGE ATTRIBUTES
# ---------------------------------------------------------

result = wards[
    [
        "ward_code",
        "geometry"
    ]
].copy()


result = result.merge(
    stress_small,
    on="ward_code",
    how="left"
)

result = result.merge(
    cluster_small,
    on="ward_code",
    how="left"
)

result = result.merge(
    anomaly_small,
    on="ward_code",
    how="left"
)

result = result.merge(
    feature_text,
    on="ward_code",
    how="left"
)

result = result.merge(
    best_scenario,
    on="ward_code",
    how="left"
)


# ---------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------

print("\nValidation")
print("-" * 40)

print(
    f"Ward polygons: {len(wards)}"
)

print(
    f"Combined records: {len(result)}"
)

print(
    f"Stress matches: "
    f"{result['healthcare_stress'].notna().sum()}"
)

print(
    f"Cluster matches: "
    f"{result['cluster'].notna().sum()}"
)

print(
    f"Anomaly matches: "
    f"{result['reconstruction_mse'].notna().sum()}"
)

print(
    f"Anomaly candidates: "
    f"{result['anomaly_candidate'].fillna(False).sum()}"
)

print(
    f"Scenario matches: "
    f"{result['best_scenario'].notna().sum()}"
)

print(
    f"CRS: {result.crs}"
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

print("\n" + "=" * 65)
print("COMBINED URBANSIM GIS LAYER COMPLETE")
print("=" * 65)

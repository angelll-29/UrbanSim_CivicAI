from pathlib import Path
import geopandas as gpd
import pandas as pd
import numpy as np

BASE = Path(__file__).resolve().parents[1]

WARD_FILE = BASE / "data/spatial/mumbai_wards.geojson"
STRESS_FILE = BASE / "data/processed/mumbai_ward_domain_stress_v2.csv"
CLUSTER_FILE = BASE / "data/spatial/mumbai_ward_clusters.geojson"
ANOMALY_FILE = BASE / "data/processed/urban_ward_anomaly_scores.csv"
EVIDENCE_FILE = BASE / "data/processed/urban_ward_anomaly_feature_evidence.csv"
SCENARIO_FILE = BASE / "data/processed/urban_scenario_results_v2.csv"

OUTPUT_FILE = BASE / "data/spatial/mumbai_urbansim_intelligence.geojson"

print("=" * 70)
print("URBANSIM — INTERACTIVE GIS INTELLIGENCE LAYER")
print("=" * 70)


# ---------------------------------------------------------
# LOAD
# ---------------------------------------------------------

wards = gpd.read_file(WARD_FILE)
stress = pd.read_csv(STRESS_FILE)
clusters = gpd.read_file(CLUSTER_FILE)
anomalies = pd.read_csv(ANOMALY_FILE)
evidence = pd.read_csv(EVIDENCE_FILE)
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

for data in [stress, anomalies, evidence, scenarios]:
    data["ward_code"] = (
        data["ward_code"]
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


# ---------------------------------------------------------
# STRESS
# ---------------------------------------------------------

stress_columns = [
    "ward_code",
    "healthcare_stress",
    "education_stress",
    "sanitation_stress",
    "safety_stress",
    "transport_stress",
    "civic_stress",
    "green_space_stress",
]

stress_columns = [
    c for c in stress_columns
    if c in stress.columns
]

stress_data = stress[stress_columns].copy()

# Find overall stress field
for candidate in [
    "urban_stress_index",
    "overall_stress",
    "overall_pressure",
]:
    if candidate in stress.columns:
        stress_data["urban_stress"] = stress[candidate]
        break


# ---------------------------------------------------------
# CLUSTERS
# ---------------------------------------------------------

cluster_data = clusters[
    [
        c for c in [
            "ward_code",
            "cluster_id",
            "cluster"
        ]
        if c in clusters.columns
    ]
].copy()


# ---------------------------------------------------------
# ANOMALIES
# ---------------------------------------------------------

anomaly_data = anomalies[
    [
        c for c in [
            "ward_code",
            "reconstruction_mse",
            "reconstruction_mae",
            "anomaly_percentile",
            "anomaly_candidate"
        ]
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

feature_lookup = (
    top_features
    .groupby("ward_code")["feature"]
    .apply(
        lambda x: " | ".join(
            x.astype(str)
        )
    )
    .reset_index()
)

feature_lookup = feature_lookup.rename(
    columns={
        "feature": "top_anomaly_features"
    }
)


# ---------------------------------------------------------
# SCENARIO SUMMARY
# ---------------------------------------------------------

# Most pressure-reducing scenario per ward
best_scenario = (
    scenarios
    .sort_values(
        ["ward_code", "pressure_change"]
    )
    .groupby("ward_code")
    .first()
    .reset_index()
)

best_scenario = best_scenario[
    [
        "ward_code",
        "scenario",
        "pressure_change"
    ]
].rename(
    columns={
        "scenario": "best_scenario",
        "pressure_change": "best_scenario_change"
    }
)


# ---------------------------------------------------------
# GEOMETRY + ATTRIBUTES
# ---------------------------------------------------------

result = wards[
    [
        "ward_code",
        "geometry"
    ]
].copy()


result = result.merge(
    stress_data,
    on="ward_code",
    how="left"
)

result = result.merge(
    cluster_data,
    on="ward_code",
    how="left"
)

result = result.merge(
    anomaly_data,
    on="ward_code",
    how="left"
)

result = result.merge(
    feature_lookup,
    on="ward_code",
    how="left"
)

result = result.merge(
    best_scenario,
    on="ward_code",
    how="left"
)


# ---------------------------------------------------------
# INTERACTIVE GIS FIELDS
# ---------------------------------------------------------

# Human-readable anomaly status
result["anomaly_status"] = np.where(
    result["anomaly_candidate"].fillna(False),
    "Anomaly Candidate",
    "No Anomaly Candidate"
)


# Stress presentation band
def stress_band(value):
    if pd.isna(value):
        return "No Data"
    if value < 20:
        return "Very Low"
    if value < 40:
        return "Low"
    if value < 60:
        return "Moderate"
    if value < 80:
        return "High"
    return "Very High"


result["stress_band"] = (
    result["urban_stress"]
    .apply(stress_band)
)


# Create a compact ward popup summary
result["ward_summary"] = (
    "Ward "
    + result["ward_code"].astype(str)
    + " | Urban Stress: "
    + result["urban_stress"].round(2).astype(str)
    + " | "
    + result["stress_band"]
)


# ---------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------

print("\nVALIDATION")
print("-" * 50)

print(f"Ward polygons: {len(wards)}")
print(f"Final GIS records: {len(result)}")
print(
    f"Stress matched: "
    f"{result['urban_stress'].notna().sum()}"
)
print(
    f"Clusters matched: "
    f"{result['cluster'].notna().sum()}"
)
print(
    f"Anomaly scores matched: "
    f"{result['reconstruction_mse'].notna().sum()}"
)
print(
    f"Anomaly candidates: "
    f"{result['anomaly_candidate'].fillna(False).sum()}"
)
print(
    f"Scenario records matched: "
    f"{result['best_scenario'].notna().sum()}"
)
print(f"CRS: {result.crs}")


# Exact ward coverage
expected = set(stress["ward_code"])
actual = set(result["ward_code"])

missing = expected - actual
extra = actual - expected

print(f"Missing wards: {sorted(missing)}")
print(f"Unexpected wards: {sorted(extra)}")


if len(result) != 24:
    raise ValueError(
        "Expected exactly 24 BMC ward records."
    )

if missing:
    raise ValueError(
        f"Missing ward records: {missing}"
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

print("\n" + "=" * 70)
print("INTERACTIVE GIS DATA BACKBONE COMPLETE")
print("=" * 70)

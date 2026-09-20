import geopandas as gpd
import pandas as pd
from pathlib import Path

WARD_FILE = Path("data/spatial/mumbai_wards.geojson")
STRESS_FILE = Path("data/processed/mumbai_ward_domain_stress_v2.csv")
OUTPUT = Path("data/spatial/mumbai_urban_stress_v2.geojson")

# ---------------------------------------------------------
# Load data
# ---------------------------------------------------------
wards = gpd.read_file(WARD_FILE)
stress = pd.read_csv(STRESS_FILE)

print("Ward polygons:", len(wards))
print("Stress records:", len(stress))


# ---------------------------------------------------------
# Normalize source BMC ward codes
# ---------------------------------------------------------
WARD_MAP = {
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


def normalize_ward(value):
    if pd.isna(value):
        return None

    value = str(value).strip()

    return WARD_MAP.get(value, value)


wards["ward_code"] = wards["NAME2"].apply(normalize_ward)


# ---------------------------------------------------------
# Validate ward codes
# ---------------------------------------------------------
print("\nGIS ward codes:")
print(sorted(wards["ward_code"].dropna().unique()))

print("\nStress ward codes:")
print(sorted(stress["ward_code"].dropna().unique()))

if wards["ward_code"].duplicated().any():
    duplicates = wards[
        wards["ward_code"].duplicated(keep=False)
    ]["ward_code"].tolist()

    raise ValueError(
        f"Duplicate GIS ward codes detected: {duplicates}"
    )

if stress["ward_code"].duplicated().any():
    raise ValueError(
        "Duplicate stress ward codes detected"
    )


gis_codes = set(wards["ward_code"])
stress_codes = set(stress["ward_code"])

missing_in_gis = stress_codes - gis_codes
missing_in_stress = gis_codes - stress_codes

if missing_in_gis:
    raise ValueError(
        f"Wards missing from GIS: {sorted(missing_in_gis)}"
    )

if missing_in_stress:
    raise ValueError(
        f"Wards missing from stress data: {sorted(missing_in_stress)}"
    )


# ---------------------------------------------------------
# Select analytical fields
# ---------------------------------------------------------
stress_columns = [
    "urban_stress_index",
    "urban_stress_band",

    "healthcare_stress",
    "education_stress",
    "sanitation_stress",
    "safety_stress",
    "transport_stress",
    "civic_stress",
    "green_space_stress",

    "healthcare_coverage_pct",
    "education_coverage_pct",
    "sanitation_coverage_pct",
    "safety_coverage_pct",
    "transport_coverage_pct",
    "civic_coverage_pct",
    "green_space_coverage_pct",

    "urban_stress_domain_count",
    "urban_stress_domain_coverage_pct",
]

stress_columns = [
    c for c in stress_columns
    if c in stress.columns
]


# ---------------------------------------------------------
# Merge stress results onto ward polygons
# ---------------------------------------------------------
stress_subset = stress[
    ["ward_code"] + stress_columns
].copy()

gis = wards.merge(
    stress_subset,
    on="ward_code",
    how="left",
    validate="one_to_one"
)


# ---------------------------------------------------------
# Final validation
# ---------------------------------------------------------
if len(gis) != 24:
    raise ValueError(
        f"Expected 24 GIS wards, found {len(gis)}"
    )

if gis["urban_stress_index"].isna().any():
    missing = gis.loc[
        gis["urban_stress_index"].isna(),
        "ward_code"
    ].tolist()

    raise ValueError(
        f"Missing stress scores for wards: {missing}"
    )

if gis.crs is None:
    raise ValueError("GIS layer has no CRS")

print("\nCRS:", gis.crs)

# ---------------------------------------------------------
# Save GeoJSON
# ---------------------------------------------------------
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

gis.to_file(
    OUTPUT,
    driver="GeoJSON"
)

print("\nUrban Stress GIS Layer Complete")
print("--------------------------------")
print("Wards:", len(gis))
print("CRS:", gis.crs)
print("Stress fields:", len(stress_columns))

print("\nStress range:")
print(
    f"  Min: {gis['urban_stress_index'].min():.2f}"
)
print(
    f"  Max: {gis['urban_stress_index'].max():.2f}"
)

print("\nOutput:")
print(OUTPUT)

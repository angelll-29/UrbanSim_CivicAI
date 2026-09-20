import pandas as pd
import numpy as np
from pathlib import Path

INPUT = Path("data/processed/mumbai_ward_normalized_indicators.csv")
OUTPUT = Path("data/processed/mumbai_ward_domain_stress_v2.csv")

df = pd.read_csv(INPUT)

# ---------------------------------------------------------
# Correlation-adjusted indicator groups
# One representative indicator is retained where
# multiple indicators measure the same underlying concept.
# ---------------------------------------------------------
DOMAINS = {
    "healthcare": [
        "population_per_healthcare_facility_stress",
    ],

    "education": [
        "students_per_school_stress",
        "classrooms_per_100_students_stress",
        "classrooms_repair_pct_stress",
    ],

    "sanitation": [
        "population_per_public_toilet_stress",
    ],

    "safety": [
        "population_per_police_station_stress",
        "population_per_fire_station_stress",
    ],

    "transport": [
        "transport_nodes_per_100k_stress",
        "transport_nodes_per_km2_stress",
    ],

    "civic": [
        "complaints_per_1000_population_stress",
        "unresolved_per_1000_population_stress",
        "avg_resolution_days_2024_stress",
    ],

    "green_space": [
        "green_spaces_per_km2_stress",
        "green_spaces_per_100k_population_stress",
    ],
}


result = df[
    [
        "ward_code",
        "population_2011",
        "area_sq_km",
        "population_density_per_sq_km",
    ]
].copy()


# ---------------------------------------------------------
# Domain scores
# Equal weighting within each domain.
# ---------------------------------------------------------
for domain, indicators in DOMAINS.items():

    missing = [
        col for col in indicators
        if col not in df.columns
    ]

    if missing:
        raise ValueError(
            f"{domain} missing indicators: {missing}"
        )

    result[f"{domain}_stress"] = df[indicators].mean(
        axis=1,
        skipna=True
    )

    result[f"{domain}_indicator_count"] = (
        df[indicators].notna().sum(axis=1)
    )

    result[f"{domain}_indicator_total"] = len(indicators)

    result[f"{domain}_coverage_pct"] = (
        result[f"{domain}_indicator_count"]
        / len(indicators)
        * 100
    )


# ---------------------------------------------------------
# Overall Urban Stress Index
#
# Equal weighting across the 7 domains prevents domains
# with more indicators from dominating the composite.
# ---------------------------------------------------------
domain_columns = [
    "healthcare_stress",
    "education_stress",
    "sanitation_stress",
    "safety_stress",
    "transport_stress",
    "civic_stress",
    "green_space_stress",
]

result["urban_stress_index"] = result[
    domain_columns
].mean(axis=1, skipna=True)

result["urban_stress_domain_count"] = result[
    domain_columns
].notna().sum(axis=1)

result["urban_stress_domain_coverage_pct"] = (
    result["urban_stress_domain_count"]
    / len(domain_columns)
    * 100
)


# ---------------------------------------------------------
# Presentation bands
# These are relative presentation bands, not official
# risk thresholds.
# ---------------------------------------------------------
def stress_band(value):

    if pd.isna(value):
        return "Insufficient Data"

    if value < 20:
        return "Very Low"

    if value < 40:
        return "Low"

    if value < 60:
        return "Moderate"

    if value < 80:
        return "High"

    return "Very High"


result["urban_stress_band"] = (
    result["urban_stress_index"]
    .apply(stress_band)
)


# ---------------------------------------------------------
# Validation
# ---------------------------------------------------------
if len(result) != 24:
    raise ValueError(
        f"Expected 24 wards, found {len(result)}"
    )

if result["ward_code"].duplicated().any():
    raise ValueError("Duplicate ward codes detected")

valid_index = result["urban_stress_index"].dropna()

if valid_index.min() < 0 or valid_index.max() > 100:
    raise ValueError(
        "Urban Stress Index outside 0-100 range"
    )


# ---------------------------------------------------------
# Save
# ---------------------------------------------------------
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
result.to_csv(OUTPUT, index=False)

print("\nUrban Domain Stress Model V2 Complete")
print("--------------------------------------")
print(f"Wards: {len(result)}")
print(f"Domains: {len(domain_columns)}")
print("Indicators used: 15")

print("\nDomain coverage:")

for domain in DOMAINS:
    print(
        f"  {domain:<15} "
        f"{result[f'{domain}_coverage_pct'].mean():6.1f}% average"
    )

print("\nUrban Stress Index V2:")
print(f"  Minimum: {valid_index.min():.2f}")
print(f"  Maximum: {valid_index.max():.2f}")
print(f"  Mean:    {valid_index.mean():.2f}")

print("\nStress bands:")
print(
    result["urban_stress_band"]
    .value_counts()
    .to_string()
)

print("\nOutput:")
print(OUTPUT)

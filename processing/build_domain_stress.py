import pandas as pd
import numpy as np
from pathlib import Path

INPUT = Path("data/processed/mumbai_ward_normalized_indicators.csv")
OUTPUT = Path("data/processed/mumbai_ward_domain_stress.csv")

df = pd.read_csv(INPUT)

# ---------------------------------------------------------
# Domain definitions
# ---------------------------------------------------------
DOMAINS = {
    "healthcare": [
        "population_per_healthcare_facility_stress",
        "healthcare_facilities_per_100k_stress",
    ],

    "education": [
        "students_per_school_stress",
        "classrooms_per_100_students_stress",
        "classrooms_repair_pct_stress",
    ],

    "sanitation": [
        "population_per_public_toilet_stress",
        "facilities_per_10000_population_stress",
    ],

    "safety": [
        "population_per_police_station_stress",
        "police_stations_per_100k_stress",
        "population_per_fire_station_stress",
        "fire_stations_per_100k_stress",
    ],

    "transport": [
        "transport_nodes_per_100k_stress",
        "transport_nodes_per_km2_stress",
    ],

    "civic": [
        "complaints_per_1000_population_stress",
        "unresolved_per_1000_population_stress",
        "closure_pct_2024_stress",
        "avg_resolution_days_2024_stress",
    ],

    "green_space": [
        "green_spaces_per_km2_stress",
        "green_spaces_per_100k_population_stress",
    ],
}


result = df[[
    "ward_code",
    "population_2011",
    "area_sq_km",
    "population_density_per_sq_km"
]].copy()


# ---------------------------------------------------------
# Calculate domain scores
# ---------------------------------------------------------
for domain, indicators in DOMAINS.items():

    available = [
        col for col in indicators
        if col in df.columns
    ]

    if not available:
        raise ValueError(
            f"No indicators available for domain: {domain}"
        )

    # Equal weight within domain
    result[f"{domain}_stress"] = df[available].mean(
        axis=1,
        skipna=True
    )

    # Number of valid indicators
    result[f"{domain}_indicator_count"] = df[available].notna().sum(
        axis=1
    )

    # Total expected indicators
    result[f"{domain}_indicator_total"] = len(available)

    # Coverage percentage
    result[f"{domain}_coverage_pct"] = (
        result[f"{domain}_indicator_count"]
        / result[f"{domain}_indicator_total"]
        * 100
    )


# ---------------------------------------------------------
# Overall Urban Stress
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

# Equal weighting across domains.
# This prevents domains with more indicators from dominating.
result["urban_stress_index"] = result[domain_columns].mean(
    axis=1,
    skipna=True
)

result["urban_stress_domain_count"] = result[domain_columns].notna().sum(
    axis=1
)

result["urban_stress_domain_coverage_pct"] = (
    result["urban_stress_domain_count"] /
    len(domain_columns) *
    100
)


# ---------------------------------------------------------
# Stress bands
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


result["urban_stress_band"] = result[
    "urban_stress_index"
].apply(stress_band)


# ---------------------------------------------------------
# Validation
# ---------------------------------------------------------
if len(result) != 24:
    raise ValueError(
        f"Expected 24 wards, found {len(result)}"
    )

if result["ward_code"].duplicated().any():
    raise ValueError("Duplicate ward codes detected")

if result["urban_stress_index"].dropna().min() < 0:
    raise ValueError("Urban Stress Index below 0")

if result["urban_stress_index"].dropna().max() > 100:
    raise ValueError("Urban Stress Index above 100")


# ---------------------------------------------------------
# Save
# ---------------------------------------------------------
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
result.to_csv(OUTPUT, index=False)

print("\nUrban Domain Stress Model Complete")
print("-----------------------------------")
print(f"Wards: {len(result)}")

print("\nDomain coverage:")

for domain in DOMAINS:
    coverage = result[f"{domain}_coverage_pct"]

    print(
        f"  {domain:<15} "
        f"{coverage.mean():6.1f}% average"
    )

print("\nUrban Stress Index:")
print(
    f"  Minimum: {result['urban_stress_index'].min():.2f}"
)

print(
    f"  Maximum: {result['urban_stress_index'].max():.2f}"
)

print(
    f"  Mean:    {result['urban_stress_index'].mean():.2f}"
)

print("\nStress bands:")
print(
    result["urban_stress_band"]
    .value_counts()
    .to_string()
)

print("\nOutput:")
print(OUTPUT)

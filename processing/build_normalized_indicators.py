import pandas as pd
import numpy as np
from pathlib import Path

INPUT = Path("data/processed/mumbai_ward_infrastructure_stress.csv")
OUTPUT = Path("data/processed/mumbai_ward_normalized_indicators.csv")

df = pd.read_csv(INPUT)

# ---------------------------------------------------------
# Indicator definitions
#
# True  = higher raw value means higher stress
# False = higher raw value means lower stress
# ---------------------------------------------------------
INDICATORS = {
    # Healthcare
    "population_per_healthcare_facility": True,
    "healthcare_facilities_per_100k": False,

    # Education
    "students_per_school": True,
    "classrooms_per_100_students": False,
    "classrooms_repair_pct": True,

    # Sanitation
    "population_per_public_toilet": True,
    "facilities_per_10000_population": False,

    # Police
    "population_per_police_station": True,
    "police_stations_per_100k": False,

    # Fire
    "population_per_fire_station": True,
    "fire_stations_per_100k": False,

    # Transport
    "transport_nodes_per_100k": False,
    "transport_nodes_per_km2": False,

    # Civic
    "complaints_per_1000_population": True,
    "unresolved_per_1000_population": True,
    "closure_pct_2024": False,
    "avg_resolution_days_2024": True,

    # Green space
    "green_spaces_per_km2": False,
    "green_spaces_per_100k_population": False,
}


def percentile_stress(series, higher_is_stress):
    """
    Convert a raw indicator to 0-100 percentile stress.

    rank(pct=True) gives:
        lowest value  -> ~0
        highest value -> 100

    Missing values remain NaN.
    """
    numeric = pd.to_numeric(series, errors="coerce")

    if higher_is_stress:
        stress = numeric.rank(method="average", pct=True) * 100
    else:
        stress = (1 - numeric.rank(method="average", pct=True)) * 100

    return stress


# ---------------------------------------------------------
# Create normalized indicators
# ---------------------------------------------------------
normalized = df[["ward_code"]].copy()

for indicator, higher_is_stress in INDICATORS.items():

    if indicator not in df.columns:
        print(f"WARNING: Missing indicator: {indicator}")
        continue

    normalized[f"{indicator}_stress"] = percentile_stress(
        df[indicator],
        higher_is_stress
    )


# ---------------------------------------------------------
# Add raw indicators for traceability
# ---------------------------------------------------------
raw_columns = [
    "population_2011",
    "area_sq_km",
    "population_density_per_sq_km",

    "population_per_healthcare_facility",
    "healthcare_facilities_per_100k",

    "students_per_school",
    "classrooms_per_100_students",
    "classrooms_repair_pct",

    "population_per_public_toilet",
    "facilities_per_10000_population",

    "population_per_police_station",
    "police_stations_per_100k",

    "population_per_fire_station",
    "fire_stations_per_100k",

    "transport_nodes_per_100k",
    "transport_nodes_per_km2",

    "complaints_per_1000_population",
    "unresolved_per_1000_population",
    "closure_pct_2024",
    "avg_resolution_days_2024",

    "green_spaces_per_km2",
    "green_spaces_per_100k_population",
]

raw_columns = [
    c for c in raw_columns
    if c in df.columns
]

for col in raw_columns:
    normalized[col] = df[col]


# ---------------------------------------------------------
# Validation
# ---------------------------------------------------------
if len(normalized) != 24:
    raise ValueError(
        f"Expected 24 wards, found {len(normalized)}"
    )

if normalized["ward_code"].duplicated().any():
    raise ValueError("Duplicate ward codes detected")


stress_columns = [
    c for c in normalized.columns
    if c.endswith("_stress")
]

# Verify stress values
for col in stress_columns:
    valid = normalized[col].dropna()

    if len(valid) > 0:
        if valid.min() < 0 or valid.max() > 100:
            raise ValueError(
                f"Invalid normalized range in {col}"
            )


# ---------------------------------------------------------
# Save
# ---------------------------------------------------------
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
normalized.to_csv(OUTPUT, index=False)

print("\nNormalization Layer Complete")
print("--------------------------------")
print(f"Wards:             {len(normalized)}")
print(f"Raw indicators:    {len(raw_columns)}")
print(f"Stress indicators: {len(stress_columns)}")

print("\nStress indicator coverage:")

for col in stress_columns:
    valid = normalized[col].notna().sum()
    print(f"  {col}: {valid}/24")

print("\nOutput:")
print(OUTPUT)

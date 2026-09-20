import pandas as pd
from pathlib import Path

INPUT = Path("data/processed/mumbai_ward_civic_intelligence_base_environment.csv")
OUTPUT = Path("data/processed/urban_ai_features.csv")

FEATURES = [
    # Population / urban form
    "population_2011",
    "population_density_per_sq_km",
    "area_sq_km",

    # Education
    "udise_city_schools",
    "students_total",
    "teachers_total",
    "teacher_student_ratio",
    "classrooms_repair_pct",
    "girls_share_pct",

    # Healthcare
    "healthcare_facilities",
    "hospitals",
    "dispensaries",
    "uphcs",

    # Civic
    "complaints_received_2024",
    "unresolved_complaints_2024",
    "closure_pct_2024",
    "avg_resolution_days_2024",

    # Green space
    "green_space_count",
    "green_space_share_pct",
    "green_spaces_per_km2",

    # Transport
    "bus_stop_count",
    "railway_station_count",
    "metro_station_count",
    "monorail_station_count",
    "total_public_transport_nodes",

    # Sanitation
    "public_toilet_count",
    "facilities_per_10000_population",

    # Safety
    "fire_station_count",
    "police_station_count",
]

df = pd.read_csv(INPUT)

required = ["ward_code"] + FEATURES
missing = [c for c in required if c not in df.columns]

if missing:
    raise ValueError(f"Missing columns: {missing}")

ai = df[required].copy()

# Convert feature columns to numeric
for col in FEATURES:
    ai[col] = pd.to_numeric(ai[col], errors="coerce")

print("UrbanSim AI Feature Dataset")
print("-" * 50)
print("Rows:", len(ai))
print("Features:", len(FEATURES))
print("\nMissing values:")
print(ai[FEATURES].isna().sum())

print("\nFeature ranges:")
print(ai[FEATURES].describe().T[["min", "max", "mean"]].to_string())

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
ai.to_csv(OUTPUT, index=False)

print("\nSaved:", OUTPUT)
print("Shape:", ai.shape)

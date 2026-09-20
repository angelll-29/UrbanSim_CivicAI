import pandas as pd
import numpy as np
from pathlib import Path

INPUT = Path("data/processed/mumbai_ward_civic_intelligence_base_environment.csv")
OUTPUT = Path("data/processed/mumbai_ward_infrastructure_stress.csv")

df = pd.read_csv(INPUT)

# ---------------------------------------------------------
# Helper
# ---------------------------------------------------------
def safe_divide(numerator, denominator):
    numerator = pd.to_numeric(numerator, errors="coerce")
    denominator = pd.to_numeric(denominator, errors="coerce")
    return numerator.div(denominator.replace(0, np.nan))


# ---------------------------------------------------------
# Healthcare
# ---------------------------------------------------------
df["population_per_healthcare_facility"] = safe_divide(
    df["population_2011"],
    df["healthcare_facilities"]
)

df["healthcare_facilities_per_100k"] = safe_divide(
    df["healthcare_facilities"] * 100000,
    df["population_2011"]
)


# ---------------------------------------------------------
# Education
# ---------------------------------------------------------
df["students_per_school"] = safe_divide(
    df["students_total"],
    df["udise_city_schools"]
)

df["classrooms_per_100_students"] = safe_divide(
    df["classrooms_total_observed"] * 100,
    df["students_total"]
)

# Preserve existing UDISE indicators
# teacher_student_ratio
# classrooms_repair_pct


# ---------------------------------------------------------
# Sanitation
# ---------------------------------------------------------
df["population_per_public_toilet"] = safe_divide(
    df["population_2011"],
    df["public_toilet_count"]
)

df["facilities_per_10000_population"] = safe_divide(
    df["total_toilet_facilities"] * 10000,
    df["population_2011"]
)


# ---------------------------------------------------------
# Police
# ---------------------------------------------------------
df["population_per_police_station"] = safe_divide(
    df["population_2011"],
    df["police_station_count"]
)

df["police_stations_per_100k"] = safe_divide(
    df["police_station_count"] * 100000,
    df["population_2011"]
)


# ---------------------------------------------------------
# Fire
# ---------------------------------------------------------
df["population_per_fire_station"] = safe_divide(
    df["population_2011"],
    df["fire_station_count"]
)

df["fire_stations_per_100k"] = safe_divide(
    df["fire_station_count"] * 100000,
    df["population_2011"]
)


# ---------------------------------------------------------
# Public Transport
# ---------------------------------------------------------
df["transport_nodes_per_100k"] = safe_divide(
    df["total_public_transport_nodes"] * 100000,
    df["population_2011"]
)

df["transport_nodes_per_km2"] = safe_divide(
    df["total_public_transport_nodes"],
    df["area_sq_km"]
)


# ---------------------------------------------------------
# Civic complaints
# ---------------------------------------------------------
df["complaints_per_1000_population"] = safe_divide(
    df["complaints_received_2024"] * 1000,
    df["population_2011"]
)

df["unresolved_per_1000_population"] = safe_divide(
    df["unresolved_complaints_2024"] * 1000,
    df["population_2011"]
)


# ---------------------------------------------------------
# Green space
# ---------------------------------------------------------
# Already calculated in environmental integration:
# green_spaces_per_km2
# green_spaces_per_100k_population


# ---------------------------------------------------------
# Select analytical columns
# ---------------------------------------------------------
base_columns = [
    "ward_code",

    # Population / geography
    "population_2011",
    "area_sq_km",
    "population_density_per_sq_km",

    # Healthcare
    "healthcare_facilities",
    "population_per_healthcare_facility",
    "healthcare_facilities_per_100k",

    # Education
    "udise_city_schools",
    "students_total",
    "teachers_total",
    "students_per_school",
    "classrooms_total_observed",
    "classrooms_per_100_students",
    "teacher_student_ratio",
    "classrooms_repair_pct",

    # Sanitation
    "public_toilet_count",
    "total_toilet_facilities",
    "population_per_public_toilet",
    "facilities_per_10000_population",

    # Police
    "police_station_count",
    "population_per_police_station",
    "police_stations_per_100k",

    # Fire
    "fire_station_count",
    "population_per_fire_station",
    "fire_stations_per_100k",

    # Transport
    "total_public_transport_nodes",
    "bus_stop_count",
    "railway_station_count",
    "total_metro_monorail_stations",
    "transport_nodes_per_100k",
    "transport_nodes_per_km2",

    # Civic
    "complaints_received_2024",
    "complaints_closed_2024",
    "unresolved_complaints_2024",
    "closure_pct_2024",
    "avg_resolution_days_2024",
    "complaints_per_1000_population",
    "unresolved_per_1000_population",

    # Environment
    "green_space_count",
    "green_space_share_pct",
    "green_spaces_per_km2",
    "green_spaces_per_100k_population",

    # Air quality + monitoring metadata
    "pm25",
    "pm10",
    "no2",
    "so2",
    "o3",
    "co",
    "recent_measurement_count",
    "environmental_station_presence",
]

# Keep only columns that actually exist
output_columns = [
    c for c in base_columns
    if c in df.columns
]

result = df[output_columns].copy()

# ---------------------------------------------------------
# Validation
# ---------------------------------------------------------
if len(result) != 24:
    raise ValueError(
        f"Expected 24 wards, found {len(result)}"
    )

if result["ward_code"].duplicated().any():
    raise ValueError("Duplicate ward codes detected")

# Save
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
result.to_csv(OUTPUT, index=False)

print("\nInfrastructure Indicator Layer Complete")
print("----------------------------------------")
print(f"Rows:    {len(result)}")
print(f"Columns: {len(result.columns)}")

print("\nOutput:")
print(OUTPUT)

print("\nDerived indicators:")
for col in [
    "population_per_healthcare_facility",
    "healthcare_facilities_per_100k",
    "students_per_school",
    "classrooms_per_100_students",
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
]:
    if col in result.columns:
        valid = result[col].notna().sum()
        print(f"  {col}: {valid}/24 valid")

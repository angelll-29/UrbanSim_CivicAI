import pandas as pd
import numpy as np

INPUT_NORMALIZED = "data/processed/mumbai_ward_normalized_indicators.csv"
INPUT_STRESS = "data/processed/mumbai_ward_domain_stress_v2.csv"
OUTPUT = "data/processed/mumbai_ward_intervention_evidence.csv"

normalized = pd.read_csv(INPUT_NORMALIZED)
stress = pd.read_csv(INPUT_STRESS)

# ---------------------------------------------------------
# Indicator -> domain mapping
# ---------------------------------------------------------
indicator_domains = {
    "population_per_healthcare_facility_stress": "Healthcare",

    "students_per_school_stress": "Education",
    "classrooms_per_100_students_stress": "Education",
    "classrooms_repair_pct_stress": "Education",

    "population_per_public_toilet_stress": "Sanitation",

    "population_per_police_station_stress": "Safety",
    "population_per_fire_station_stress": "Safety",

    "transport_nodes_per_100k_population_stress": "Transport",
    "transport_nodes_per_km2_stress": "Transport",

    "complaints_per_1000_population_stress": "Civic",
    "unresolved_per_1000_population_stress": "Civic",
    "avg_resolution_days_2024_stress": "Civic",

    "green_spaces_per_km2_stress": "Green Space",
    "green_spaces_per_100k_population_stress": "Green Space",
}

# ---------------------------------------------------------
# Find priority domain for each ward
# ---------------------------------------------------------
domain_columns = {
    "Healthcare": "healthcare_stress",
    "Education": "education_stress",
    "Sanitation": "sanitation_stress",
    "Safety": "safety_stress",
    "Transport": "transport_stress",
    "Civic": "civic_stress",
    "Green Space": "green_space_stress",
}

priority_domain = {}

for _, row in stress.iterrows():
    values = {
        domain: row[column]
        for domain, column in domain_columns.items()
        if pd.notna(row[column])
    }

    if values:
        priority_domain[row["ward_code"]] = max(
            values,
            key=values.get
        )
    else:
        priority_domain[row["ward_code"]] = "Insufficient Data"

# ---------------------------------------------------------
# Convert normalized indicators into long format
# ---------------------------------------------------------
rows = []

for _, ward in normalized.iterrows():

    ward_code = ward["ward_code"]
    domain = priority_domain.get(
        ward_code,
        "Insufficient Data"
    )

    for indicator, indicator_domain in indicator_domains.items():

        if indicator_domain != domain:
            continue

        if indicator not in normalized.columns:
            continue

        value = ward[indicator]

        if pd.isna(value):
            continue

        rows.append({
            "ward_code": ward_code,
            "priority_domain": domain,
            "indicator": indicator,
            "normalized_stress": value,
        })

evidence = pd.DataFrame(rows)

# ---------------------------------------------------------
# Rank indicators within each priority domain
# ---------------------------------------------------------
if not evidence.empty:

    evidence["indicator_rank_within_domain"] = (
        evidence
        .groupby("priority_domain")["normalized_stress"]
        .rank(
            method="min",
            ascending=False
        )
        .astype(int)
    )

    # Highest indicator = primary evidence
    evidence["evidence_level"] = np.where(
        evidence["indicator_rank_within_domain"] == 1,
        "Primary",
        "Supporting"
    )

# ---------------------------------------------------------
# Human-readable indicator names
# ---------------------------------------------------------
indicator_names = {
    "population_per_healthcare_facility_stress":
        "Population per healthcare facility",

    "students_per_school_stress":
        "Students per school",

    "classrooms_per_100_students_stress":
        "Classrooms per 100 students",

    "classrooms_repair_pct_stress":
        "Classrooms requiring repair",

    "population_per_public_toilet_stress":
        "Population per public toilet",

    "population_per_police_station_stress":
        "Population per police station",

    "population_per_fire_station_stress":
        "Population per fire station",

    "transport_nodes_per_100k_population_stress":
        "Transport nodes per 100,000 population",

    "transport_nodes_per_km2_stress":
        "Transport nodes per km²",

    "complaints_per_1000_population_stress":
        "Civic complaints per 1,000 population",

    "unresolved_per_1000_population_stress":
        "Unresolved complaints per 1,000 population",

    "avg_resolution_days_2024_stress":
        "Average complaint resolution days",

    "green_spaces_per_km2_stress":
        "Green spaces per km²",

    "green_spaces_per_100k_population_stress":
        "Green spaces per 100,000 population",
}

evidence["indicator_name"] = (
    evidence["indicator"]
    .map(indicator_names)
    .fillna(evidence["indicator"])
)

# ---------------------------------------------------------
# Save
# ---------------------------------------------------------
columns = [
    "ward_code",
    "priority_domain",
    "indicator_rank_within_domain",
    "evidence_level",
    "indicator_name",
    "indicator",
    "normalized_stress",
]

evidence = evidence[columns]

evidence.to_csv(
    OUTPUT,
    index=False
)

print("========================================")
print("INTERVENTION EVIDENCE COMPLETE")
print("========================================")

print(f"Evidence records: {len(evidence)}")
print(f"Wards covered: {evidence['ward_code'].nunique()}")

print("\nPriority domains:")
print(
    evidence[
        ["ward_code", "priority_domain"]
    ]
    .drop_duplicates()["priority_domain"]
    .value_counts()
)

print("\nPrimary evidence by ward:")

print(
    evidence[
        evidence["evidence_level"] == "Primary"
    ][
        [
            "ward_code",
            "priority_domain",
            "indicator_name",
            "normalized_stress",
        ]
    ]
    .sort_values(
        ["ward_code", "normalized_stress"],
        ascending=[True, False]
    )
    .to_string(index=False)
)

print(f"\nSaved: {OUTPUT}")

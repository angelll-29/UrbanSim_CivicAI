import pandas as pd
import numpy as np

INPUT_STRESS = "data/processed/mumbai_ward_domain_stress_v2.csv"
INPUT_SPATIAL = "data/processed/mumbai_urban_stress_spatial_stats.csv"
OUTPUT = "data/processed/mumbai_ward_priority_interventions.csv"

stress = pd.read_csv(INPUT_STRESS)
spatial = pd.read_csv(INPUT_SPATIAL)

# ---------------------------------------------------------
# Domain -> actual column mapping
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

domains = list(domain_columns.values())

# Check required columns
required = ["ward_code", "urban_stress_index"] + domains

missing = [c for c in required if c not in stress.columns]

if missing:
    raise ValueError(f"Missing columns in stress file: {missing}")

# ---------------------------------------------------------
# Merge spatial statistics
# ---------------------------------------------------------
spatial_cols = [
    "ward_code",
    "lisa_cluster",
    "moran_local_p",
    "lisa_significant",
]

result = stress.merge(
    spatial[spatial_cols],
    on="ward_code",
    how="left"
)

# ---------------------------------------------------------
# Identify highest-stress domain
# ---------------------------------------------------------
def get_top_domain(row):
    values = row[domains].dropna()

    if values.empty:
        return "Insufficient Data"

    top_column = values.idxmax()

    for domain, column in domain_columns.items():
        if column == top_column:
            return domain

    return "Insufficient Data"


result["priority_domain"] = result.apply(get_top_domain, axis=1)

# ---------------------------------------------------------
# Get score of highest-stress domain
# ---------------------------------------------------------
result["priority_domain_score"] = result.apply(
    lambda row: (
        row[domain_columns[row["priority_domain"]]]
        if row["priority_domain"] in domain_columns
        else np.nan
    ),
    axis=1,
)

# ---------------------------------------------------------
# Intervention priority
# ---------------------------------------------------------
def priority_band(score):
    if pd.isna(score):
        return "Insufficient Data"

    if score >= 60:
        return "High Priority"

    if score >= 40:
        return "Medium Priority"

    return "Lower Priority"


result["intervention_priority"] = (
    result["priority_domain_score"].apply(priority_band)
)

# ---------------------------------------------------------
# Suggested intervention
# ---------------------------------------------------------
interventions = {
    "Healthcare": "Healthcare capacity and accessibility",
    "Education": "School capacity and infrastructure",
    "Sanitation": "Public sanitation and toilet access",
    "Safety": "Police and fire-service accessibility",
    "Transport": "Public transport accessibility",
    "Civic": "Civic service response and resolution",
    "Green Space": "Green-space availability and access",
}

result["suggested_intervention"] = (
    result["priority_domain"]
    .map(interventions)
    .fillna("Further assessment required")
)

# ---------------------------------------------------------
# Overall stress ranking
# ---------------------------------------------------------
result["overall_stress_rank"] = (
    result["urban_stress_index"]
    .rank(method="min", ascending=False)
    .astype(int)
)

# ---------------------------------------------------------
# Decision-support note
# ---------------------------------------------------------
def explanation(row):
    if row["priority_domain"] == "Insufficient Data":
        return "Insufficient domain data for intervention prioritization."

    return (
        f"{row['priority_domain']} is the highest-stress domain "
        f"for this ward ({row['priority_domain_score']:.2f}). "
        f"Overall Urban Stress Index is "
        f"{row['urban_stress_index']:.2f}."
    )


result["decision_support_note"] = result.apply(
    explanation,
    axis=1
)

# ---------------------------------------------------------
# Save
# ---------------------------------------------------------
result.to_csv(OUTPUT, index=False)

print("========================================")
print("WARD PRIORITY ENGINE COMPLETE")
print("========================================")

print(f"Wards processed: {len(result)}")

print("\nPriority domains:")
print(result["priority_domain"].value_counts())

print("\nIntervention priorities:")
print(result["intervention_priority"].value_counts())

print("\nTop 10 wards:")
print(
    result.sort_values(
        "urban_stress_index",
        ascending=False
    )[
        [
            "ward_code",
            "urban_stress_index",
            "overall_stress_rank",
            "priority_domain",
            "priority_domain_score",
            "intervention_priority",
            "lisa_cluster",
        ]
    ].head(10).to_string(index=False)
)

print(f"\nSaved: {OUTPUT}")

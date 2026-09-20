import pandas as pd
import numpy as np

INPUT_EVIDENCE = "data/processed/mumbai_ward_intervention_evidence.csv"
INPUT_STRESS = "data/processed/mumbai_ward_domain_stress_v2.csv"
OUTPUT = "data/processed/mumbai_ward_intervention_recommendations.csv"

evidence = pd.read_csv(INPUT_EVIDENCE)
stress = pd.read_csv(INPUT_STRESS)

# ---------------------------------------------------------
# Intervention definitions
# ---------------------------------------------------------
interventions = {
    "Healthcare": {
        "action": "Assess healthcare capacity and accessibility",
        "reason": "The ward has comparatively high healthcare service pressure."
    },
    "Education": {
        "action": "Assess school infrastructure and classroom capacity",
        "reason": "The ward has comparatively high education-related infrastructure pressure."
    },
    "Sanitation": {
        "action": "Assess public sanitation and toilet capacity",
        "reason": "The ward has comparatively high sanitation service pressure."
    },
    "Safety": {
        "action": "Assess police and fire-service accessibility",
        "reason": "The ward has comparatively high emergency-service pressure."
    },
    "Transport": {
        "action": "Assess public transport accessibility and coverage",
        "reason": "The ward has comparatively high transport-access pressure."
    },
    "Civic": {
        "action": "Prioritize civic-service response and resolution assessment",
        "reason": "The ward has comparatively high civic complaint pressure."
    },
    "Green Space": {
        "action": "Assess green-space availability and accessibility",
        "reason": "The ward has comparatively high green-space pressure."
    },
}

# ---------------------------------------------------------
# Evidence confidence
# ---------------------------------------------------------
# Confidence is based on the availability of evidence records
# for the ward's priority domain. It does NOT represent
# statistical certainty or real-world intervention effectiveness.

evidence_count = (
    evidence
    .groupby(["ward_code", "priority_domain"])
    .size()
    .reset_index(name="evidence_indicator_count")
)

primary_count = (
    evidence[evidence["evidence_level"] == "Primary"]
    .groupby(["ward_code", "priority_domain"])
    .size()
    .reset_index(name="primary_indicator_count")
)

confidence = evidence_count.merge(
    primary_count,
    on=["ward_code", "priority_domain"],
    how="left"
)

confidence["primary_indicator_count"] = (
    confidence["primary_indicator_count"].fillna(0)
)

def confidence_level(row):
    if row["evidence_indicator_count"] >= 2:
        return "High"

    if row["evidence_indicator_count"] == 1:
        return "Medium"

    return "Limited"

confidence["evidence_confidence"] = confidence.apply(
    confidence_level,
    axis=1
)

# ---------------------------------------------------------
# Get primary/supporting evidence
# ---------------------------------------------------------
evidence_summary = (
    evidence
    .sort_values(
        ["ward_code", "normalized_stress"],
        ascending=[True, False]
    )
    .groupby(["ward_code", "priority_domain"])
    .agg(
        top_indicator=("indicator_name", "first"),
        top_indicator_stress=("normalized_stress", "first"),
        evidence_indicator_count=("indicator_name", "count"),
    )
    .reset_index()
)

# ---------------------------------------------------------
# Merge domain stress + evidence
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

priority_rows = []

for _, row in stress.iterrows():

    ward = row["ward_code"]

    available = {
        domain: row[column]
        for domain, column in domain_columns.items()
        if pd.notna(row[column])
    }

    if not available:
        priority_rows.append({
            "ward_code": ward,
            "urban_stress_index": row["urban_stress_index"],
            "priority_domain": "Insufficient Data",
            "priority_domain_score": np.nan,
        })
        continue

    domain = max(available, key=available.get)

    priority_rows.append({
        "ward_code": ward,
        "urban_stress_index": row["urban_stress_index"],
        "priority_domain": domain,
        "priority_domain_score": available[domain],
    })

priority = pd.DataFrame(priority_rows)

result = priority.merge(
    evidence_summary,
    on=["ward_code", "priority_domain"],
    how="left"
)

result = result.merge(
    confidence[
        [
            "ward_code",
            "priority_domain",
            "evidence_indicator_count",
            "primary_indicator_count",
            "evidence_confidence",
        ]
    ],
    on=["ward_code", "priority_domain"],
    how="left",
    suffixes=("", "_confidence")
)

# ---------------------------------------------------------
# Add intervention
# ---------------------------------------------------------
def get_action(domain):
    if domain in interventions:
        return interventions[domain]["action"]
    return "Further assessment required"

def get_reason(domain):
    if domain in interventions:
        return interventions[domain]["reason"]
    return "The available evidence is insufficient for a domain-specific recommendation."

result["suggested_intervention"] = (
    result["priority_domain"].apply(get_action)
)

result["recommendation_basis"] = (
    result["priority_domain"].apply(get_reason)
)

# ---------------------------------------------------------
# Evidence-aware explanation
# ---------------------------------------------------------
def build_explanation(row):

    if row["priority_domain"] == "Insufficient Data":
        return "Insufficient domain data for a specific intervention recommendation."

    indicator = row["top_indicator"]

    if pd.isna(indicator):
        return (
            f"{row['priority_domain']} is the highest-stress domain, "
            "but indicator-level evidence is incomplete."
        )

    score = row["top_indicator_stress"]

    return (
        f"{row['priority_domain']} is the highest-stress domain "
        f"with an indicator-level stress value of {score:.2f}. "
        f"The leading evidence indicator is '{indicator}'. "
        "The recommendation is an analytical decision-support suggestion "
        "and should be validated with current local conditions."
    )

result["explanation"] = result.apply(
    build_explanation,
    axis=1
)

# ---------------------------------------------------------
# Priority band — analytical only
# ---------------------------------------------------------
def analytical_band(score):
    if pd.isna(score):
        return "Insufficient Data"

    if score >= 80:
        return "Very High Relative Pressure"

    if score >= 60:
        return "High Relative Pressure"

    if score >= 40:
        return "Moderate Relative Pressure"

    return "Lower Relative Pressure"

result["domain_pressure_band"] = (
    result["priority_domain_score"]
    .apply(analytical_band)
)

# ---------------------------------------------------------
# Final columns
# ---------------------------------------------------------
columns = [
    "ward_code",
    "urban_stress_index",
    "priority_domain",
    "priority_domain_score",
    "domain_pressure_band",
    "top_indicator",
    "top_indicator_stress",
    "evidence_indicator_count",
    "primary_indicator_count",
    "evidence_confidence",
    "suggested_intervention",
    "recommendation_basis",
    "explanation",
]

result = result[columns]

# ---------------------------------------------------------
# Save
# ---------------------------------------------------------
result.to_csv(OUTPUT, index=False)

print("========================================")
print("INTERVENTION RECOMMENDATION ENGINE")
print("========================================")

print(f"Wards processed: {len(result)}")

print("\nEvidence confidence:")
print(
    result["evidence_confidence"]
    .value_counts()
)

print("\nDomain pressure bands:")
print(
    result["domain_pressure_band"]
    .value_counts()
)

print("\nRecommendations:")
print(
    result[
        [
            "ward_code",
            "urban_stress_index",
            "priority_domain",
            "priority_domain_score",
            "top_indicator",
            "evidence_confidence",
            "suggested_intervention",
        ]
    ]
    .sort_values(
        "urban_stress_index",
        ascending=False
    )
    .to_string(index=False)
)

print(f"\nSaved: {OUTPUT}")

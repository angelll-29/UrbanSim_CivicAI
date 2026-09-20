from pathlib import Path
import pandas as pd
import numpy as np
import geopandas as gpd


# =========================================================
# URBANSIM — CIVIC AI EXPLANATION ENGINE
# =========================================================

BASE = Path(__file__).resolve().parents[1]

STRESS_FILE = (
    BASE / "data" / "processed"
    / "mumbai_ward_domain_stress_v2.csv"
)

CLUSTER_FILE = (
    BASE / "data" / "spatial"
    / "mumbai_ward_clusters.geojson"
)

ANOMALY_FILE = (
    BASE / "data" / "processed"
    / "urban_ward_anomaly_scores.csv"
)

ANOMALY_EVIDENCE_FILE = (
    BASE / "data" / "processed"
    / "urban_ward_anomaly_feature_evidence.csv"
)

SCENARIO_FILE = (
    BASE / "data" / "processed"
    / "urban_scenario_results_v2.csv"
)

INTERVENTION_FILE = (
    BASE / "data" / "processed"
    / "mumbai_ward_intervention_evidence.csv"
)

OUTPUT_FILE = (
    BASE / "data" / "processed"
    / "urban_civic_ai_explanations.csv"
)


print("=" * 65)
print("URBANSIM CIVIC AI EXPLANATION ENGINE")
print("=" * 65)


# ---------------------------------------------------------
# LOAD FILES
# ---------------------------------------------------------

stress = pd.read_csv(STRESS_FILE)
clusters = gpd.read_file(CLUSTER_FILE)
anomalies = pd.read_csv(ANOMALY_FILE)
anomaly_evidence = pd.read_csv(ANOMALY_EVIDENCE_FILE)
scenarios = pd.read_csv(SCENARIO_FILE)
interventions = pd.read_csv(INTERVENTION_FILE)

print(f"\nStress records: {len(stress)}")
print(f"Cluster records: {len(clusters)}")
print(f"Anomaly records: {len(anomalies)}")
print(f"Scenario records: {len(scenarios)}")


# ---------------------------------------------------------
# NORMALIZE WARD CODES
# ---------------------------------------------------------

datasets = [
    stress,
    anomalies,
    anomaly_evidence,
    scenarios,
    interventions
]

for data in datasets:
    if "ward_code" in data.columns:
        data["ward_code"] = (
            data["ward_code"]
            .astype(str)
            .str.strip()
            .str.upper()
        )


# ---------------------------------------------------------
# IDENTIFY STRESS COLUMNS
# ---------------------------------------------------------

domain_columns = {
    "healthcare": "healthcare_stress",
    "education": "education_stress",
    "sanitation": "sanitation_stress",
    "safety": "safety_stress",
    "transport": "transport_stress",
    "civic": "civic_stress",
    "green_space": "green_space_stress"
}


# ---------------------------------------------------------
# FIND ACTUAL STRESS COLUMN NAMES
# ---------------------------------------------------------

available_domain_columns = {}

for domain, column in domain_columns.items():

    if column in stress.columns:
        available_domain_columns[domain] = column


if not available_domain_columns:
    print("\nAvailable stress columns:")
    print(stress.columns.tolist())

    raise KeyError(
        "Could not identify domain stress columns."
    )


# ---------------------------------------------------------
# CLUSTER COLUMN
# ---------------------------------------------------------

cluster_column = "cluster"

if cluster_column not in clusters.columns:
    raise KeyError(
        "Cluster column not found in GIS cluster layer."
    )


# ---------------------------------------------------------
# BUILD CLUSTER LOOKUP
# ---------------------------------------------------------

cluster_lookup = {}

for _, row in clusters.iterrows():

    ward = str(
        row["ward_code"]
    ).strip().upper()

    cluster_lookup[ward] = row[
        "cluster"
    ]


# ---------------------------------------------------------
# ANOMALY EVIDENCE LOOKUP
# ---------------------------------------------------------

anomaly_lookup = {}

for ward, group in anomaly_evidence.groupby(
    "ward_code"
):

    top_features = (
        group
        .sort_values("feature_rank")
        ["feature"]
        .head(5)
        .tolist()
    )

    anomaly_lookup[ward] = top_features


# ---------------------------------------------------------
# SCENARIO LOOKUP
# ---------------------------------------------------------

scenario_lookup = {}

for ward, group in scenarios.groupby(
    "ward_code"
):

    best = (
        group
        .sort_values(
            "pressure_change"
        )
        .iloc[0]
    )

    scenario_lookup[ward] = {
        "scenario": best["scenario"],
        "change": best["pressure_change"]
    }


# ---------------------------------------------------------
# INTERVENTION LOOKUP
# ---------------------------------------------------------

intervention_lookup = {}

for ward, group in interventions.groupby(
    "ward_code"
):

    if len(group) == 0:
        continue

    # Preserve ties by taking all records
    # at the highest evidence score.

    score_column = None

    for candidate in [
        "evidence_score",
        "priority_score",
        "indicator_priority",
        "pressure_score"
    ]:
        if candidate in group.columns:
            score_column = candidate
            break

    if score_column:

        max_score = group[
            score_column
        ].max()

        selected = group[
            group[score_column] == max_score
        ]

    else:

        selected = group.head(1)


    records = []

    for _, row in selected.iterrows():

        records.append({
            "domain":
                row.get(
                    "priority_domain",
                    row.get(
                        "domain",
                        ""
                    )
                ),

            "indicator":
                row.get(
                    "indicator",
                    ""
                )
        })

    intervention_lookup[ward] = records


# ---------------------------------------------------------
# CREATE CIVIC AI RECORDS
# ---------------------------------------------------------

records = []


for _, row in stress.iterrows():

    ward = str(
        row["ward_code"]
    ).strip().upper()


    # -----------------------------------------------------
    # OVERALL STRESS
    # -----------------------------------------------------

    overall = row.get(
        "urban_stress_index",
        row.get(
            "overall_stress",
            row.get(
                "overall_pressure",
                np.nan
            )
        )
    )


    # -----------------------------------------------------
    # DOMAIN VALUES
    # -----------------------------------------------------

    domain_values = {}

    for domain, column in (
        available_domain_columns.items()
    ):

        value = row[column]

        if pd.notna(value):
            domain_values[domain] = float(
                value
            )


    # -----------------------------------------------------
    # TOP DOMAINS
    # -----------------------------------------------------

    sorted_domains = sorted(
        domain_values.items(),
        key=lambda x: x[1],
        reverse=True
    )

    top_domains = [
        domain
        for domain, value
        in sorted_domains[:3]
    ]


    # -----------------------------------------------------
    # ANOMALY
    # -----------------------------------------------------

    anomaly_row = anomalies[
        anomalies["ward_code"] == ward
    ]

    if len(anomaly_row):

        anomaly_row = anomaly_row.iloc[0]

        anomaly_candidate = bool(
            anomaly_row[
                "anomaly_candidate"
            ]
        )

        anomaly_score = float(
            anomaly_row[
                "reconstruction_mse"
            ]
        )

    else:

        anomaly_candidate = False
        anomaly_score = np.nan


    anomaly_features = anomaly_lookup.get(
        ward,
        []
    )


    # -----------------------------------------------------
    # CLUSTER
    # -----------------------------------------------------

    cluster = cluster_lookup.get(
        ward,
        None
    )


    # -----------------------------------------------------
    # SCENARIO
    # -----------------------------------------------------

    scenario = scenario_lookup.get(
        ward,
        None
    )


    # -----------------------------------------------------
    # INTERVENTION
    # -----------------------------------------------------

    intervention = intervention_lookup.get(
        ward,
        []
    )


    # -----------------------------------------------------
    # TEXT EXPLANATION
    # -----------------------------------------------------

    domain_text = (
        ", ".join(top_domains)
        if top_domains
        else "no dominant domain identified"
    )


    explanation = (
        f"Ward {ward} has a modeled UrbanSim "
        f"profile with the strongest relative "
        f"pressure in {domain_text}. "
    )


    if anomaly_candidate:

        explanation += (
            f"The ward is also an anomaly candidate "
            f"with an Autoencoder reconstruction MSE "
            f"of {anomaly_score:.4f}. "
        )

        if anomaly_features:

            explanation += (
                "The largest model reconstruction "
                "deviations are associated with: "
                + ", ".join(anomaly_features[:5])
                + ". "
            )

    else:

        explanation += (
            "The ward is not flagged as an "
            "Autoencoder anomaly candidate. "
        )


    if scenario:

        explanation += (
            f"The strongest modeled scenario effect "
            f"in the current scenario set is "
            f"'{scenario['scenario']}', with a "
            f"{scenario['change']:.2f}-point change "
            f"in relative pressure. "
        )


    explanation += (
        "These outputs are decision-support signals "
        "derived from UrbanSim data and models; "
        "they do not establish causality or guarantee "
        "real-world intervention outcomes."
    )


    # -----------------------------------------------------
    # RECORD
    # -----------------------------------------------------

    records.append({

        "ward_code":
            ward,

        "overall_stress":
            overall,

        "top_domain_1":
            top_domains[0]
            if len(top_domains) > 0
            else "",

        "top_domain_2":
            top_domains[1]
            if len(top_domains) > 1
            else "",

        "top_domain_3":
            top_domains[2]
            if len(top_domains) > 2
            else "",

        "cluster":
            cluster,

        "anomaly_candidate":
            anomaly_candidate,

        "anomaly_score":
            anomaly_score,

        "top_anomaly_features":
            " | ".join(
                anomaly_features
            ),

        "best_scenario":
            scenario["scenario"]
            if scenario
            else "",

        "best_scenario_change":
            scenario["change"]
            if scenario
            else np.nan,

        "intervention_domains":
            " | ".join(
                str(x["domain"])
                for x in intervention
            ),

        "intervention_indicators":
            " | ".join(
                str(x["indicator"])
                for x in intervention
            ),

        "civic_ai_explanation":
            explanation
    })


result = pd.DataFrame(records)


# ---------------------------------------------------------
# SAVE
# ---------------------------------------------------------

result.to_csv(
    OUTPUT_FILE,
    index=False
)


# ---------------------------------------------------------
# REPORT
# ---------------------------------------------------------

print("\n" + "=" * 65)
print("CIVIC AI SUMMARY")
print("=" * 65)

print(
    result[
        [
            "ward_code",
            "top_domain_1",
            "anomaly_candidate",
            "best_scenario_change"
        ]
    ]
    .head(10)
    .to_string(index=False)
)


print("\nAnomaly candidates:")

print(
    result[
        result["anomaly_candidate"]
    ][
        [
            "ward_code",
            "anomaly_score",
            "top_anomaly_features"
        ]
    ].to_string(index=False)
)


print("\nSaved:")
print(OUTPUT_FILE)

print("\n" + "=" * 65)
print("CIVIC AI EXPLANATION ENGINE COMPLETE")
print("=" * 65)

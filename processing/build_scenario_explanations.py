from pathlib import Path
import pandas as pd


# =========================================================
# URBANSIM — SCENARIO EXPLANATION LAYER
# =========================================================

BASE = Path(__file__).resolve().parents[1]

RESULT_FILE = (
    BASE / "data" / "processed"
    / "urban_scenario_results_v2.csv"
)

OUTPUT_FILE = (
    BASE / "data" / "processed"
    / "urban_scenario_explanations.csv"
)


print("=" * 65)
print("URBANSIM SCENARIO EXPLANATION LAYER")
print("=" * 65)


# ---------------------------------------------------------
# LOAD
# ---------------------------------------------------------

df = pd.read_csv(RESULT_FILE)

print(f"\nScenario records: {len(df)}")


# ---------------------------------------------------------
# SCENARIO METADATA
# ---------------------------------------------------------

scenario_info = {

    "healthcare_capacity_plus_20": {
        "intervention":
            "Increase modeled healthcare capacity by 20%",
        "domain":
            "Healthcare",
        "indicator":
            "Population per healthcare facility",
        "direction":
            "Lower modeled pressure"
    },

    "public_toilet_capacity_plus_20": {
        "intervention":
            "Increase modeled public toilet capacity by 20%",
        "domain":
            "Sanitation",
        "indicator":
            "Population per public toilet",
        "direction":
            "Lower modeled pressure"
    },

    "green_space_plus_20": {
        "intervention":
            "Increase modeled green-space count by 20%",
        "domain":
            "Green Space",
        "indicator":
            "Green spaces per km² and per 100k population",
        "direction":
            "Lower modeled pressure"
    },

    "public_transport_plus_20": {
        "intervention":
            "Increase modeled public transport nodes by 20%",
        "domain":
            "Transport",
        "indicator":
            "Transport nodes per 100k population and per km²",
        "direction":
            "Lower modeled pressure"
    },

    "resolution_time_minus_20": {
        "intervention":
            "Reduce modeled average complaint resolution time by 20%",
        "domain":
            "Civic",
        "indicator":
            "Average resolution days",
        "direction":
            "Lower modeled pressure"
    }
}


# ---------------------------------------------------------
# EXPLANATIONS
# ---------------------------------------------------------

records = []


for _, row in df.iterrows():

    scenario = row["scenario"]
    ward = row["ward_code"]

    info = scenario_info[scenario]

    change = row["pressure_change"]

    if change < -0.01:
        effect = "Modeled pressure decreases"

    elif change > 0.01:
        effect = "Modeled pressure increases"

    else:
        effect = "No material modeled change"


    explanation = (
        f"For ward {ward}, the scenario "
        f"'{info['intervention']}' produces a "
        f"{change:.2f}-point change in modeled "
        f"overall relative pressure. The directly "
        f"affected domain is {info['domain']}, "
        f"through {info['indicator']}. "
        f"This is a scenario simulation using the "
        f"fixed UrbanSim V2 reference normalization "
        f"and should not be interpreted as a causal "
        f"prediction of real-world outcomes."
    )


    records.append({

        "ward_code":
            ward,

        "scenario":
            scenario,

        "intervention":
            info["intervention"],

        "affected_domain":
            info["domain"],

        "affected_indicator":
            info["indicator"],

        "baseline_pressure":
            row["baseline_pressure"],

        "scenario_pressure":
            row["scenario_pressure"],

        "pressure_change":
            change,

        "effect":
            effect,

        "explanation":
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
print("SCENARIO EXPLANATION SUMMARY")
print("=" * 65)

print(
    result[
        [
            "ward_code",
            "scenario",
            "affected_domain",
            "pressure_change",
            "effect"
        ]
    ].head(15).to_string(index=False)
)


print("\nSaved:")
print(OUTPUT_FILE)

print("\n" + "=" * 65)
print("SCENARIO EXPLANATION COMPLETE")
print("=" * 65)

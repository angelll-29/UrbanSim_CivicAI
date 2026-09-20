from pathlib import Path
import numpy as np
import pandas as pd


# =========================================================
# URBANSIM — V2 FIXED-REFERENCE SCENARIO ENGINE
# =========================================================

BASE = Path(__file__).resolve().parents[1]

BASE_FILE = BASE / "data" / "processed" / "mumbai_ward_civic_intelligence_base_fire.csv"
NORMALIZED_FILE = BASE / "data" / "processed" / "mumbai_ward_normalized_indicators.csv"
POLICE_FILE = BASE / "data" / "processed" / "mumbai_police_station_ward_summary.csv"

OUTPUT_FILE = BASE / "data" / "processed" / "urban_scenario_results_v2.csv"


print("=" * 65)
print("URBANSIM V2 FIXED-REFERENCE SCENARIO ENGINE")
print("=" * 65)


# ---------------------------------------------------------
# LOAD BASE DATA
# ---------------------------------------------------------

df = pd.read_csv(BASE_FILE)
norm = pd.read_csv(NORMALIZED_FILE)
police = pd.read_csv(POLICE_FILE)

df["ward_code"] = df["ward_code"].astype(str).str.strip().str.upper()
norm["ward_code"] = norm["ward_code"].astype(str).str.strip().str.upper()
police["ward_code"] = police["ward_code"].astype(str).str.strip().str.upper()


# ---------------------------------------------------------
# POLICE DATA
# ---------------------------------------------------------

if "police_station_count" in police.columns:
    police_col = "police_station_count"
elif "station_count" in police.columns:
    police_col = "station_count"
elif "total_police_locations" in police.columns:
    police_col = "total_police_locations"
else:
    raise KeyError(
        "Could not identify police station count column."
    )

df = df.merge(
    police[["ward_code", police_col]].rename(
        columns={police_col: "police_station_count"}
    ),
    on="ward_code",
    how="left"
)


# ---------------------------------------------------------
# REQUIRED DATA
# ---------------------------------------------------------

required = [
    "ward_code",
    "population_2011",
    "area_sq_km",
    "healthcare_facilities",
    "udise_city_schools",
    "students_total",
    "classrooms_repair_pct",
    "public_toilet_count",
    "green_space_count",
    "total_public_transport_nodes",
    "complaints_received_2024",
    "unresolved_complaints_2024",
    "avg_resolution_days_2024",
    "police_station_count",
    "fire_station_count",
]

missing = [c for c in required if c not in df.columns]

if missing:
    raise KeyError(f"Missing columns: {missing}")


# ---------------------------------------------------------
# BUILD RAW V2 INDICATORS
# ---------------------------------------------------------

def indicators(data):

    return pd.DataFrame({
        "ward_code": data["ward_code"],

        "population_per_healthcare_facility":
            data["population_2011"]
            / data["healthcare_facilities"].replace(0, np.nan),

        "students_per_school":
            data["students_total"]
            / data["udise_city_schools"].replace(0, np.nan),

        "classrooms_per_100_students":
            data["classrooms_total_observed"]
            / data["students_total"].replace(0, np.nan)
            * 100,

        "classrooms_repair_pct":
            data["classrooms_repair_pct"],

        "population_per_public_toilet":
            data["population_2011"]
            / data["public_toilet_count"].replace(0, np.nan),

        "population_per_police_station":
            data["population_2011"]
            / data["police_station_count"].replace(0, np.nan),

        "population_per_fire_station":
            data["population_2011"]
            / data["fire_station_count"].replace(0, np.nan),

        "transport_nodes_per_100k_population":
            data["total_public_transport_nodes"]
            / data["population_2011"]
            * 100000,

        "transport_nodes_per_km2":
            data["total_public_transport_nodes"]
            / data["area_sq_km"],

        "complaints_per_1000_population":
            data["complaints_received_2024"]
            / data["population_2011"]
            * 1000,

        "unresolved_per_1000_population":
            data["unresolved_complaints_2024"]
            / data["population_2011"]
            * 1000,

        "avg_resolution_days_2024":
            data["avg_resolution_days_2024"],

        "green_spaces_per_km2":
            data["green_space_count"]
            / data["area_sq_km"],

        "green_spaces_per_100k_population":
            data["green_space_count"]
            / data["population_2011"]
            * 100000,
    })


raw_base = indicators(df)


# ---------------------------------------------------------
# FIXED BASELINE PERCENTILE REFERENCE
# ---------------------------------------------------------

indicator_columns = [
    "population_per_healthcare_facility",
    "students_per_school",
    "classrooms_per_100_students",
    "classrooms_repair_pct",
    "population_per_public_toilet",
    "population_per_police_station",
    "population_per_fire_station",
    "transport_nodes_per_100k_population",
    "transport_nodes_per_km2",
    "complaints_per_1000_population",
    "unresolved_per_1000_population",
    "avg_resolution_days_2024",
    "green_spaces_per_km2",
    "green_spaces_per_100k_population",
]


# Higher raw value = higher pressure
higher_pressure = {
    "population_per_healthcare_facility": True,
    "students_per_school": True,
    "classrooms_per_100_students": False,
    "classrooms_repair_pct": True,
    "population_per_public_toilet": True,
    "population_per_police_station": True,
    "population_per_fire_station": True,
    "transport_nodes_per_100k_population": False,
    "transport_nodes_per_km2": False,
    "complaints_per_1000_population": True,
    "unresolved_per_1000_population": True,
    "avg_resolution_days_2024": True,
    "green_spaces_per_km2": False,
    "green_spaces_per_100k_population": False,
}


# ---------------------------------------------------------
# BUILD FIXED REFERENCE
# ---------------------------------------------------------

reference = {}

for col in indicator_columns:

    values = raw_base[col].dropna().sort_values().values

    reference[col] = values


def fixed_percentile(value, reference_values):

    if pd.isna(value):
        return np.nan

    return (
        np.searchsorted(
            reference_values,
            value,
            side="right"
        )
        / len(reference_values)
        * 100
    )


def calculate_fixed_stress(raw):

    stress = pd.DataFrame(index=raw.index)

    for col in indicator_columns:

        scores = raw[col].apply(
            lambda x: fixed_percentile(
                x,
                reference[col]
            )
        )

        if not higher_pressure[col]:
            scores = 100 - scores

        stress[col + "_stress"] = scores


    # -----------------------------------------------------
    # DOMAIN BALANCING — SAME V2 LOGIC
    # -----------------------------------------------------

    stress["healthcare"] = stress[
        [
            "population_per_healthcare_facility_stress"
        ]
    ].mean(axis=1)

    stress["education"] = stress[
        [
            "students_per_school_stress",
            "classrooms_per_100_students_stress",
            "classrooms_repair_pct_stress",
        ]
    ].mean(axis=1)

    stress["sanitation"] = stress[
        [
            "population_per_public_toilet_stress"
        ]
    ].mean(axis=1)

    stress["safety"] = stress[
        [
            "population_per_police_station_stress",
            "population_per_fire_station_stress",
        ]
    ].mean(axis=1)

    stress["transport"] = stress[
        [
            "transport_nodes_per_100k_population_stress",
            "transport_nodes_per_km2_stress",
        ]
    ].mean(axis=1)

    stress["civic"] = stress[
        [
            "complaints_per_1000_population_stress",
            "unresolved_per_1000_population_stress",
            "avg_resolution_days_2024_stress",
        ]
    ].mean(axis=1)

    stress["green_space"] = stress[
        [
            "green_spaces_per_km2_stress",
            "green_spaces_per_100k_population_stress",
        ]
    ].mean(axis=1)

    stress["overall_pressure"] = stress[
        [
            "healthcare",
            "education",
            "sanitation",
            "safety",
            "transport",
            "civic",
            "green_space",
        ]
    ].mean(axis=1)

    return stress


baseline_stress = calculate_fixed_stress(
    raw_base
)


# ---------------------------------------------------------
# SCENARIOS
# ---------------------------------------------------------

scenarios = {
    "healthcare_capacity_plus_20": {
        "column": "healthcare_facilities",
        "factor": 1.20
    },

    "public_toilet_capacity_plus_20": {
        "column": "public_toilet_count",
        "factor": 1.20
    },

    "green_space_plus_20": {
        "column": "green_space_count",
        "factor": 1.20
    },

    "public_transport_plus_20": {
        "column": "total_public_transport_nodes",
        "factor": 1.20
    },

    "resolution_time_minus_20": {
        "column": "avg_resolution_days_2024",
        "factor": 0.80
    },
}


# ---------------------------------------------------------
# RUN
# ---------------------------------------------------------

records = []

for scenario_name, config in scenarios.items():

    print(f"\nRunning: {scenario_name}")

    scenario_df = df.copy()

    scenario_df[config["column"]] = (
        scenario_df[config["column"]]
        * config["factor"]
    )

    scenario_raw = indicators(scenario_df)

    scenario_stress = calculate_fixed_stress(
        scenario_raw
    )

    for i, ward in enumerate(
        df["ward_code"]
    ):

        records.append({
            "scenario": scenario_name,
            "ward_code": ward,

            "baseline_pressure":
                baseline_stress.iloc[i][
                    "overall_pressure"
                ],

            "scenario_pressure":
                scenario_stress.iloc[i][
                    "overall_pressure"
                ],

            "pressure_change":
                scenario_stress.iloc[i][
                    "overall_pressure"
                ]
                -
                baseline_stress.iloc[i][
                    "overall_pressure"
                ],

            "healthcare_change":
                scenario_stress.iloc[i]["healthcare"]
                -
                baseline_stress.iloc[i]["healthcare"],

            "education_change":
                scenario_stress.iloc[i]["education"]
                -
                baseline_stress.iloc[i]["education"],

            "sanitation_change":
                scenario_stress.iloc[i]["sanitation"]
                -
                baseline_stress.iloc[i]["sanitation"],

            "safety_change":
                scenario_stress.iloc[i]["safety"]
                -
                baseline_stress.iloc[i]["safety"],

            "transport_change":
                scenario_stress.iloc[i]["transport"]
                -
                baseline_stress.iloc[i]["transport"],

            "civic_change":
                scenario_stress.iloc[i]["civic"]
                -
                baseline_stress.iloc[i]["civic"],

            "green_space_change":
                scenario_stress.iloc[i]["green_space"]
                -
                baseline_stress.iloc[i]["green_space"],
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
# SUMMARY
# ---------------------------------------------------------

print("\n" + "=" * 65)
print("SCENARIO SUMMARY")
print("=" * 65)

summary = (
    result
    .groupby("scenario")
    .agg(
        mean_pressure_change=(
            "pressure_change",
            "mean"
        ),
        min_pressure_change=(
            "pressure_change",
            "min"
        ),
        max_pressure_change=(
            "pressure_change",
            "max"
        ),
    )
    .reset_index()
)

print(
    summary.to_string(index=False)
)


print("\nSaved:")
print(OUTPUT_FILE)

print("\n" + "=" * 65)
print("V2 SCENARIO ENGINE COMPLETE")
print("=" * 65)

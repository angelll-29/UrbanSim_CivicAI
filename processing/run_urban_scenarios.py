from pathlib import Path
import numpy as np
import pandas as pd


# =========================================================
# URBANSIM — WHAT-IF / SCENARIO ENGINE
# =========================================================

BASE = Path(__file__).resolve().parents[1]

BASE_FILE = (
    BASE
    / "data"
    / "processed"
    / "mumbai_ward_civic_intelligence_base_fire.csv"
)

OUTPUT_FILE = (
    BASE
    / "data"
    / "processed"
    / "urban_scenario_results.csv"
)


print("=" * 65)
print("URBANSIM WHAT-IF / SCENARIO ENGINE")
print("=" * 65)


# ---------------------------------------------------------
# LOAD MASTER DATA
# ---------------------------------------------------------

df = pd.read_csv(BASE_FILE)

print(f"\nBase wards: {len(df)}")


# ---------------------------------------------------------
# LOAD POLICE WARD SUMMARY
# ---------------------------------------------------------

POLICE_FILE = (
    BASE
    / "data"
    / "processed"
    / "mumbai_police_station_ward_summary.csv"
)

police = pd.read_csv(POLICE_FILE)

police["ward_code"] = (
    police["ward_code"]
    .astype(str)
    .str.strip()
    .str.upper()
)

# Use the authoritative total police-location count
police_count_candidates = [
    c for c in police.columns
    if c in [
        "police_station_count",
        "total_police_locations",
        "police_locations",
        "station_count"
    ]
]

if "police_station_count" in police.columns:
    police_col = "police_station_count"
elif police_count_candidates:
    police_col = police_count_candidates[0]
else:
    raise KeyError(
        "Could not identify police count column."
    )

df = df.drop(
    columns=["police_station_count"],
    errors="ignore"
)

df = df.merge(
    police[
        ["ward_code", police_col]
    ].rename(
        columns={
            police_col: "police_station_count"
        }
    ),
    on="ward_code",
    how="left"
)

if df["police_station_count"].isna().any():
    missing_wards = df.loc[
        df["police_station_count"].isna(),
        "ward_code"
    ].tolist()

    raise ValueError(
        f"Missing police data for wards: {missing_wards}"
    )

print(
    f"Police ward data loaded: "
    f"{len(police)} wards"
)


# ---------------------------------------------------------
# VALIDATE REQUIRED COLUMNS
# ---------------------------------------------------------

required = [
    "ward_code",
    "population_2011",
    "area_sq_km",

    # Healthcare
    "healthcare_facilities",

    # Education
    "udise_city_schools",
    "students_total",
    "classrooms_repair_pct",

    # Sanitation
    "public_toilet_count",

    # Green
    "green_space_count",

    # Transport
    "total_public_transport_nodes",

    # Civic
    "complaints_received_2024",
    "unresolved_complaints_2024",
    "avg_resolution_days_2024",

    # Safety
    "police_station_count",
    "fire_station_count",
]


missing = [
    c for c in required
    if c not in df.columns
]

if missing:
    print("\nMissing columns:")
    for c in missing:
        print(" -", c)

    raise KeyError(
        "Required scenario columns are missing."
    )


print("\nRequired columns: OK")


# ---------------------------------------------------------
# INDICATOR CALCULATION
# ---------------------------------------------------------

def calculate_indicators(data):

    result = pd.DataFrame({

        "ward_code":
            data["ward_code"],

        # ---------------------------------------------
        # HEALTHCARE
        # ---------------------------------------------

        "population_per_healthcare_facility":
            data["population_2011"]
            / data["healthcare_facilities"]
            .replace(0, np.nan),

        # ---------------------------------------------
        # EDUCATION
        # ---------------------------------------------

        "students_per_school":
            data["students_total"]
            / data["udise_city_schools"]
            .replace(0, np.nan),

        "classrooms_repair_pct":
            data["classrooms_repair_pct"],

        # ---------------------------------------------
        # SANITATION
        # ---------------------------------------------

        "population_per_public_toilet":
            data["population_2011"]
            / data["public_toilet_count"]
            .replace(0, np.nan),

        # ---------------------------------------------
        # GREEN SPACE
        # ---------------------------------------------

        "green_spaces_per_km2":
            data["green_space_count"]
            / data["area_sq_km"],

        "green_spaces_per_100k_population":
            data["green_space_count"]
            / data["population_2011"]
            * 100000,

        # ---------------------------------------------
        # TRANSPORT
        # ---------------------------------------------

        "transport_nodes_per_100k_population":
            data["total_public_transport_nodes"]
            / data["population_2011"]
            * 100000,

        "transport_nodes_per_km2":
            data["total_public_transport_nodes"]
            / data["area_sq_km"],

        # ---------------------------------------------
        # CIVIC
        # ---------------------------------------------

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

        # ---------------------------------------------
        # SAFETY
        # ---------------------------------------------

        "population_per_police_station":
            data["population_2011"]
            / data["police_station_count"]
            .replace(0, np.nan),

        "population_per_fire_station":
            data["population_2011"]
            / data["fire_station_count"]
            .replace(0, np.nan),
    })

    return result


# ---------------------------------------------------------
# NORMALIZATION
# ---------------------------------------------------------

def pressure(series):
    """
    Higher value = greater relative pressure.
    """

    return (
        series.rank(
            method="average",
            pct=True
        ) * 100
    )


def availability_pressure(series):
    """
    Higher availability = lower pressure.
    """

    return 100 - pressure(series)


# ---------------------------------------------------------
# DOMAIN STRESS
# ---------------------------------------------------------

def calculate_domain_stress(ind):

    stress = pd.DataFrame(
        index=ind.index
    )

    # Healthcare
    stress["healthcare"] = pressure(
        ind[
            "population_per_healthcare_facility"
        ]
    )

    # Education
    education_1 = pressure(
        ind["students_per_school"]
    )

    education_2 = pressure(
        ind["classrooms_repair_pct"]
    )

    stress["education"] = (
        education_1 + education_2
    ) / 2

    # Sanitation
    stress["sanitation"] = pressure(
        ind[
            "population_per_public_toilet"
        ]
    )

    # Safety
    safety_police = pressure(
        ind[
            "population_per_police_station"
        ]
    )

    safety_fire = pressure(
        ind[
            "population_per_fire_station"
        ]
    )

    stress["safety"] = pd.concat(
        [
            safety_police,
            safety_fire
        ],
        axis=1
    ).mean(axis=1)

    # Transport
    transport_1 = availability_pressure(
        ind[
            "transport_nodes_per_100k_population"
        ]
    )

    transport_2 = availability_pressure(
        ind[
            "transport_nodes_per_km2"
        ]
    )

    stress["transport"] = (
        transport_1 + transport_2
    ) / 2

    # Civic
    civic_1 = pressure(
        ind[
            "complaints_per_1000_population"
        ]
    )

    civic_2 = pressure(
        ind[
            "unresolved_per_1000_population"
        ]
    )

    civic_3 = pressure(
        ind[
            "avg_resolution_days_2024"
        ]
    )

    stress["civic"] = (
        civic_1
        + civic_2
        + civic_3
    ) / 3

    # Green space
    green_1 = availability_pressure(
        ind[
            "green_spaces_per_km2"
        ]
    )

    green_2 = availability_pressure(
        ind[
            "green_spaces_per_100k_population"
        ]
    )

    stress["green_space"] = (
        green_1 + green_2
    ) / 2

    # Equal domain weighting
    stress["overall_pressure"] = (
        stress.mean(axis=1)
    )

    return stress


# ---------------------------------------------------------
# BASELINE
# ---------------------------------------------------------

baseline_indicators = calculate_indicators(
    df
)

baseline_stress = calculate_domain_stress(
    baseline_indicators
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
    }
}


# ---------------------------------------------------------
# RUN SCENARIOS
# ---------------------------------------------------------

records = []


for scenario_name, config in scenarios.items():

    print(
        f"\nRunning: {scenario_name}"
    )

    scenario_df = df.copy()

    scenario_df[
        config["column"]
    ] = (
        scenario_df[
            config["column"]
        ] * config["factor"]
    )

    scenario_indicators = (
        calculate_indicators(
            scenario_df
        )
    )

    scenario_stress = (
        calculate_domain_stress(
            scenario_indicators
        )
    )

    for i, ward in enumerate(
        df["ward_code"]
    ):

        records.append({

            "scenario":
                scenario_name,

            "ward_code":
                ward,

            "baseline_pressure":
                baseline_stress.iloc[i][
                    "overall_pressure"
                ],

            "scenario_pressure":
                scenario_stress.iloc[i][
                    "overall_pressure"
                ],

            "pressure_change":
                (
                    scenario_stress.iloc[i][
                        "overall_pressure"
                    ]
                    -
                    baseline_stress.iloc[i][
                        "overall_pressure"
                    ]
                ),

            "healthcare_change":
                (
                    scenario_stress.iloc[i][
                        "healthcare"
                    ]
                    -
                    baseline_stress.iloc[i][
                        "healthcare"
                    ]
                ),

            "education_change":
                (
                    scenario_stress.iloc[i][
                        "education"
                    ]
                    -
                    baseline_stress.iloc[i][
                        "education"
                    ]
                ),

            "sanitation_change":
                (
                    scenario_stress.iloc[i][
                        "sanitation"
                    ]
                    -
                    baseline_stress.iloc[i][
                        "sanitation"
                    ]
                ),

            "safety_change":
                (
                    scenario_stress.iloc[i][
                        "safety"
                    ]
                    -
                    baseline_stress.iloc[i][
                        "safety"
                    ]
                ),

            "transport_change":
                (
                    scenario_stress.iloc[i][
                        "transport"
                    ]
                    -
                    baseline_stress.iloc[i][
                        "transport"
                    ]
                ),

            "civic_change":
                (
                    scenario_stress.iloc[i][
                        "civic"
                    ]
                    -
                    baseline_stress.iloc[i][
                        "civic"
                    ]
                ),

            "green_space_change":
                (
                    scenario_stress.iloc[i][
                        "green_space"
                    ]
                    -
                    baseline_stress.iloc[i][
                        "green_space"
                    ]
                )
        })


result = pd.DataFrame(
    records
)


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
        )
    )
    .reset_index()
)

print(
    summary.to_string(
        index=False
    )
)


print("\nSaved:")
print(OUTPUT_FILE)

print("\n" + "=" * 65)
print("SCENARIO ENGINE COMPLETE")
print("=" * 65)

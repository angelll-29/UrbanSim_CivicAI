from pathlib import Path

import pandas as pd


INPUT_FILE = Path(
    "data/external/mumbai_census_2011_ward.csv"
)

OUTPUT_FILE = Path(
    "data/processed/mumbai_ward_population_2011.csv"
)


# ============================================================
# LOAD
# ============================================================

df = pd.read_csv(INPUT_FILE)

print("=" * 70)
print("URBANSIM - MUMBAI WARD POPULATION 2011")
print("=" * 70)

print(f"\nRaw Census records: {len(df)}")


# ============================================================
# NORMALIZE WARD NAMES
# ============================================================

def normalize_ward(value):

    value = str(value).strip().upper()

    mapping = {
        "F/N": "FN",
        "F/S": "FS",
        "G/N": "GN",
        "G/S": "GS",
        "H/E": "HE",
        "H/W": "HW",
        "K/E": "KE",
        "K/W": "KW",
        "M/E": "ME",
        "M/W": "MW",
        "P/N": "PN",
        "P/S": "PS",
        "R/C": "RC",
        "R/N": "RN",
        "R/S": "RS",
    }

    return mapping.get(value, value)


df["ward_code"] = df["Ward Name"].apply(
    normalize_ward
)


# ============================================================
# NUMERIC COLUMNS
# ============================================================

numeric_columns = [
    "Total Population",
    "Total Males",
    "Total Females",
    "SC Population",
    "SC Males",
    "SC Females",
    "ST Population",
    "ST Males",
    "ST Females",
]

for column in numeric_columns:

    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    )


# ============================================================
# AGGREGATE TO BMC WARD
# ============================================================

population = (
    df.groupby("ward_code", as_index=False)[numeric_columns]
    .sum()
)


# ============================================================
# RENAME
# ============================================================

population = population.rename(
    columns={
        "Total Population": "population_2011",
        "Total Males": "male_population_2011",
        "Total Females": "female_population_2011",
        "SC Population": "sc_population_2011",
        "SC Males": "sc_male_population_2011",
        "SC Females": "sc_female_population_2011",
        "ST Population": "st_population_2011",
        "ST Males": "st_male_population_2011",
        "ST Females": "st_female_population_2011",
    }
)


# ============================================================
# DERIVED INDICATORS
# ============================================================

population["male_share_pct"] = (
    population["male_population_2011"]
    / population["population_2011"]
    * 100
)

population["female_share_pct"] = (
    population["female_population_2011"]
    / population["population_2011"]
    * 100
)

population["sc_share_pct"] = (
    population["sc_population_2011"]
    / population["population_2011"]
    * 100
)

population["st_share_pct"] = (
    population["st_population_2011"]
    / population["population_2011"]
    * 100
)


# ============================================================
# ROUND PERCENTAGES
# ============================================================

percentage_columns = [
    "male_share_pct",
    "female_share_pct",
    "sc_share_pct",
    "st_share_pct",
]

population[percentage_columns] = (
    population[percentage_columns].round(2)
)


# ============================================================
# VALIDATE 24 BMC WARDS
# ============================================================

BMC_WARDS = [
    "A", "B", "C", "D", "E",
    "FN", "FS", "GN", "GS",
    "HE", "HW", "KE", "KW",
    "L", "ME", "MW", "N",
    "PN", "PS", "RC", "RN",
    "RS", "S", "T"
]

missing_wards = sorted(
    set(BMC_WARDS)
    - set(population["ward_code"])
)

unexpected_wards = sorted(
    set(population["ward_code"])
    - set(BMC_WARDS)
)

print(f"\nAggregated wards: {len(population)}")

if missing_wards:
    print("\nMissing wards:")
    print(missing_wards)

if unexpected_wards:
    print("\nUnexpected wards:")
    print(unexpected_wards)


if missing_wards or unexpected_wards:
    raise ValueError(
        "Ward validation failed."
    )


# ============================================================
# SAVE
# ============================================================

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)

population.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# REPORT
# ============================================================

print("\nWard population:")
print(
    population[
        [
            "ward_code",
            "population_2011",
            "male_population_2011",
            "female_population_2011",
        ]
    ].to_string(index=False)
)

print("\nMumbai total population in dataset:")
print(
    f"{population['population_2011'].sum():,}"
)

print("\nOutput:")
print(OUTPUT_FILE)

print("=" * 70)
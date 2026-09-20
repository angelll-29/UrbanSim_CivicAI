from pathlib import Path

import pandas as pd


# ============================================================
# FILES
# ============================================================

BASE_FILE = Path(
    "data/processed/mumbai_ward_civic_intelligence_base_full_transport.csv"
)

POPULATION_FILE = Path(
    "data/processed/mumbai_ward_population_2011.csv"
)

OUTPUT_FILE = Path(
    "data/processed/mumbai_ward_civic_intelligence_base_population.csv"
)


# ============================================================
# LOAD
# ============================================================

base = pd.read_csv(BASE_FILE)
population = pd.read_csv(POPULATION_FILE)

print("=" * 70)
print("URBANSIM - POPULATION INTEGRATION")
print("=" * 70)

print(f"\nBase wards: {len(base)}")
print(f"Population wards: {len(population)}")


# ============================================================
# VALIDATE WARD KEYS
# ============================================================

if "ward_code" not in base.columns:
    raise ValueError("ward_code missing from base dataset")

if "ward_code" not in population.columns:
    raise ValueError("ward_code missing from population dataset")


# Ensure one population record per ward

if population["ward_code"].duplicated().any():
    raise ValueError(
        "Duplicate ward_code found in population dataset."
    )


# ============================================================
# REMOVE POPULATION COLUMNS IF SCRIPT IS RE-RUN
# ============================================================

population_columns = [
    "population_2011",
    "male_population_2011",
    "female_population_2011",
    "sc_population_2011",
    "sc_male_population_2011",
    "sc_female_population_2011",
    "st_population_2011",
    "st_male_population_2011",
    "st_female_population_2011",
    "male_share_pct",
    "female_share_pct",
    "sc_share_pct",
    "st_share_pct",
]

existing_columns = [
    col for col in population_columns
    if col in base.columns
]

if existing_columns:
    base = base.drop(columns=existing_columns)


# ============================================================
# MERGE
# ============================================================

merged = base.merge(
    population,
    on="ward_code",
    how="left",
    validate="one_to_one",
)


# ============================================================
# VALIDATION
# ============================================================

if len(merged) != 24:
    raise ValueError(
        f"Expected 24 wards after merge, got {len(merged)}"
    )


missing_population = merged[
    "population_2011"
].isna().sum()

if missing_population > 0:
    raise ValueError(
        f"{missing_population} wards have missing population data."
    )


# ============================================================
# SAVE
# ============================================================

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True,
)

merged.to_csv(
    OUTPUT_FILE,
    index=False,
)


# ============================================================
# REPORT
# ============================================================

print("\n" + "=" * 70)
print("POPULATION INTEGRATION COMPLETE")
print("=" * 70)

print(f"Wards: {len(merged)}")
print(f"Columns: {len(merged.columns)}")

print(
    f"\nMumbai population (2011): "
    f"{merged['population_2011'].sum():,}"
)

print("\nPopulation columns added:")

for col in population_columns:
    if col in merged.columns:
        print(f"  + {col}")

print("\nOutput:")
print(OUTPUT_FILE)

print("=" * 70)
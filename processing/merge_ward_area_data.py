from pathlib import Path

import pandas as pd


BASE_FILE = Path(
    "data/processed/mumbai_ward_civic_intelligence_base_population.csv"
)

AREA_FILE = Path(
    "data/processed/mumbai_ward_area_density.csv"
)

OUTPUT_FILE = Path(
    "data/processed/mumbai_ward_civic_intelligence_base_area.csv"
)


# ============================================================
# LOAD
# ============================================================

base = pd.read_csv(BASE_FILE)
area = pd.read_csv(AREA_FILE)

print("=" * 70)
print("URBANSIM - WARD AREA + DENSITY INTEGRATION")
print("=" * 70)

print(f"\nBase wards: {len(base)}")
print(f"Area wards: {len(area)}")


# ============================================================
# VALIDATE
# ============================================================

if "ward_code" not in base.columns:
    raise ValueError("ward_code missing from base dataset")

if "ward_code" not in area.columns:
    raise ValueError("ward_code missing from area dataset")

if area["ward_code"].duplicated().any():
    raise ValueError("Duplicate ward_code found in area dataset")


# ============================================================
# REMOVE OLD AREA COLUMNS IF RE-RUN
# ============================================================

area_columns = [
    "area_sq_m",
    "area_sq_km",
    "population_density_per_sq_km",
]

existing = [
    col for col in area_columns
    if col in base.columns
]

if existing:
    base = base.drop(columns=existing)


# ============================================================
# MERGE
# ============================================================

merged = base.merge(
    area[
        [
            "ward_code",
            "area_sq_m",
            "area_sq_km",
            "population_density_per_sq_km",
        ]
    ],
    on="ward_code",
    how="left",
    validate="one_to_one",
)


# ============================================================
# VALIDATE RESULT
# ============================================================

if len(merged) != 24:
    raise ValueError(
        f"Expected 24 wards after merge, got {len(merged)}"
    )

if merged[
    "population_density_per_sq_km"
].isna().any():
    raise ValueError(
        "Missing population density for one or more wards"
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
print("AREA + DENSITY INTEGRATION COMPLETE")
print("=" * 70)

print(f"Wards: {len(merged)}")
print(f"Columns: {len(merged.columns)}")

print("\nAdded:")
print("  + area_sq_m")
print("  + area_sq_km")
print("  + population_density_per_sq_km")

print("\nOutput:")
print(OUTPUT_FILE)

print("=" * 70)
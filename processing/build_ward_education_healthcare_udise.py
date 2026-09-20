import pandas as pd
from pathlib import Path

BASE_FILE = Path(
    "data/processed/mumbai_ward_education_healthcare.csv"
)

UDISE_FILE = Path(
    "data/processed/udise_city_ward_education_indicators.csv"
)

OUTPUT = Path(
    "data/processed/mumbai_ward_education_healthcare_udise.csv"
)

# --------------------------------------------------
# Load
# --------------------------------------------------

base = pd.read_csv(BASE_FILE)
udise = pd.read_csv(UDISE_FILE)

print("Base ward rows:", len(base))
print("UDISE ward rows:", len(udise))


# --------------------------------------------------
# Normalize ward codes
# --------------------------------------------------

def normalize_ward(value):
    return (
        str(value)
        .strip()
        .upper()
        .replace("/", "")
        .replace("-", "")
        .replace(" ", "")
    )


base["ward_code"] = base["ward_code"].apply(normalize_ward)
udise["ward_code"] = udise["ward_code"].apply(normalize_ward)


# --------------------------------------------------
# Validate uniqueness BEFORE merge
# --------------------------------------------------

print("\nBase duplicate wards:",
      base["ward_code"].duplicated().sum())

print("UDISE duplicate wards:",
      udise["ward_code"].duplicated().sum())


# --------------------------------------------------
# Merge
# --------------------------------------------------

combined = base.merge(
    udise,
    on="ward_code",
    how="left",
    validate="one_to_one",
)


# --------------------------------------------------
# Validation
# --------------------------------------------------

print("\n==============================================")
print("COMBINED URBANSIM WARD DATASET")
print("==============================================")

print("Rows:", len(combined))
print("Unique wards:", combined["ward_code"].nunique())

print("\nMissing UDISE ward matches:",
      combined["udise_city_schools"].isna().sum())


# --------------------------------------------------
# Check important totals
# --------------------------------------------------

print("\nGIS school total:",
      combined["school_count"].sum())

print("Healthcare total:",
      combined["healthcare_facilities"].sum())

print("UDISE City schools:",
      combined["udise_city_schools"].sum())

print("UDISE students:",
      combined["students_total"].sum())

print("UDISE teachers:",
      combined["teachers_total"].sum())


# --------------------------------------------------
# Missing values
# --------------------------------------------------

print("\nMissing values:")
missing = combined.isna().sum()
print(missing[missing > 0].to_string())


# --------------------------------------------------
# Ward list
# --------------------------------------------------

print("\nWard codes:")
print(sorted(combined["ward_code"].unique().tolist()))


# --------------------------------------------------
# Save
# --------------------------------------------------

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

combined.to_csv(
    OUTPUT,
    index=False
)

print("\nSaved:")
print(OUTPUT)
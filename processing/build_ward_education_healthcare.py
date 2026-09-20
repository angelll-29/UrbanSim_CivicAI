import pandas as pd
from pathlib import Path

WARD_FILE = Path("data/raw/mumbai_wards.csv")
SCHOOL_FILE = Path("data/processed/mumbai_school_ward_summary.csv")
HEALTH_FILE = Path("data/processed/mumbai_healthcare_gis_ward_summary.csv")

OUTPUT = Path("data/processed/mumbai_ward_education_healthcare.csv")


# -----------------------------
# Load datasets
# -----------------------------
wards = pd.read_csv(WARD_FILE)
schools = pd.read_csv(SCHOOL_FILE)
health = pd.read_csv(HEALTH_FILE)


# -----------------------------
# Inspect ward column
# -----------------------------
print("Ward columns:", wards.columns.tolist())

# The ward summary uses ward_code.
# Normalize the ward identifier in all datasets.
def normalize_ward(value):
    return (
        str(value)
        .strip()
        .upper()
        .replace("/", "")
        .replace("-", "")
        .replace(" ", "")
    )


wards["ward_code"] = wards["ward_code"].apply(normalize_ward)
schools["ward_code"] = schools["ward_code"].apply(normalize_ward)
health["ward_code"] = health["ward_code"].apply(normalize_ward)


# -----------------------------
# Keep only required school fields
# -----------------------------
school_cols = [
    "ward_code",
    "school_count",
    "aided_schools",
    "unaided_schools",
    "municipal_schools",
]

schools = schools[school_cols].copy()


# -----------------------------
# Keep only required healthcare fields
# -----------------------------
health_cols = [
    "ward_code",
    "healthcare_facilities",
    "dispensaries",
    "hospitals",
    "maternity_hospitals",
    "uphcs",
    "veterinary_hospitals",
]

health = health[health_cols].copy()


# -----------------------------
# Merge school + healthcare
# -----------------------------
combined = wards[["ward_code"]].copy()

combined = combined.merge(
    schools,
    on="ward_code",
    how="left",
)

combined = combined.merge(
    health,
    on="ward_code",
    how="left",
)


# -----------------------------
# Check missing values
# -----------------------------
numeric_cols = [
    "school_count",
    "aided_schools",
    "unaided_schools",
    "municipal_schools",
    "healthcare_facilities",
    "dispensaries",
    "hospitals",
    "maternity_hospitals",
    "uphcs",
    "veterinary_hospitals",
]

print("\nMissing values before fill:")
print(combined[numeric_cols].isna().sum())


# A ward with no recorded facility should be represented as 0
# in this aggregated dataset.
combined[numeric_cols] = combined[numeric_cols].fillna(0)


# -----------------------------
# Integer conversion
# -----------------------------
for col in numeric_cols:
    combined[col] = combined[col].astype(int)


# -----------------------------
# Validation
# -----------------------------
print("\nCombined dataset:")
print(combined.to_string(index=False))

print("\nRows:", len(combined))
print("Unique wards:", combined["ward_code"].nunique())

print("\nSchool total:",
      combined["school_count"].sum())

print("Healthcare total:",
      combined["healthcare_facilities"].sum())


# -----------------------------
# Save
# -----------------------------
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
combined.to_csv(OUTPUT, index=False)

print("\nSaved:")
print(OUTPUT)
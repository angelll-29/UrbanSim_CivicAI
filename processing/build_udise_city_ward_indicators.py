import pandas as pd
from pathlib import Path

INDICATORS = Path("data/processed/udise_education_indicators.csv")
MAPPING = Path("data/processed/udise_city_school_ward_mapping.csv")
OUTPUT = Path("data/processed/udise_city_ward_education_indicators.csv")

ind = pd.read_csv(INDICATORS)
mapping = pd.read_csv(MAPPING)

print("UDISE indicators rows:", len(ind))
print("UDISE mapping rows:", len(mapping))

# --------------------------------------------------
# Keep only City schools that have a BMC ward mapping
# --------------------------------------------------
mapping = mapping[
    mapping["bmc_ward_code"].notna()
].copy()

# Ensure one mapping per pseudocode
mapping = mapping.drop_duplicates(subset=["pseudocode"])

# --------------------------------------------------
# Merge using pseudocode
# --------------------------------------------------
df = mapping.merge(
    ind,
    on="pseudocode",
    how="left",
    validate="one_to_one"
)

print("\nMerged rows:", len(df))
print("Missing indicator records:", df["student_total"].isna().sum())

# --------------------------------------------------
# Aggregate indicators by BMC ward
# --------------------------------------------------

def weighted_ratio(numerator, denominator):
    total_denominator = denominator.sum()
    if total_denominator == 0:
        return 0
    return numerator.sum() / total_denominator


grouped = []

for ward, g in df.groupby("bmc_ward_code"):

    students = g["student_total"].sum()
    teachers = g["teachers_total"].sum()

    row = {
        "ward_code": ward,

        "udise_city_schools": len(g),

        "students_total": students,
        "students_boys": g["student_boys"].sum(),
        "students_girls": g["student_girls"].sum(),

        "teachers_total": teachers,
        "teachers_male": g["teachers_male"].sum(),
        "teachers_female": g["teachers_female"].sum(),

        "classrooms_total_observed": g["classrooms_total_observed"].sum(),
        "classrooms_good": g["classrooms_good"].sum(),
        "classrooms_minor_repair": g["classrooms_minor_repair"].sum(),
        "classrooms_major_repair": g["classrooms_major_repair"].sum(),

        "boys_toilets": g["boys_toilets"].sum(),
        "boys_functional_toilets": g["boys_functional_toilets"].sum(),
        "girls_toilets": g["girls_toilets"].sum(),
        "girls_functional_toilets": g["girls_functional_toilets"].sum(),

        "functional_toilets_total": g["functional_toilets_total"].sum(),

        "cwsn_boys_toilets": g["cwsn_boys_toilets"].sum(),
        "cwsn_girls_toilets": g["cwsn_girls_toilets"].sum(),
        "cwsn_toilets_total": g["cwsn_toilets_total"].sum(),

        "electricity_schools": g["electricity_available"].sum(),
        "library_schools": g["library_available"].sum(),
        "playground_schools": g["playground_available"].sum(),
        "ramps_schools": g["ramps_available"].sum(),
        "handrails_schools": g["handrails_available"].sum(),
        "ict_lab_schools": g["ict_lab_available"].sum(),
        "internet_schools": g["internet_available"].sum(),
        "computer_ict_lab_schools": g["computer_ict_lab_available"].sum(),
    }

    # Derived ward-level ratios
    row["teacher_student_ratio"] = (
        teachers / students if students > 0 else 0
    )

    row["female_teacher_share_pct"] = (
        g["teachers_female"].sum() / teachers * 100
        if teachers > 0 else 0
    )

    row["girls_share_pct"] = (
        g["student_girls"].sum() / students * 100
        if students > 0 else 0
    )

    row["classrooms_repair_pct"] = (
        (
            g["classrooms_minor_repair"].sum()
            + g["classrooms_major_repair"].sum()
        )
        / g["classrooms_total_observed"].sum()
        * 100
        if g["classrooms_total_observed"].sum() > 0 else 0
    )

    grouped.append(row)


summary = pd.DataFrame(grouped)

summary = summary.sort_values("ward_code")

# --------------------------------------------------
# Validation
# --------------------------------------------------

print("\n==============================================")
print("UDISE CITY WARD EDUCATION INDICATORS")
print("==============================================")

print("Rows:", len(summary))
print("Unique wards:", summary["ward_code"].nunique())

print("\nSchool coverage:")
print(summary[["ward_code", "udise_city_schools"]].to_string(index=False))

print("\nTotal City schools represented:",
      summary["udise_city_schools"].sum())

print("\nTotal students represented:",
      summary["students_total"].sum())

print("\nTotal teachers represented:",
      summary["teachers_total"].sum())

print("\nMissing values:")
print(summary.isna().sum().to_string())

# --------------------------------------------------
# Save
# --------------------------------------------------

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
summary.to_csv(OUTPUT, index=False)

print("\nSaved:")
print(OUTPUT)


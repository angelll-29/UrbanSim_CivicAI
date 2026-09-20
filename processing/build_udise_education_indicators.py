import pandas as pd
import numpy as np

INPUT = "data/processed/udise_school_master.csv"
OUTPUT = "data/processed/udise_education_indicators.csv"

# ============================================================
# LOAD MASTER
# ============================================================

df = pd.read_csv(INPUT)

print("Input schools:", len(df))


# ============================================================
# HELPER
# ============================================================

def safe_ratio(numerator, denominator):
    numerator = pd.to_numeric(numerator, errors="coerce")
    denominator = pd.to_numeric(denominator, errors="coerce")

    return np.where(
        denominator > 0,
        numerator / denominator,
        np.nan
    )


# ============================================================
# CREATE INDICATORS WITHOUT MODIFYING ORIGINAL MASTER
# ============================================================

ind = pd.DataFrame()

ind["pseudocode"] = df["pseudocode"].astype(str)


# ============================================================
# 1. STUDENT / ENROLMENT INDICATORS
# ============================================================

ind["student_boys"] = pd.to_numeric(
    df["boys"],
    errors="coerce"
)

ind["student_girls"] = pd.to_numeric(
    df["girls"],
    errors="coerce"
)

ind["student_total"] = pd.to_numeric(
    df["total_enrolment"],
    errors="coerce"
)

ind["girls_share_pct"] = safe_ratio(
    ind["student_girls"],
    ind["student_total"]
) * 100


# ============================================================
# 2. TEACHER INDICATORS
# ============================================================

ind["teachers_total"] = pd.to_numeric(
    df["teacher_total_tch"],
    errors="coerce"
)

ind["teachers_male"] = pd.to_numeric(
    df["teacher_male"],
    errors="coerce"
)

ind["teachers_female"] = pd.to_numeric(
    df["teacher_female"],
    errors="coerce"
)

ind["teacher_student_ratio"] = safe_ratio(
    ind["student_total"],
    ind["teachers_total"]
)

ind["female_teacher_share_pct"] = safe_ratio(
    ind["teachers_female"],
    ind["teachers_total"]
) * 100


# ============================================================
# 3. CLASSROOM CONDITION INDICATORS
# ============================================================

ind["classrooms_good"] = pd.to_numeric(
    df["facility_classrooms_in_good_condition"],
    errors="coerce"
)

ind["classrooms_minor_repair"] = pd.to_numeric(
    df["facility_classrooms_needs_minor_repair"],
    errors="coerce"
)

ind["classrooms_major_repair"] = pd.to_numeric(
    df["facility_classrooms_needs_major_repair"],
    errors="coerce"
)

# The UDISE extract has total_class_rooms = 0 for all schools.
# Therefore derive an observed classroom denominator from
# the three available classroom-condition components.

ind["classrooms_total_observed"] = (
    ind["classrooms_good"].fillna(0)
    + ind["classrooms_minor_repair"].fillna(0)
    + ind["classrooms_major_repair"].fillna(0)
)

repair_total = (
    ind["classrooms_minor_repair"].fillna(0)
    + ind["classrooms_major_repair"].fillna(0)
)

ind["classrooms_repair_pct"] = safe_ratio(
    repair_total,
    ind["classrooms_total_observed"]
) * 100


# ============================================================
# 4. TOILET INDICATORS
# ============================================================

ind["boys_toilets"] = pd.to_numeric(
    df["facility_total_boys_toilet"],
    errors="coerce"
)

ind["boys_functional_toilets"] = pd.to_numeric(
    df["facility_total_boys_func_toilet"],
    errors="coerce"
)

ind["girls_toilets"] = pd.to_numeric(
    df["facility_total_girls_toilet"],
    errors="coerce"
)

ind["girls_functional_toilets"] = pd.to_numeric(
    df["facility_total_girls_func_toilet"],
    errors="coerce"
)

ind["functional_toilets_total"] = (
    ind["boys_functional_toilets"].fillna(0)
    +
    ind["girls_functional_toilets"].fillna(0)
)


# ============================================================
# 5. INFRASTRUCTURE AVAILABILITY
# ============================================================

ind["electricity_available"] = df[
    "facility_electricity_availability"
]

ind["library_available"] = df[
    "facility_library_availability"
]

ind["playground_available"] = df[
    "facility_playground_available"
]

ind["ramps_available"] = df[
    "facility_availability_ramps"
]

ind["handrails_available"] = df[
    "facility_availability_of_handrails"
]

ind["computer_ict_lab_available"] = df[
    "facility_comp_ict_lab_yn"
]

ind["ict_lab_available"] = df[
    "facility_ict_lab_yn"
]

ind["internet_available"] = df[
    "facility_internet"
]


# ============================================================
# 6. CWSN FACILITIES
# ============================================================

ind["cwsn_boys_toilets"] = pd.to_numeric(
    df["facility_total_boys_cwsn_toilet"],
    errors="coerce"
)

ind["cwsn_girls_toilets"] = pd.to_numeric(
    df["facility_total_girls_cwsn_toilet"],
    errors="coerce"
)

ind["cwsn_toilets_total"] = (
    ind["cwsn_boys_toilets"].fillna(0)
    +
    ind["cwsn_girls_toilets"].fillna(0)
)


# ============================================================
# VALIDATION
# ============================================================

print("\n========== VALIDATION ==========")

# Unique school key
duplicate_keys = ind["pseudocode"].duplicated().sum()

print("Duplicate pseudocodes:", duplicate_keys)

assert duplicate_keys == 0


# Student consistency check
valid_enrolment = (
    ind["student_total"].notna()
    &
    ind["student_boys"].notna()
    &
    ind["student_girls"].notna()
)

student_mismatch = (
    ind.loc[valid_enrolment, "student_total"]
    !=
    (
        ind.loc[valid_enrolment, "student_boys"]
        +
        ind.loc[valid_enrolment, "student_girls"]
    )
).sum()

print("Student mismatches:", student_mismatch)

assert student_mismatch == 0


# Missing enrolment
missing_enrolment = ind["student_total"].isna().sum()

print("Missing enrolment schools:", missing_enrolment)

# We expect the 11 schools identified earlier
assert missing_enrolment == 11


# Total enrolment
total_students = ind["student_total"].sum()

print("Total students:", int(total_students))


# Total teachers
total_teachers = ind["teachers_total"].sum()

print("Total teachers:", int(total_teachers))


# ============================================================
# SAVE
# ============================================================

ind.to_csv(
    OUTPUT,
    index=False
)

print("\n========== OUTPUT ==========")
print("Created:", OUTPUT)
print("Rows:", len(ind))
print("Columns:", len(ind.columns))
print("File saved successfully.")

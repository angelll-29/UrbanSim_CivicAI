from pathlib import Path
import pandas as pd
import numpy as np

BASE = Path(__file__).resolve().parents[1]
INPUT = BASE / "data" / "processed" / "mumbai_ward_civic_intelligence_base.csv"
OUTPUT = BASE / "data" / "processed" / "mumbai_ward_indicators.csv"

df = pd.read_csv(INPUT)

def safe_divide(numerator, denominator):
    denominator = denominator.replace(0, np.nan)
    return numerator / denominator

# -----------------------------
# 1. Civic service indicators
# -----------------------------
df["complaints_per_school"] = safe_divide(
    df["complaints_received_2024"], df["school_count"]
)

df["unresolved_complaint_pct"] = safe_divide(
    df["unresolved_complaints_2024"],
    df["complaints_received_2024"]
) * 100

df["closure_rate_pct"] = safe_divide(
    df["complaints_closed_2024"],
    df["complaints_received_2024"]
) * 100

df["avg_resolution_days"] = df["avg_resolution_days_2024"]

df["resolution_days_change_pct"] = safe_divide(
    df["avg_resolution_days_2024"] - df["avg_resolution_days_2023"],
    df["avg_resolution_days_2023"]
) * 100

# -----------------------------
# 2. Education access indicators
# -----------------------------
df["schools_per_1000_students"] = safe_divide(
    df["school_count"], df["students_total"]
) * 1000

df["teachers_per_1000_students"] = safe_divide(
    df["teachers_total"], df["students_total"]
) * 1000

df["functional_toilet_rate_pct"] = safe_divide(
    df["functional_toilets_total"],
    df["boys_toilets"] + df["girls_toilets"]
) * 100

df["classrooms_repair_pct"] = safe_divide(
    df["classrooms_minor_repair"] + df["classrooms_major_repair"],
    df["classrooms_total_observed"]
) * 100

# -----------------------------
# 3. Digital / physical school infrastructure
# -----------------------------
df["electricity_availability_pct"] = safe_divide(
    df["electricity_schools"], df["udise_city_schools"]
) * 100

df["library_availability_pct"] = safe_divide(
    df["library_schools"], df["udise_city_schools"]
) * 100

df["playground_availability_pct"] = safe_divide(
    df["playground_schools"], df["udise_city_schools"]
) * 100

df["ramp_availability_pct"] = safe_divide(
    df["ramps_schools"], df["udise_city_schools"]
) * 100

df["handrail_availability_pct"] = safe_divide(
    df["handrails_schools"], df["udise_city_schools"]
) * 100

df["internet_availability_pct"] = safe_divide(
    df["internet_schools"], df["udise_city_schools"]
) * 100

df["ict_lab_availability_pct"] = safe_divide(
    df["ict_lab_schools"], df["udise_city_schools"]
) * 100

# -----------------------------
# 4. Healthcare access indicators
# -----------------------------
df["healthcare_per_100_schools"] = safe_divide(
    df["healthcare_facilities"], df["school_count"]
) * 100

df["hospitals_per_100_schools"] = safe_divide(
    df["hospitals"], df["school_count"]
) * 100

df["uphcs_per_100_schools"] = safe_divide(
    df["uphcs"], df["school_count"]
) * 100

# -----------------------------
# 5. Keep provenance + core fields
# -----------------------------
indicator_cols = [
    "ward_code", "region",
    "school_count", "healthcare_facilities", "udise_city_schools",
    "students_total", "teachers_total",
    "complaints_received_2024", "complaints_closed_2024",
    "unresolved_complaints_2024",

    "complaints_per_school",
    "unresolved_complaint_pct",
    "closure_rate_pct",
    "avg_resolution_days",
    "resolution_days_change_pct",

    "schools_per_1000_students",
    "teachers_per_1000_students",
    "teacher_student_ratio",
    "female_teacher_share_pct",
    "girls_share_pct",
    "functional_toilet_rate_pct",
    "classrooms_repair_pct",

    "electricity_availability_pct",
    "library_availability_pct",
    "playground_availability_pct",
    "ramp_availability_pct",
    "handrail_availability_pct",
    "internet_availability_pct",
    "ict_lab_availability_pct",

    "healthcare_per_100_schools",
    "hospitals_per_100_schools",
    "uphcs_per_100_schools",
]

missing = [c for c in indicator_cols if c not in df.columns]
if missing:
    raise ValueError(f"Missing required columns: {missing}")

out = df[indicator_cols].copy()

if out["ward_code"].duplicated().any():
    raise ValueError("Duplicate ward codes detected.")

if len(out) != 24:
    raise ValueError(f"Expected 24 wards, found {len(out)}.")

out.to_csv(OUTPUT, index=False)

print("SUCCESS")
print(f"Wards: {len(out)}")
print(f"Indicators: {len(out.columns)}")
print(f"Output: {OUTPUT}")

print("\nIndicator preview:")
preview = [
    "ward_code",
    "complaints_per_school",
    "closure_rate_pct",
    "unresolved_complaint_pct",
    "avg_resolution_days",
    "functional_toilet_rate_pct",
    "classrooms_repair_pct",
    "electricity_availability_pct",
    "internet_availability_pct",
    "healthcare_per_100_schools",
]
print(out[preview].to_string(index=False))

print("\nMissing values:")
print(out.isna().sum()[out.isna().sum() > 0])


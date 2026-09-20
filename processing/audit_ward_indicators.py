from pathlib import Path
import pandas as pd

BASE = Path(__file__).resolve().parents[1]
INPUT = BASE / "data" / "processed" / "mumbai_ward_education_healthcare_udise.csv"
OUT = BASE / "data" / "processed" / "ward_indicator_audit.csv"

df = pd.read_csv(INPUT)

cols = [
    "ward_code",
    "udise_city_schools",
    "classrooms_total",
    "classrooms_good",
    "classrooms_minor_repair",
    "classrooms_major_repair",
    "electricity_schools",
    "internet_schools",
    "library_schools",
    "playground_schools",
    "ramps_schools",
    "handrails_schools",
    "ict_lab_schools",
    "computer_ict_lab_schools",
]

missing = [c for c in cols if c not in df.columns]
if missing:
    raise ValueError(f"Missing columns: {missing}")

audit = df[cols].copy()

# Basic consistency checks
audit["repair_sum"] = (
    audit["classrooms_minor_repair"].fillna(0)
    + audit["classrooms_major_repair"].fillna(0)
)

audit["repair_denominator"] = audit["classrooms_total"]

audit["electricity_rate"] = (
    audit["electricity_schools"] / audit["udise_city_schools"] * 100
)
audit["internet_rate"] = (
    audit["internet_schools"] / audit["udise_city_schools"] * 100
)

audit["classroom_repair_rate"] = (
    audit["repair_sum"] / audit["repair_denominator"] * 100
)

audit.to_csv(OUT, index=False)

print("SUCCESS")
print(f"Rows: {len(audit)}")
print(f"Output: {OUT}")

print("\nClassroom totals:")
print(audit[
    ["ward_code", "classrooms_total", "classrooms_good",
     "classrooms_minor_repair", "classrooms_major_repair", "repair_sum"]
].to_string(index=False))

print("\nInfrastructure rate ranges:")
for c in ["electricity_rate", "internet_rate", "classroom_repair_rate"]:
    s = audit[c]
    print(
        f"{c}: min={s.min():.2f}, max={s.max():.2f}, "
        f"missing={s.isna().sum()}"
    )

print("\nUnique raw values for infrastructure counts:")
for c in [
    "electricity_schools", "internet_schools", "library_schools",
    "playground_schools", "ramps_schools", "handrails_schools",
    "ict_lab_schools", "computer_ict_lab_schools"
]:
    print(f"{c}: {sorted(audit[c].dropna().unique().tolist())[:30]}")

print("\nConsistency warnings:")
for _, r in audit.iterrows():
    warnings = []
    if pd.notna(r["classrooms_total"]) and r["repair_sum"] > r["classrooms_total"]:
        warnings.append("repair_sum > classrooms_total")
    if pd.notna(r["electricity_rate"]) and r["electricity_rate"] > 100:
        warnings.append("electricity > 100%")
    if pd.notna(r["internet_rate"]) and r["internet_rate"] > 100:
        warnings.append("internet > 100%")
    if warnings:
        print(r["ward_code"], " | ", "; ".join(warnings))

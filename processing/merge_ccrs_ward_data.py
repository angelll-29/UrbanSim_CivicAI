from pathlib import Path
import pandas as pd

BASE = Path(__file__).resolve().parents[1]
PROCESSED = BASE / "data" / "processed"

EDU_HEALTH = PROCESSED / "mumbai_ward_education_healthcare_udise.csv"
CCRS = PROCESSED / "mumbai_ccrs_ward_complaints_2024.csv"
OUTPUT = PROCESSED / "mumbai_ward_civic_intelligence_base.csv"

def normalize_ward(value):
    if pd.isna(value):
        return value
    value = str(value).strip().upper()
    return {
        "H/E": "HE", "H/W": "HW",
        "K/E": "KE", "K/W": "KW",
        "M/E": "ME", "M/W": "MW",
        "P/N": "PN", "P/S": "PS",
        "R/C": "RC", "R/N": "RN", "R/S": "RS",
        "F/N": "FN", "F/S": "FS",
        "G/N": "GN", "G/S": "GS",
    }.get(value, value)

print("Loading ward base data...")
base = pd.read_csv(EDU_HEALTH)
ccrs = pd.read_csv(CCRS)

base["ward_code"] = base["ward_code"].map(normalize_ward)
ccrs["ward_code"] = ccrs["ward_code"].map(normalize_ward)

if base["ward_code"].duplicated().any():
    raise ValueError("Base ward dataset contains duplicate ward_code values.")

if ccrs["ward_code"].duplicated().any():
    raise ValueError("CCRS dataset contains duplicate ward_code values.")

merged = base.merge(
    ccrs,
    on="ward_code",
    how="left",
    validate="one_to_one",
    suffixes=("", "_ccrs"),
)

if len(merged) != 24:
    raise ValueError(f"Expected 24 wards after merge, got {len(merged)}.")

missing_ccrs = merged["complaints_received_2024"].isna().sum()
if missing_ccrs:
    raise ValueError(f"{missing_ccrs} wards are missing CCRS data.")

merged.to_csv(OUTPUT, index=False)

print("\nSUCCESS")
print(f"Rows: {len(merged)}")
print(f"Columns: {len(merged.columns)}")
print(f"Output: {OUTPUT}")
print("\nCCRS 2024 totals:")
print("Complaints received:", int(merged["complaints_received_2024"].sum()))
print("Complaints closed:", int(merged["complaints_closed_2024"].sum()))
print("Unresolved:", int(merged["unresolved_complaints_2024"].sum()))
print("\nWard coverage: 24/24")

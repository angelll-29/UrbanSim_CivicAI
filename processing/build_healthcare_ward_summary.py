import pandas as pd
from pathlib import Path

INPUT = Path("data/processed/mumbai_healthcare_facilities.csv")
OUTPUT = Path("data/processed/mumbai_healthcare_ward_summary.csv")

df = pd.read_csv(INPUT)

# Standardize ward-code naming variants
WARD_NORMALIZATION = {
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

df["ward_code_standard"] = (
    df["ward_code"]
    .astype(str)
    .str.strip()
    .str.upper()
    .replace(WARD_NORMALIZATION)
)

# Keep only records with a valid ward
df = df[
    df["ward_code_standard"].notna()
    & (df["ward_code_standard"] != "")
    & (df["ward_code_standard"] != "NAN")
].copy()

summary = (
    df.groupby("ward_code_standard")
    .agg(
        healthcare_facilities=("facility_id", "count"),
        dispensaries=("service_type", lambda x: (x == "dispensary").sum()),
        hospitals=("service_type", lambda x: (x == "hospital").sum()),
        maternity_hospitals=(
            "service_type",
            lambda x: (x == "maternity_hospital").sum()
        ),
        uphcs=("service_type", lambda x: (x == "uphc").sum()),
        veterinary_hospitals=(
            "service_type",
            lambda x: (x == "veterinary_hospital").sum()
        ),
    )
    .reset_index()
    .rename(columns={"ward_code_standard": "ward_code"})
)

summary = summary.sort_values("ward_code")

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
summary.to_csv(OUTPUT, index=False)

print("Healthcare ward summary created successfully.")
print("Rows:", len(summary))

print("\nSummary:")
print(summary.to_string(index=False))

print("\nTotal facilities represented:", summary["healthcare_facilities"].sum())

print("\nWard codes:")
print(summary["ward_code"].tolist())
import pandas as pd
from pathlib import Path

INPUT = Path("data/processed/mumbai_healthcare_validated.csv")
OUTPUT = Path("data/processed/mumbai_healthcare_gis_ward_summary.csv")

df = pd.read_csv(INPUT)

# Use GIS-derived ward for spatial analysis
df = df[
    df["gis_ward"].notna()
    & (df["gis_ward"].astype(str).str.strip() != "")
].copy()

summary = (
    df.groupby("gis_ward")
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
    .rename(columns={"gis_ward": "ward_code"})
)

summary = summary.sort_values("ward_code")

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
summary.to_csv(OUTPUT, index=False)

print("Healthcare GIS ward summary created successfully.")
print("Rows:", len(summary))

print("\nSummary:")
print(summary.to_string(index=False))

print("\nTotal facilities represented:",
      summary["healthcare_facilities"].sum())

print("\nFacility type totals:")
print("Dispensaries:", summary["dispensaries"].sum())
print("Hospitals:", summary["hospitals"].sum())
print("Maternity hospitals:", summary["maternity_hospitals"].sum())
print("UPHCs:", summary["uphcs"].sum())
print("Veterinary hospitals:", summary["veterinary_hospitals"].sum())
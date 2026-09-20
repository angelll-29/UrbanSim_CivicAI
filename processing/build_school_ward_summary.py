import pandas as pd

INPUT = "data/processed/mumbai_schools_validated.csv"
OUTPUT = "data/processed/mumbai_school_ward_summary.csv"

df = pd.read_csv(INPUT)

# Use GIS-derived ward assignment
df = df[df["gis_ward"].notna()].copy()

# Ensure numeric coordinates
df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")

summary = (
    df.groupby("gis_ward")
      .agg(
          school_count=("school_id", "count"),
          valid_coordinates=("coordinate_valid", "sum"),
          aided_schools=("school_category", lambda x: (x.astype(str).str.lower() == "aided").sum()),
          unaided_schools=("school_category", lambda x: (x.astype(str).str.lower() == "unaided").sum()),
          municipal_schools=("school_category", lambda x: (x.astype(str).str.lower() == "municipal").sum()),
      )
      .reset_index()
      .rename(columns={"gis_ward": "ward_code"})
)

summary["coordinate_coverage_pct"] = (
    summary["valid_coordinates"] / summary["school_count"] * 100
)

summary = summary.sort_values("ward_code")

summary.to_csv(OUTPUT, index=False)

print("======================================")
print("MUMBAI SCHOOL WARD SUMMARY")
print("======================================")
print("Wards represented:", len(summary))
print("Schools represented:", int(summary["school_count"].sum()))
print("Output:", OUTPUT)

print("\nWard summary:")
print(summary.to_string(index=False))

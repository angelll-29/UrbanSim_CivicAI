from pathlib import Path
import pandas as pd

INPUT = Path(
    "data/processed/mumbai_public_toilets_validated.csv"
)

OUTPUT = Path(
    "data/processed/mumbai_public_toilet_ward_summary.csv"
)

df = pd.read_csv(INPUT)

# Use only toilets physically located inside a BMC ward
df = df[df["urban_ward_code"].notna()].copy()

summary = (
    df.groupby("urban_ward_code")
    .agg(
        public_toilet_count=("toilet_id", "count"),
        female_facility_count=("female_facilities", "sum"),
        male_facility_count=("male_facilities", "sum"),
        total_toilet_facilities=("total_facilities", "sum"),
    )
    .reset_index()
    .rename(columns={"urban_ward_code": "ward_code"})
)

# Ensure all 24 BMC wards are represented
ward_codes = [
    "A", "B", "C", "D", "E",
    "FN", "FS", "GN", "GS",
    "HE", "HW", "KE", "KW",
    "L", "ME", "MW", "N",
    "PN", "PS", "RC", "RN",
    "RS", "S", "T"
]

ward_df = pd.DataFrame({"ward_code": ward_codes})

summary = ward_df.merge(
    summary,
    on="ward_code",
    how="left"
)

numeric_cols = [
    "public_toilet_count",
    "female_facility_count",
    "male_facility_count",
    "total_toilet_facilities",
]

summary[numeric_cols] = summary[numeric_cols].fillna(0)

# Population baseline = Census 2011
population = pd.read_csv(
    "data/processed/mumbai_ward_population_2011.csv"
)

population = population[
    ["ward_code", "population_2011"]
]

summary = summary.merge(
    population,
    on="ward_code",
    how="left"
)

# Derived accessibility indicators
summary["population_per_public_toilet"] = (
    summary["population_2011"]
    / summary["public_toilet_count"].replace(0, pd.NA)
)

summary["toilets_per_10000_population"] = (
    summary["public_toilet_count"]
    / summary["population_2011"]
    * 10000
)

summary["facilities_per_10000_population"] = (
    summary["total_toilet_facilities"]
    / summary["population_2011"]
    * 10000
)

summary.to_csv(OUTPUT, index=False)

print("\nPublic Toilet Ward Summary")
print("--------------------------------")

print(f"Wards: {len(summary)}")
print(
    f"Public toilet locations: "
    f"{summary['public_toilet_count'].sum():,.0f}"
)
print(
    f"Male facilities: "
    f"{summary['male_facility_count'].sum():,.0f}"
)
print(
    f"Female facilities: "
    f"{summary['female_facility_count'].sum():,.0f}"
)
print(
    f"Total facilities: "
    f"{summary['total_toilet_facilities'].sum():,.0f}"
)

print("\nOutput:")
print(OUTPUT)

print("\nWard summary:")
print(
    summary[
        [
            "ward_code",
            "public_toilet_count",
            "total_toilet_facilities",
            "population_2011",
            "population_per_public_toilet",
            "toilets_per_10000_population",
        ]
    ].to_string(index=False)
)
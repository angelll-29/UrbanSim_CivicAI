from pathlib import Path
import pandas as pd

BASE = Path(
    "data/processed/mumbai_ward_civic_intelligence_base_area.csv"
)

TOILETS = Path(
    "data/processed/mumbai_public_toilet_ward_summary.csv"
)

OUTPUT = Path(
    "data/processed/mumbai_ward_civic_intelligence_base_toilets.csv"
)


def main():

    base = pd.read_csv(BASE)
    toilets = pd.read_csv(TOILETS)

    toilet_columns = [
        "ward_code",
        "public_toilet_count",
        "female_facility_count",
        "male_facility_count",
        "total_toilet_facilities",
        "population_per_public_toilet",
        "toilets_per_10000_population",
        "facilities_per_10000_population",
    ]

    toilets = toilets[toilet_columns]

    merged = base.merge(
        toilets,
        on="ward_code",
        how="left",
        validate="one_to_one"
    )

    numeric_columns = [
        "public_toilet_count",
        "female_facility_count",
        "male_facility_count",
        "total_toilet_facilities",
        "population_per_public_toilet",
        "toilets_per_10000_population",
        "facilities_per_10000_population",
    ]

    missing = merged[numeric_columns].isna().sum().sum()

    if missing > 0:
        raise ValueError(
            f"Unexpected missing toilet indicators: {missing}"
        )

    merged.to_csv(OUTPUT, index=False)

    print("\nPublic Toilet Integration Complete")
    print("-----------------------------------")
    print(f"Wards:       {len(merged)}")
    print(f"Columns:     {len(merged.columns)}")
    print(f"Missing:     {missing}")

    print("\nNew toilet indicators:")
    for column in numeric_columns:
        print(f"  {column}")

    print("\nOutput:")
    print(OUTPUT)


if __name__ == "__main__":
    main()
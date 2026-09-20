from pathlib import Path
import pandas as pd

BASE = Path(
    "data/processed/mumbai_ward_civic_intelligence_base_toilets.csv"
)

FIRE = Path(
    "data/processed/mumbai_fire_station_ward_indicators.csv"
)

OUTPUT = Path(
    "data/processed/mumbai_ward_civic_intelligence_base_fire.csv"
)


def main():

    base = pd.read_csv(BASE)
    fire = pd.read_csv(FIRE)

    fire_columns = [
        "ward_code",
        "fire_station_count",
        "fire_stations_per_100k_population",
        "fire_stations_per_10_sq_km",
        "population_per_fire_station",
    ]

    fire = fire[fire_columns]

    merged = base.merge(
        fire,
        on="ward_code",
        how="left",
        validate="one_to_one"
    )

    required = [
        "fire_station_count",
        "fire_stations_per_100k_population",
        "fire_stations_per_10_sq_km",
    ]

    if merged[required].isna().any().any():
        raise ValueError(
            "Unexpected missing Fire Station indicators."
        )

    if len(merged) != 24:
        raise ValueError(
            f"Expected 24 wards, found {len(merged)}"
        )

    merged.to_csv(
        OUTPUT,
        index=False
    )

    print("\nFire Station Integration Complete")
    print("-----------------------------------")

    print(f"Wards:       {len(merged)}")
    print(f"Columns:     {len(merged.columns)}")

    print(
        f"Total stations: "
        f"{merged['fire_station_count'].sum()}"
    )

    print(
        f"Wards with stations: "
        f"{(merged['fire_station_count'] > 0).sum()}"
    )

    print(
        f"Wards with zero stations: "
        f"{(merged['fire_station_count'] == 0).sum()}"
    )

    print("\nOutput:")
    print(OUTPUT)


if __name__ == "__main__":
    main()
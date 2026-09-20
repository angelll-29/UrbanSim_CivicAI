from pathlib import Path
import pandas as pd

FIRE = Path(
    "data/processed/mumbai_fire_station_ward_summary.csv"
)

POPULATION = Path(
    "data/processed/mumbai_ward_population_2011.csv"
)

AREA = Path(
    "data/processed/mumbai_ward_area_density.csv"
)

OUTPUT = Path(
    "data/processed/mumbai_fire_station_ward_indicators.csv"
)


def main():

    fire = pd.read_csv(FIRE)
    population = pd.read_csv(POPULATION)
    area = pd.read_csv(AREA)

    population = population[
        ["ward_code", "population_2011"]
    ]

    area = area[
        ["ward_code", "area_sq_km"]
    ]

    df = fire.merge(
        population,
        on="ward_code",
        how="left",
        validate="one_to_one"
    )

    df = df.merge(
        area,
        on="ward_code",
        how="left",
        validate="one_to_one"
    )

    # Fire stations per 100,000 population
    df["fire_stations_per_100k_population"] = (
        df["fire_station_count"]
        / df["population_2011"]
        * 100000
    )

    # Fire stations per 10 sq km
    df["fire_stations_per_10_sq_km"] = (
        df["fire_station_count"]
        / df["area_sq_km"]
        * 10
    )

    # Population served per fire station.
    # NaN is retained for wards with zero stations.
    df["population_per_fire_station"] = (
        df["population_2011"]
        / df["fire_station_count"].replace(0, pd.NA)
    )

    # Basic validation
    if len(df) != 24:
        raise ValueError(
            f"Expected 24 wards, found {len(df)}"
        )

    if df["population_2011"].isna().any():
        raise ValueError(
            "Missing population values detected."
        )

    if df["area_sq_km"].isna().any():
        raise ValueError(
            "Missing ward area values detected."
        )

    df.to_csv(
        OUTPUT,
        index=False
    )

    print("\nFire Station Indicators")
    print("--------------------------------")

    print(
        f"Wards: {len(df)}"
    )

    print(
        f"Total stations: "
        f"{df['fire_station_count'].sum()}"
    )

    print(
        f"Wards with stations: "
        f"{(df['fire_station_count'] > 0).sum()}"
    )

    print(
        f"Wards with zero stations: "
        f"{(df['fire_station_count'] == 0).sum()}"
    )

    print("\nIndicators:")
    print(
        df[
            [
                "ward_code",
                "fire_station_count",
                "population_2011",
                "area_sq_km",
                "fire_stations_per_100k_population",
                "fire_stations_per_10_sq_km",
                "population_per_fire_station",
            ]
        ].to_string(index=False)
    )

    print("\nOutput:")
    print(OUTPUT)


if __name__ == "__main__":
    main()
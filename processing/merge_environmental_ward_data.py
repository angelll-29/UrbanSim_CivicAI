from pathlib import Path
import pandas as pd

MASTER = Path(
    "data/processed/mumbai_ward_civic_intelligence_base_police.csv"
)

ENV = Path(
    "data/processed/mumbai_ward_environmental_profile.csv"
)

OUTPUT = Path(
    "data/processed/mumbai_ward_civic_intelligence_base_environment.csv"
)


def main():

    master = pd.read_csv(MASTER)
    env = pd.read_csv(ENV)

    print("Current master:")
    print(f"  Rows:    {len(master)}")
    print(f"  Columns: {len(master.columns)}")

    print("\nEnvironmental profile:")
    print(f"  Rows:    {len(env)}")
    print(f"  Columns: {len(env.columns)}")

    # Environmental columns to integrate.
    env_columns = [
        "ward_code",

        # Air quality
        "pm25",
        "pm10",
        "no2",
        "so2",
        "o3",
        "co",

        # Air-quality station coverage
        "pm25_station_count",
        "pm10_station_count",
        "no2_station_count",
        "so2_station_count",
        "o3_station_count",
        "co_station_count",

        # Observation age
        "pm25_age_hours",
        "pm10_age_hours",
        "no2_age_hours",
        "so2_age_hours",
        "o3_age_hours",
        "co_age_hours",

        # Environmental monitoring
        "recent_measurement_count",
        "environmental_station_presence",

        # Green space
        "green_space_count",
        "green_space_share_pct",
        "green_spaces_per_km2",
        "green_spaces_per_100k_population"
    ]

    # Keep only columns that actually exist.
    available = [
        column
        for column in env_columns
        if column in env.columns
    ]

    missing = [
        column
        for column in env_columns
        if column not in env.columns
        and column != "ward_code"
    ]

    if missing:
        print("\nWarning — environmental columns not found:")
        for column in missing:
            print(f"  {column}")

    env = env[available].copy()

    # Ensure one row per ward.
    if env["ward_code"].duplicated().any():

        raise ValueError(
            "Environmental profile contains duplicate ward codes."
        )

    if master["ward_code"].duplicated().any():

        raise ValueError(
            "Master contains duplicate ward codes."
        )

    # Check ward coverage.
    master_wards = set(
        master["ward_code"]
    )

    env_wards = set(
        env["ward_code"]
    )

    missing_wards = (
        master_wards - env_wards
    )

    if missing_wards:

        raise ValueError(
            "Environmental data missing wards: "
            f"{sorted(missing_wards)}"
        )

    # Prevent accidental duplicate columns.
    existing_columns = set(
        master.columns
    )

    merge_columns = [
        column
        for column in env.columns
        if column == "ward_code"
        or column not in existing_columns
    ]

    env = env[merge_columns]

    merged = master.merge(
        env,
        on="ward_code",
        how="left",
        validate="one_to_one"
    )

    # The merge must preserve exactly 24 wards.
    if len(merged) != len(master):

        raise ValueError(
            "Merge changed the number of ward rows."
        )

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    merged.to_csv(
        OUTPUT,
        index=False
    )

    print("\nEnvironmental Integration Complete")
    print("------------------------------------")

    print(
        f"Rows:    {len(merged)}"
    )

    print(
        f"Columns: {len(merged.columns)}"
    )

    print(
        "Added columns:",
        len(merged.columns) - len(master.columns)
    )

    print(
        "\nWards with recent air-quality data:",
        merged[
            "environmental_station_presence"
        ].sum()
    )

    print(
        "Wards without recent air-quality data:",
        (
            ~merged[
                "environmental_station_presence"
            ]
        ).sum()
    )

    print(
        "\nOutput:"
    )

    print(OUTPUT)


if __name__ == "__main__":
    main()

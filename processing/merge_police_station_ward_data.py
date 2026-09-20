from pathlib import Path
import pandas as pd

MASTER = Path(
    "data/processed/mumbai_ward_civic_intelligence_base_fire.csv"
)

POLICE = Path(
    "data/processed/mumbai_police_station_ward_summary.csv"
)

OUTPUT = Path(
    "data/processed/mumbai_ward_civic_intelligence_base_police.csv"
)


def main():

    master = pd.read_csv(MASTER)
    police = pd.read_csv(POLICE)

    print("Current master:")
    print(f"  Rows:    {len(master)}")
    print(f"  Columns: {len(master.columns)}")

    print("\nPolice summary:")
    print(f"  Rows:    {len(police)}")
    print(f"  Columns: {len(police.columns)}")

    # Keep only police-specific columns.
    police_columns = [
        "ward_code",
        "police_location_count",
        "police_station_count",
        "police_office_count",
        "traffic_chowki_count",
        "police_control_room_count",
        "police_stations_per_100k_population",
        "police_stations_per_10_sq_km",
        "population_per_police_station"
    ]

    police = police[police_columns].copy()

    # Prevent accidental duplicate ward records.
    if police["ward_code"].duplicated().any():

        duplicates = police[
            police["ward_code"].duplicated(
                keep=False
            )
        ]

        print("\nERROR: Duplicate ward codes found:")
        print(duplicates.to_string(index=False))

        raise ValueError(
            "Police summary contains duplicate wards."
        )

    if master["ward_code"].duplicated().any():

        raise ValueError(
            "Master dataset contains duplicate wards."
        )

    # Check that all master wards exist in police summary.
    missing = set(
        master["ward_code"]
    ) - set(
        police["ward_code"]
    )

    if missing:

        raise ValueError(
            f"Police data missing wards: {sorted(missing)}"
        )

    merged = master.merge(
        police,
        on="ward_code",
        how="left",
        validate="one_to_one"
    )

    if len(merged) != len(master):

        raise ValueError(
            "Merge changed the number of ward rows."
        )

    # Integer count fields.
    count_columns = [
        "police_location_count",
        "police_station_count",
        "police_office_count",
        "traffic_chowki_count",
        "police_control_room_count"
    ]

    for column in count_columns:

        merged[column] = (
            merged[column]
            .fillna(0)
            .astype(int)
        )

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    merged.to_csv(
        OUTPUT,
        index=False
    )

    print("\nPolice integration complete")
    print("---------------------------")

    print(
        f"Rows:    {len(merged)}"
    )

    print(
        f"Columns: {len(merged.columns)}"
    )

    print(
        f"Police stations: "
        f"{merged['police_station_count'].sum()}"
    )

    print(
        f"Police locations: "
        f"{merged['police_location_count'].sum()}"
    )

    print(
        f"Wards with police stations: "
        f"{(merged['police_station_count'] > 0).sum()}"
    )

    print(
        f"Wards with zero police stations: "
        f"{(merged['police_station_count'] == 0).sum()}"
    )

    print(
        f"\nOutput: {OUTPUT}"
    )


if __name__ == "__main__":
    main()

from pathlib import Path
import pandas as pd

POLICE = Path(
    "data/processed/mumbai_police_stations_validated.csv"
)

POP = Path(
    "data/processed/mumbai_ward_population_2011.csv"
)

AREA = Path(
    "data/processed/mumbai_ward_area_density.csv"
)

OUT = Path(
    "data/processed/mumbai_police_station_ward_summary.csv"
)


def main():

    police = pd.read_csv(POLICE)

    population = pd.read_csv(POP)

    area = pd.read_csv(AREA)

    # Only spatially assigned records are used for
    # ward-level aggregation.
    police = police[
        police["urban_ward_code"].notna()
    ].copy()

    police["urban_ward_code"] = (
        police["urban_ward_code"]
        .astype(str)
        .str.strip()
    )

    # Start with all 24 BMC wards so zero-infrastructure
    # wards are explicitly represented.
    wards = pd.DataFrame({
        "ward_code": sorted(
            area["ward_code"]
            .dropna()
            .unique()
        )
    })

    grouped = (
        police
        .groupby(
            ["urban_ward_code", "subtype"],
            dropna=False
        )
        .size()
        .unstack(fill_value=0)
        .reset_index()
        .rename(
            columns={
                "urban_ward_code": "ward_code"
            }
        )
    )

    # Ensure expected columns exist.
    for column in [
        "Station",
        "Office",
        "Traffic Chowki",
        "Control Room"
    ]:

        if column not in grouped.columns:
            grouped[column] = 0

    grouped = grouped.rename(
        columns={
            "Station":
                "police_station_count",

            "Office":
                "police_office_count",

            "Traffic Chowki":
                "traffic_chowki_count",

            "Control Room":
                "police_control_room_count"
        }
    )

    summary = wards.merge(
        grouped[
            [
                "ward_code",
                "police_station_count",
                "police_office_count",
                "traffic_chowki_count",
                "police_control_room_count"
            ]
        ],
        on="ward_code",
        how="left"
    )

    count_columns = [
        "police_station_count",
        "police_office_count",
        "traffic_chowki_count",
        "police_control_room_count"
    ]

    summary[count_columns] = (
        summary[count_columns]
        .fillna(0)
        .astype(int)
    )

    summary["police_location_count"] = (
        summary[count_columns]
        .sum(axis=1)
    )

    summary = summary.merge(
        population[
            [
                "ward_code",
                "population_2011"
            ]
        ],
        on="ward_code",
        how="left"
    )

    summary = summary.merge(
        area[
            [
                "ward_code",
                "area_sq_km"
            ]
        ],
        on="ward_code",
        how="left"
    )

    summary["police_stations_per_100k_population"] = (
        summary["police_station_count"]
        /
        summary["population_2011"]
        * 100000
    )

    summary["police_stations_per_10_sq_km"] = (
        summary["police_station_count"]
        /
        summary["area_sq_km"]
        * 10
    )

    summary["population_per_police_station"] = (
        summary["population_2011"]
        /
        summary["police_station_count"]
    )

    # No police station should produce an artificial
    # population-per-station value.
    summary.loc[
        summary["police_station_count"] == 0,
        "population_per_police_station"
    ] = pd.NA

    summary = summary.sort_values(
        "ward_code"
    ).reset_index(drop=True)

    OUT.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    summary.to_csv(
        OUT,
        index=False
    )

    print("\nPolice Ward Summary")
    print("-------------------")

    print(
        f"Wards: {len(summary)}"
    )

    print(
        f"Police locations: "
        f"{summary['police_location_count'].sum()}"
    )

    print(
        f"Police stations: "
        f"{summary['police_station_count'].sum()}"
    )

    print(
        f"Police offices: "
        f"{summary['police_office_count'].sum()}"
    )

    print(
        f"Traffic chowkis: "
        f"{summary['traffic_chowki_count'].sum()}"
    )

    print(
        f"Control rooms: "
        f"{summary['police_control_room_count'].sum()}"
    )

    print(
        f"Wards with police stations: "
        f"{(summary['police_station_count'] > 0).sum()}"
    )

    print(
        f"Wards with zero police stations: "
        f"{(summary['police_station_count'] == 0).sum()}"
    )

    print("\nWard summary:")

    print(
        summary[
            [
                "ward_code",
                "police_location_count",
                "police_station_count",
                "police_office_count",
                "traffic_chowki_count",
                "police_control_room_count"
            ]
        ].to_string(index=False)
    )

    print(f"\nOutput: {OUT}")


if __name__ == "__main__":
    main()

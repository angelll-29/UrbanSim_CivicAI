import pandas as pd
from pathlib import Path


BASE = Path(
    "data/processed/mumbai_ward_civic_intelligence_base_transport.csv"
)

RAILWAY = Path(
    "data/processed/mumbai_suburban_railway_ward_summary.csv"
)

OUTPUT = Path(
    "data/processed/mumbai_ward_civic_intelligence_base_multimodal.csv"
)


def main():

    print("\n========================================")
    print("MULTIMODAL TRANSPORT INTEGRATION")
    print("========================================")

    base = pd.read_csv(BASE)
    railway = pd.read_csv(RAILWAY)

    print(f"Base wards loaded    : {len(base)}")
    print(f"Railway wards loaded : {len(railway)}")

    # ---------------------------------------------------------
    # Validate ward coverage
    # ---------------------------------------------------------

    base_wards = set(base["ward_code"])
    railway_wards = set(railway["ward_code"])

    missing_in_railway = base_wards - railway_wards
    extra_in_railway = railway_wards - base_wards

    if missing_in_railway:
        print(
            f"WARNING: Missing railway wards: "
            f"{sorted(missing_in_railway)}"
        )

    if extra_in_railway:
        print(
            f"WARNING: Extra railway wards: "
            f"{sorted(extra_in_railway)}"
        )

    # ---------------------------------------------------------
    # Merge
    # ---------------------------------------------------------

    railway_features = [
        "ward_code",
        "railway_station_count",
        "existing_railway_station_count",
        "proposed_railway_station_count",
        "western_railway_station_count",
        "central_railway_station_count",
        "harbour_railway_station_count",
    ]

    railway = railway[railway_features]

    merged = base.merge(
        railway,
        on="ward_code",
        how="left",
        validate="one_to_one"
    )

    # ---------------------------------------------------------
    # Fill railway ward counts
    # ---------------------------------------------------------

    count_columns = [
        "railway_station_count",
        "existing_railway_station_count",
        "proposed_railway_station_count",
        "western_railway_station_count",
        "central_railway_station_count",
        "harbour_railway_station_count",
    ]

    merged[count_columns] = (
        merged[count_columns]
        .fillna(0)
        .astype(int)
    )

    # ---------------------------------------------------------
    # Multimodal transport indicators
    # ---------------------------------------------------------

    merged["total_public_transport_nodes"] = (
        merged["bus_stop_count"]
        + merged["bus_depot_count"]
        + merged["railway_station_count"]
    )

    merged["railway_presence"] = (
        merged["railway_station_count"] > 0
    ).astype(int)

    merged["multimodal_presence"] = (
        (
            merged["bus_stop_count"] > 0
        )
        & (
            merged["railway_station_count"] > 0
        )
    ).astype(int)

    # ---------------------------------------------------------
    # Save
    # ---------------------------------------------------------

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    merged.to_csv(
        OUTPUT,
        index=False
    )

    # ---------------------------------------------------------
    # Results
    # ---------------------------------------------------------

    print("\n----------------------------------------")
    print("INTEGRATION RESULTS")
    print("----------------------------------------")

    print(f"Output wards : {len(merged)}")
    print(f"Output cols  : {len(merged.columns)}")

    print(
        f"Railway stations integrated: "
        f"{merged['railway_station_count'].sum()}"
    )

    print(
        f"Bus stops integrated: "
        f"{merged['bus_stop_count'].sum()}"
    )

    print(
        f"Bus depots integrated: "
        f"{merged['bus_depot_count'].sum()}"
    )

    print(
        f"Public transport nodes: "
        f"{merged['total_public_transport_nodes'].sum()}"
    )

    print(
        f"Wards with railway: "
        f"{merged['railway_presence'].sum()}/24"
    )

    print(
        f"Wards with bus + railway: "
        f"{merged['multimodal_presence'].sum()}/24"
    )

    print("\nRailway stations by ward:")

    print(
        merged[
            [
                "ward_code",
                "bus_stop_count",
                "railway_station_count",
                "bus_depot_count",
                "total_public_transport_nodes",
            ]
        ].to_string(index=False)
    )

    print("\nOutput:")
    print(OUTPUT)


if __name__ == "__main__":
    main()
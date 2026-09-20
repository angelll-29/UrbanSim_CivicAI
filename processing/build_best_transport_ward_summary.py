from pathlib import Path

import pandas as pd


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "mumbai_best_transport_validated.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "mumbai_best_transport_ward_summary.csv"
)


# ---------------------------------------------------------
# Official BMC wards
# ---------------------------------------------------------
EXPECTED_WARDS = [
    "A", "B", "C", "D", "E",
    "FN", "FS", "GN", "GS",
    "HE", "HW", "KE", "KW",
    "L", "ME", "MW", "N",
    "PN", "PS", "RC", "RN",
    "RS", "S", "T"
]


def main():

    print("=" * 60)
    print("UrbanSim Civic AI - BEST Transport Ward Summary")
    print("=" * 60)

    # -----------------------------------------------------
    # Read validated transport data
    # -----------------------------------------------------

    df = pd.read_csv(INPUT_FILE)

    print(
        f"\nValidated transport records: {len(df)}"
    )

    # -----------------------------------------------------
    # Keep only GIS-matched Mumbai records
    # -----------------------------------------------------

    df = df[
        df["gis_ward"].notna()
    ].copy()

    df["gis_ward"] = (
        df["gis_ward"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    print(
        f"GIS-matched Mumbai records: {len(df)}"
    )

    # -----------------------------------------------------
    # Aggregate by ward
    # -----------------------------------------------------

    summary = (
        df.groupby("gis_ward")
        .agg(
            total_best_features=(
                "transport_id",
                "count"
            ),

            bus_stop_count=(
                "transport_type",
                lambda x: (
                    x == "BUS_STOP"
                ).sum()
            ),

            bus_depot_count=(
                "transport_type",
                lambda x: (
                    x == "BUS_DEPOT"
                ).sum()
            )
        )
        .reset_index()
        .rename(
            columns={
                "gis_ward": "ward_code"
            }
        )
    )

    # -----------------------------------------------------
    # Ensure all 24 wards are present
    # -----------------------------------------------------

    wards = pd.DataFrame({
        "ward_code": EXPECTED_WARDS
    })

    summary = wards.merge(
        summary,
        on="ward_code",
        how="left"
    )

    # -----------------------------------------------------
    # Fill missing counts only
    # -----------------------------------------------------

    count_columns = [
        "total_best_features",
        "bus_stop_count",
        "bus_depot_count"
    ]

    for column in count_columns:

        summary[column] = (
            summary[column]
            .fillna(0)
            .astype(int)
        )

    # -----------------------------------------------------
    # Validation
    # -----------------------------------------------------

    print("\nValidation:")

    print(
        f"Wards: "
        f"{summary['ward_code'].nunique()}"
    )

    print(
        f"Total BEST features: "
        f"{summary['total_best_features'].sum()}"
    )

    print(
        f"Total bus stops: "
        f"{summary['bus_stop_count'].sum()}"
    )

    print(
        f"Total bus depots: "
        f"{summary['bus_depot_count'].sum()}"
    )

    print(
        f"Missing values: "
        f"{summary.isna().sum().sum()}"
    )

    # -----------------------------------------------------
    # Save
    # -----------------------------------------------------

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    summary.to_csv(
        OUTPUT_FILE,
        index=False
    )

    # -----------------------------------------------------
    # Display
    # -----------------------------------------------------

    print("\nWard summary:")

    print(
        summary.to_string(
            index=False
        )
    )

    print("\nOutput:")

    print(OUTPUT_FILE)

    print("\n" + "=" * 60)
    print("BEST TRANSPORT WARD SUMMARY COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
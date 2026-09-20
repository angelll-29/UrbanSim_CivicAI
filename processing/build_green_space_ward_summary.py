from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "mumbai_green_spaces_validated.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "mumbai_green_space_ward_summary.csv"
)


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
    print("UrbanSim Civic AI - Green Space Ward Summary")
    print("=" * 60)

    df = pd.read_csv(INPUT_FILE)

    print(
        f"\nValidated green-space records: {len(df)}"
    )

    # Only spatially matched records
    df = df[
        df["gis_ward"].notna()
    ].copy()

    # Normalize ward codes
    df["gis_ward"] = (
        df["gis_ward"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    # -----------------------------------------------------
    # Aggregate
    # -----------------------------------------------------

    summary = (
        df.groupby("gis_ward")
        .agg(
            green_space_count=(
                "green_space_id",
                "count"
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
    # Ensure all 24 BMC wards exist
    # -----------------------------------------------------

    ward_frame = pd.DataFrame({
        "ward_code": EXPECTED_WARDS
    })

    summary = ward_frame.merge(
        summary,
        on="ward_code",
        how="left"
    )

    summary["green_space_count"] = (
        summary["green_space_count"]
        .fillna(0)
        .astype(int)
    )

    # -----------------------------------------------------
    # Density by 100 green-space locations
    # -----------------------------------------------------

    total_green_spaces = (
        summary["green_space_count"].sum()
    )

    if total_green_spaces > 0:

        summary["green_space_share_pct"] = (
            summary["green_space_count"]
            / total_green_spaces
            * 100
        )

    else:

        summary["green_space_share_pct"] = 0

    # -----------------------------------------------------
    # Validation
    # -----------------------------------------------------

    print("\nValidation:")

    print(
        f"Wards: "
        f"{summary['ward_code'].nunique()}"
    )

    print(
        f"Total matched green spaces: "
        f"{summary['green_space_count'].sum()}"
    )

    print(
        "Missing ward indicators:",
        summary.isna().sum().sum()
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
        summary.to_string(index=False)
    )

    print("\nOutput:")

    print(OUTPUT_FILE)

    print("\n" + "=" * 60)
    print("GREEN SPACE WARD SUMMARY COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
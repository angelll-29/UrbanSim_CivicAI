import pandas as pd
from pathlib import Path


INPUT = Path(
    "data/processed/mumbai_suburban_railway_stations_validated.csv"
)

OUTPUT = Path(
    "data/processed/mumbai_suburban_railway_ward_summary.csv"
)


BMC_WARDS = [
    "A", "B", "C", "D", "E",
    "FN", "FS",
    "GN", "GS",
    "HE", "HW",
    "KE", "KW",
    "L",
    "ME", "MW",
    "N",
    "PN", "PS",
    "RC", "RN", "RS",
    "S", "T"
]


def main():

    print("\n========================================")
    print("SUBURBAN RAILWAY WARD SUMMARY")
    print("========================================")

    df = pd.read_csv(INPUT)

    # Only stations spatially inside BMC wards
    matched = df[
        df["ward_match_status"] == "MATCHED"
    ].copy()

    print(f"Total railway stations : {len(df)}")
    print(f"Matched to BMC wards   : {len(matched)}")
    print(f"Excluded from wards    : {len(df) - len(matched)}")

    # ---------------------------------------------------------
    # Existing / proposed
    # ---------------------------------------------------------

    matched["is_existing"] = (
        matched["station_type"]
        == "Suburban Station"
    ).astype(int)

    matched["is_proposed"] = (
        matched["station_type"]
        == "Proposed Suburban Station"
    ).astype(int)

    # ---------------------------------------------------------
    # Region indicators
    # ---------------------------------------------------------

    matched["western_count"] = (
        matched["region"] == "WESTERN"
    ).astype(int)

    matched["central_count"] = (
        matched["region"] == "CENTRAL"
    ).astype(int)

    matched["harbour_count"] = (
        matched["region"] == "HARBOUR"
    ).astype(int)

    # ---------------------------------------------------------
    # Aggregate
    # ---------------------------------------------------------

    summary = (
        matched
        .groupby("gis_ward")
        .agg(
            railway_station_count=(
                "station_id",
                "count"
            ),

            existing_railway_station_count=(
                "is_existing",
                "sum"
            ),

            proposed_railway_station_count=(
                "is_proposed",
                "sum"
            ),

            western_railway_station_count=(
                "western_count",
                "sum"
            ),

            central_railway_station_count=(
                "central_count",
                "sum"
            ),

            harbour_railway_station_count=(
                "harbour_count",
                "sum"
            )
        )
        .reset_index()
        .rename(
            columns={
                "gis_ward": "ward_code"
            }
        )
    )

    # ---------------------------------------------------------
    # Ensure all 24 BMC wards exist
    # ---------------------------------------------------------

    ward_frame = pd.DataFrame({
        "ward_code": BMC_WARDS
    })

    summary = ward_frame.merge(
        summary,
        on="ward_code",
        how="left"
    )

    numeric_columns = [
        "railway_station_count",
        "existing_railway_station_count",
        "proposed_railway_station_count",
        "western_railway_station_count",
        "central_railway_station_count",
        "harbour_railway_station_count"
    ]

    summary[numeric_columns] = (
        summary[numeric_columns]
        .fillna(0)
        .astype(int)
    )

    # ---------------------------------------------------------
    # Save
    # ---------------------------------------------------------

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    summary.to_csv(
        OUTPUT,
        index=False
    )

    # ---------------------------------------------------------
    # Print
    # ---------------------------------------------------------

    print("\nWard summary:")
    print(summary.to_string(index=False))

    print("\n----------------------------------------")
    print("TOTALS")
    print("----------------------------------------")

    for column in numeric_columns:
        print(
            f"{column}: "
            f"{summary[column].sum()}"
        )

    print("\nOutput:")
    print(OUTPUT)


if __name__ == "__main__":
    main()
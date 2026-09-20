from pathlib import Path
import pandas as pd

INPUT = Path(
    "data/processed/mumbai_fire_stations_validated.csv"
)

OUTPUT = Path(
    "data/processed/mumbai_fire_station_ward_summary.csv"
)

WARD_CODES = [
    "A", "B", "C", "D", "E",
    "FN", "FS", "GN", "GS",
    "HE", "HW", "KE", "KW",
    "L", "ME", "MW", "N",
    "PN", "PS", "RC", "RN",
    "RS", "S", "T"
]


def main():

    df = pd.read_csv(INPUT)

    df = df[
        df["urban_ward_code"].notna()
    ].copy()

    summary = (
        df.groupby("urban_ward_code")
        .agg(
            fire_station_count=(
                "fire_station_id",
                "count"
            )
        )
        .reset_index()
        .rename(
            columns={
                "urban_ward_code": "ward_code"
            }
        )
    )

    # Ensure all 24 BMC wards exist
    wards = pd.DataFrame(
        {"ward_code": WARD_CODES}
    )

    summary = wards.merge(
        summary,
        on="ward_code",
        how="left"
    )

    summary["fire_station_count"] = (
        summary["fire_station_count"]
        .fillna(0)
        .astype(int)
    )

    summary.to_csv(
        OUTPUT,
        index=False
    )

    print("\nFire Station Ward Summary")
    print("--------------------------------")

    print(
        f"Wards: {len(summary)}"
    )

    print(
        f"Fire stations: "
        f"{summary['fire_station_count'].sum()}"
    )

    print("\nWard summary:")
    print(
        summary.to_string(index=False)
    )

    print("\nOutput:")
    print(OUTPUT)


if __name__ == "__main__":
    main()
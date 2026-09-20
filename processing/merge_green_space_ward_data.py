from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

BASE_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "mumbai_ward_civic_intelligence_base.csv"
)

GREEN_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "mumbai_green_space_ward_summary.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "mumbai_ward_civic_intelligence_base_green.csv"
)


EXPECTED_WARDS = [
    "A", "B", "C", "D", "E",
    "FN", "FS", "GN", "GS",
    "HE", "HW", "KE", "KW",
    "L", "ME", "MW", "N",
    "PN", "PS", "RC", "RN",
    "RS", "S", "T"
]


def normalize_ward(value):
    return (
        str(value)
        .strip()
        .upper()
    )


def main():

    print("=" * 60)
    print("UrbanSim Civic AI - Green Space Integration")
    print("=" * 60)

    # -----------------------------------------------------
    # Read
    # -----------------------------------------------------

    base = pd.read_csv(BASE_FILE)
    green = pd.read_csv(GREEN_FILE)

    print(f"\nBase rows:   {len(base)}")
    print(f"Green rows:  {len(green)}")

    # -----------------------------------------------------
    # Normalize ward codes
    # -----------------------------------------------------

    base["ward_code"] = (
        base["ward_code"]
        .apply(normalize_ward)
    )

    green["ward_code"] = (
        green["ward_code"]
        .apply(normalize_ward)
    )

    # -----------------------------------------------------
    # Validate ward coverage
    # -----------------------------------------------------

    base_wards = set(base["ward_code"])
    green_wards = set(green["ward_code"])

    expected = set(EXPECTED_WARDS)

    print("\nWard coverage:")

    print(
        f"Expected: {len(expected)}"
    )

    print(
        f"Base:     {len(base_wards)}"
    )

    print(
        f"Green:    {len(green_wards)}"
    )

    missing_base = expected - base_wards
    missing_green = expected - green_wards

    if missing_base:
        raise ValueError(
            f"Missing wards in base: {missing_base}"
        )

    if missing_green:
        raise ValueError(
            f"Missing wards in green data: {missing_green}"
        )

    # -----------------------------------------------------
    # Check duplicates
    # -----------------------------------------------------

    if base["ward_code"].duplicated().any():
        raise ValueError(
            "Duplicate wards found in base dataset."
        )

    if green["ward_code"].duplicated().any():
        raise ValueError(
            "Duplicate wards found in green dataset."
        )

    # -----------------------------------------------------
    # Select green indicators
    # -----------------------------------------------------

    green = green[
        [
            "ward_code",
            "green_space_count",
            "green_space_share_pct"
        ]
    ]

    # -----------------------------------------------------
    # Merge
    # -----------------------------------------------------

    merged = base.merge(
        green,
        on="ward_code",
        how="left",
        validate="one_to_one"
    )

    # -----------------------------------------------------
    # Validate merge
    # -----------------------------------------------------

    if len(merged) != len(base):
        raise ValueError(
            "Merge changed the number of ward rows."
        )

    indicator_columns = [
        "green_space_count",
        "green_space_share_pct"
    ]

    missing = merged[
        indicator_columns
    ].isna().sum()

    print("\nMissing green indicators:")
    print(missing)

    if missing.sum() > 0:
        raise ValueError(
            "Missing values detected after green-space merge."
        )

    # -----------------------------------------------------
    # Save
    # -----------------------------------------------------

    merged.to_csv(
        OUTPUT_FILE,
        index=False
    )

    # -----------------------------------------------------
    # Summary
    # -----------------------------------------------------

    print("\n" + "=" * 60)
    print("GREEN SPACE INTEGRATION COMPLETE")
    print("=" * 60)

    print(
        f"Wards:             {len(merged)}"
    )

    print(
        f"Columns:           {len(merged.columns)}"
    )

    print(
        f"Green locations:   "
        f"{merged['green_space_count'].sum()}"
    )

    print(
        f"Output:            {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()
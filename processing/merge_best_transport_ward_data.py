from pathlib import Path

import pandas as pd


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]

BASE_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "mumbai_ward_civic_intelligence_base_green.csv"
)

TRANSPORT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "mumbai_best_transport_ward_summary.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "mumbai_ward_civic_intelligence_base_transport.csv"
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
    print("UrbanSim Civic AI - BEST Transport Integration")
    print("=" * 60)

    # -----------------------------------------------------
    # Read
    # -----------------------------------------------------

    base = pd.read_csv(BASE_FILE)

    transport = pd.read_csv(
        TRANSPORT_FILE
    )

    print(
        f"\nBase rows:       {len(base)}"
    )

    print(
        f"Transport rows:  {len(transport)}"
    )

    # -----------------------------------------------------
    # Normalize ward codes
    # -----------------------------------------------------

    base["ward_code"] = (
        base["ward_code"]
        .apply(normalize_ward)
    )

    transport["ward_code"] = (
        transport["ward_code"]
        .apply(normalize_ward)
    )

    # -----------------------------------------------------
    # Ward coverage
    # -----------------------------------------------------

    expected = set(EXPECTED_WARDS)

    base_wards = set(
        base["ward_code"]
    )

    transport_wards = set(
        transport["ward_code"]
    )

    print("\nWard coverage:")

    print(
        f"Expected:    {len(expected)}"
    )

    print(
        f"Base:        {len(base_wards)}"
    )

    print(
        f"Transport:   {len(transport_wards)}"
    )

    missing_base = (
        expected - base_wards
    )

    missing_transport = (
        expected - transport_wards
    )

    if missing_base:

        raise ValueError(
            f"Missing wards in base: "
            f"{missing_base}"
        )

    if missing_transport:

        raise ValueError(
            f"Missing wards in transport: "
            f"{missing_transport}"
        )

    # -----------------------------------------------------
    # Duplicate validation
    # -----------------------------------------------------

    if base["ward_code"].duplicated().any():

        raise ValueError(
            "Duplicate wards found in base dataset."
        )

    if transport["ward_code"].duplicated().any():

        raise ValueError(
            "Duplicate wards found in transport dataset."
        )

    # -----------------------------------------------------
    # Select transport indicators
    # -----------------------------------------------------

    transport = transport[
        [
            "ward_code",
            "total_best_features",
            "bus_stop_count",
            "bus_depot_count"
        ]
    ]

    # -----------------------------------------------------
    # Merge
    # -----------------------------------------------------

    merged = base.merge(
        transport,
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
        "total_best_features",
        "bus_stop_count",
        "bus_depot_count"
    ]

    missing = (
        merged[indicator_columns]
        .isna()
        .sum()
    )

    print("\nMissing transport indicators:")

    print(missing)

    if missing.sum() > 0:

        raise ValueError(
            "Missing transport indicators "
            "after merge."
        )

    # -----------------------------------------------------
    # Save
    # -----------------------------------------------------

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    merged.to_csv(
        OUTPUT_FILE,
        index=False
    )

    # -----------------------------------------------------
    # Summary
    # -----------------------------------------------------

    print("\n" + "=" * 60)
    print("BEST TRANSPORT INTEGRATION COMPLETE")
    print("=" * 60)

    print(
        f"Wards:              {len(merged)}"
    )

    print(
        f"Columns:            {len(merged.columns)}"
    )

    print(
        f"Bus stops:           "
        f"{merged['bus_stop_count'].sum()}"
    )

    print(
        f"Bus depots:          "
        f"{merged['bus_depot_count'].sum()}"
    )

    print(
        f"BEST features:       "
        f"{merged['total_best_features'].sum()}"
    )

    print(
        f"Output:              {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()
from pathlib import Path

import pandas as pd
import geopandas as gpd


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]

GREEN_SPACE_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "mumbai_green_spaces.csv"
)

WARD_FILE = (
    PROJECT_ROOT
    / "data"
    / "spatial"
    / "mumbai_wards.geojson"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "mumbai_green_spaces_validated.csv"
)

MISMATCH_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "green_space_ward_mismatches.csv"
)

GEOJSON_OUTPUT = (
    PROJECT_ROOT
    / "data"
    / "spatial"
    / "mumbai_green_spaces_validated.geojson"
)


# ---------------------------------------------------------
# Ward normalization
# ---------------------------------------------------------
WARD_NORMALIZATION = {
    "H/E": "HE",
    "H/W": "HW",
    "K/E": "KE",
    "K/W": "KW",
    "M/E": "ME",
    "M/W": "MW",
    "P/N": "PN",
    "P/S": "PS",
    "R/C": "RC",
    "R/N": "RN",
    "R/S": "RS",
    "F/N": "FN",
    "F/S": "FS",
    "G/N": "GN",
    "G/S": "GS",
}


def normalize_ward(value):
    if pd.isna(value):
        return None

    value = str(value)
    value = value.replace("\r", "")
    value = value.replace("\n", "")
    value = value.replace("\t", "")
    value = value.strip().upper()

    return WARD_NORMALIZATION.get(
        value,
        value
    )


def main():

    print("=" * 60)
    print("UrbanSim Civic AI - Green Space GIS Validation")
    print("=" * 60)

    # -----------------------------------------------------
    # Read data
    # -----------------------------------------------------

    print("\nReading green spaces...")

    df = pd.read_csv(
        GREEN_SPACE_FILE
    )

    print(
        f"Green space records: {len(df)}"
    )

    print("\nReading Mumbai ward polygons...")

    wards = gpd.read_file(
        WARD_FILE
    )

    print(
        f"Ward polygons: {len(wards)}"
    )

    # -----------------------------------------------------
    # Validate coordinate availability
    # -----------------------------------------------------

    valid_coordinates = (
        df["latitude"].notna()
        & df["longitude"].notna()
    )

    spatial_df = df[
        valid_coordinates
    ].copy()

    print(
        f"Records with coordinates: "
        f"{len(spatial_df)}"
    )

    # -----------------------------------------------------
    # Create GeoDataFrame
    # -----------------------------------------------------

    green_spaces = gpd.GeoDataFrame(
        spatial_df,
        geometry=gpd.points_from_xy(
            spatial_df["longitude"],
            spatial_df["latitude"]
        ),
        crs="EPSG:4326"
    )

    # -----------------------------------------------------
    # Prepare ward polygons
    # -----------------------------------------------------

    wards = wards.to_crs(
        green_spaces.crs
    )

    ward_column = "Name"

    if ward_column not in wards.columns:
        raise ValueError(
            f"Ward column '{ward_column}' "
            f"not found. Available columns: "
            f"{list(wards.columns)}"
        )

    wards["gis_ward"] = (
        wards[ward_column]
        .apply(normalize_ward)
    )

    # -----------------------------------------------------
    # Spatial join
    # -----------------------------------------------------

    print("\nPerforming spatial join...")

    joined = gpd.sjoin(
        green_spaces,
        wards[
            ["gis_ward", "geometry"]
        ],
        how="left",
        predicate="within"
    )

    # -----------------------------------------------------
    # Preserve source ward
    # -----------------------------------------------------

    joined["ward_code_source"] = (
        joined["ward_code_source"]
        .apply(normalize_ward)
    )

    joined["gis_ward"] = (
        joined["gis_ward"]
        .apply(normalize_ward)
    )

    # -----------------------------------------------------
    # Validation status
    # -----------------------------------------------------

    joined["validation_status"] = "GIS_MATCH"

    joined.loc[
        joined["gis_ward"].isna(),
        "validation_status"
    ] = "UNMATCHED"

    joined.loc[
        (
            joined["ward_code_source"].notna()
            &
            joined["gis_ward"].notna()
            &
            (
                joined["ward_code_source"]
                != joined["gis_ward"]
            )
        ),
        "validation_status"
    ] = "WARD_MISMATCH"

    # -----------------------------------------------------
    # Save mismatch records
    # -----------------------------------------------------

    mismatches = joined[
        joined["validation_status"]
        == "WARD_MISMATCH"
    ].copy()

    mismatches[
        [
            "green_space_id",
            "green_space_name",
            "ward_code_source",
            "gis_ward",
            "latitude",
            "longitude",
            "validation_status"
        ]
    ].to_csv(
        MISMATCH_FILE,
        index=False
    )

    # -----------------------------------------------------
    # Remove spatial join helper columns
    # -----------------------------------------------------

    if "index_right" in joined.columns:
        joined = joined.drop(
            columns=["index_right"]
        )

    # -----------------------------------------------------
    # Save CSV
    # -----------------------------------------------------

    output_df = pd.DataFrame(
        joined.drop(
            columns=["geometry"]
        )
    )

    output_df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    # -----------------------------------------------------
    # Save GeoJSON
    # -----------------------------------------------------

    joined.to_file(
        GEOJSON_OUTPUT,
        driver="GeoJSON"
    )

    # -----------------------------------------------------
    # Summary
    # -----------------------------------------------------

    total = len(joined)

    matched = (
        joined["gis_ward"].notna()
    ).sum()

    unmatched = (
        joined["gis_ward"].isna()
    ).sum()

    source_ward_present = (
        joined["ward_code_source"].notna()
    ).sum()

    print("\n" + "=" * 60)
    print("GIS VALIDATION COMPLETE")
    print("=" * 60)

    print(
        f"Total spatial records:     {total}"
    )

    print(
        f"GIS ward matches:          {matched}"
    )

    print(
        f"Unmatched:                 {unmatched}"
    )

    print(
        f"Source wards available:    "
        f"{source_ward_present}"
    )

    print(
        f"Source/GIS mismatches:     "
        f"{len(mismatches)}"
    )

    if total > 0:
        print(
            f"GIS match rate:            "
            f"{matched / total * 100:.2f}%"
        )

    print("\nGIS ward distribution:")

    print(
        joined["gis_ward"]
        .value_counts(dropna=False)
        .sort_index()
    )

    print("\nOutputs:")

    print(
        f"CSV:       {OUTPUT_FILE}"
    )

    print(
        f"Mismatches:{MISMATCH_FILE}"
    )

    print(
        f"GeoJSON:   {GEOJSON_OUTPUT}"
    )


if __name__ == "__main__":
    main()
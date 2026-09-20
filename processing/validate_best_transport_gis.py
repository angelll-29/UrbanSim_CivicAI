from pathlib import Path

import pandas as pd
import geopandas as gpd


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]

TRANSPORT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "mumbai_best_transport.csv"
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
    / "mumbai_best_transport_validated.csv"
)

MISMATCH_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "best_transport_ward_mismatches.csv"
)

GEOJSON_OUTPUT = (
    PROJECT_ROOT
    / "data"
    / "spatial"
    / "mumbai_best_transport_validated.geojson"
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


EXPECTED_WARDS = {
    "A", "B", "C", "D", "E",
    "FN", "FS", "GN", "GS",
    "HE", "HW", "KE", "KW",
    "L", "ME", "MW", "N",
    "PN", "PS", "RC", "RN",
    "RS", "S", "T"
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
    print("UrbanSim Civic AI - BEST Transport GIS Validation")
    print("=" * 60)

    # -----------------------------------------------------
    # Read transport data
    # -----------------------------------------------------

    print("\nReading BEST transport data...")

    transport = pd.read_csv(
        TRANSPORT_FILE
    )

    print(
        f"Transport records: {len(transport)}"
    )

    # -----------------------------------------------------
    # Read ward polygons
    # -----------------------------------------------------

    print("\nReading Mumbai ward polygons...")

    wards = gpd.read_file(
        WARD_FILE
    )

    print(
        f"Ward polygons: {len(wards)}"
    )

    # -----------------------------------------------------
    # Coordinate validation
    # -----------------------------------------------------

    transport = transport[
        transport["coordinate_valid"] == True
    ].copy()

    print(
        f"Records with valid coordinates: "
        f"{len(transport)}"
    )

    # -----------------------------------------------------
    # Create GeoDataFrame
    # -----------------------------------------------------

    transport_gdf = gpd.GeoDataFrame(
        transport,
        geometry=gpd.points_from_xy(
            transport["longitude"],
            transport["latitude"]
        ),
        crs="EPSG:4326"
    )

    # -----------------------------------------------------
    # Match CRS
    # -----------------------------------------------------

    wards = wards.to_crs(
        transport_gdf.crs
    )

    # -----------------------------------------------------
    # Identify ward column
    # -----------------------------------------------------

    if "Name" not in wards.columns:

        raise ValueError(
            "'Name' column not found in ward dataset.\n"
            f"Available columns: {list(wards.columns)}"
        )

    wards["gis_ward"] = (
        wards["Name"]
        .apply(normalize_ward)
    )

    # -----------------------------------------------------
    # Check ward values
    # -----------------------------------------------------

    unexpected = (
        set(
            wards["gis_ward"]
            .dropna()
        )
        - EXPECTED_WARDS
    )

    if unexpected:

        print(
            "\nWARNING: Unexpected ward codes:"
        )

        print(unexpected)

    # -----------------------------------------------------
    # Spatial join
    # -----------------------------------------------------

    print("\nPerforming spatial join...")

    joined = gpd.sjoin(
        transport_gdf,
        wards[
            [
                "gis_ward",
                "geometry"
            ]
        ],
        how="left",
        predicate="within"
    )

    # -----------------------------------------------------
    # Normalize source ward
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
    # Mismatch records
    # -----------------------------------------------------

    mismatches = joined[
        joined["validation_status"]
        == "WARD_MISMATCH"
    ].copy()

    mismatches[
        [
            "transport_id",
            "object_id",
            "transport_name",
            "transport_type",
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
    # Remove spatial join helper
    # -----------------------------------------------------

    if "index_right" in joined.columns:

        joined = joined.drop(
            columns=["index_right"]
        )

    # -----------------------------------------------------
    # Save CSV
    # -----------------------------------------------------

    joined.drop(
        columns=["geometry"]
    ).to_csv(
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

    source_present = (
        joined["ward_code_source"].notna()
    ).sum()

    bus_stops = (
        joined["transport_type"]
        == "BUS_STOP"
    ).sum()

    bus_depots = (
        joined["transport_type"]
        == "BUS_DEPOT"
    ).sum()

    print("\n" + "=" * 60)
    print("BEST TRANSPORT GIS VALIDATION COMPLETE")
    print("=" * 60)

    print(
        f"Total spatial records:   {total}"
    )

    print(
        f"GIS ward matches:        {matched}"
    )

    print(
        f"Unmatched:               {unmatched}"
    )

    print(
        f"Source wards available:  {source_present}"
    )

    print(
        f"Source/GIS mismatches:   {len(mismatches)}"
    )

    if total > 0:

        print(
            f"GIS match rate:          "
            f"{matched / total * 100:.2f}%"
        )

    print("\nTransport types:")

    print(
        f"BUS_STOP:                {bus_stops}"
    )

    print(
        f"BUS_DEPOT:               {bus_depots}"
    )

    print("\nGIS ward distribution:")

    print(
        joined["gis_ward"]
        .value_counts(
            dropna=False
        )
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

    print("\n" + "=" * 60)


if __name__ == "__main__":

    main()
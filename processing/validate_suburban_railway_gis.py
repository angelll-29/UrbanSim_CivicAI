import pandas as pd
import geopandas as gpd
from pathlib import Path


STATIONS = Path(
    "data/processed/mumbai_suburban_railway_stations.csv"
)

WARDS = Path(
    "data/spatial/mumbai_wards.geojson"
)

OUTPUT_CSV = Path(
    "data/processed/mumbai_suburban_railway_stations_validated.csv"
)

MISMATCH_CSV = Path(
    "data/processed/suburban_railway_station_ward_mismatches.csv"
)

OUTPUT_GEOJSON = Path(
    "data/spatial/mumbai_suburban_railway_stations_validated.geojson"
)


def find_ward_column(gdf):
    """
    Detect the BMC ward-code/name field in the ward GeoJSON.
    """

    candidates = [
        "ward_code",
        "Ward_Code",
        "WARD_CODE",
        "ward",
        "Ward",
        "WARD",
        "name",
        "Name",
        "NAME",
    ]

    for col in candidates:
        if col in gdf.columns:
            return col

    raise ValueError(
        f"Could not identify ward column. Available columns: {list(gdf.columns)}"
    )


def normalize_ward(value):
    """
    Normalize common BMC ward naming formats.
    """

    if pd.isna(value):
        return None

    value = str(value).strip().upper()

    replacements = {
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

    return replacements.get(value, value)


def main():

    print("\n========================================")
    print("SUBURBAN RAILWAY GIS VALIDATION")
    print("========================================")

    # ---------------------------------------------------------
    # Load stations
    # ---------------------------------------------------------

    df = pd.read_csv(STATIONS)

    print(f"Railway stations loaded: {len(df)}")

    stations = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(
            df["longitude"],
            df["latitude"]
        ),
        crs="EPSG:4326"
    )

    # ---------------------------------------------------------
    # Load wards
    # ---------------------------------------------------------

    wards = gpd.read_file(WARDS)

    print(f"BMC ward polygons loaded: {len(wards)}")
    print(f"Ward CRS: {wards.crs}")

    ward_column = find_ward_column(wards)

    print(f"Ward field detected: {ward_column}")

    # Make sure both datasets use same CRS
    if wards.crs != stations.crs:
        wards = wards.to_crs(stations.crs)

    # ---------------------------------------------------------
    # Spatial join
    # ---------------------------------------------------------

    ward_join = wards[[ward_column, "geometry"]].copy()

    ward_join["gis_ward"] = ward_join[ward_column].apply(
        normalize_ward
    )

    joined = gpd.sjoin(
        stations,
        ward_join[["gis_ward", "geometry"]],
        how="left",
        predicate="within"
    )

    # Remove spatial join index
    if "index_right" in joined.columns:
        joined = joined.drop(columns=["index_right"])

    # ---------------------------------------------------------
    # Validate
    # ---------------------------------------------------------

    joined["gis_ward"] = joined["gis_ward"].apply(
        normalize_ward
    )

    joined["ward_match_status"] = joined["gis_ward"].apply(
        lambda x: "MATCHED" if pd.notna(x) else "UNMATCHED"
    )

    # ---------------------------------------------------------
    # Save CSV
    # ---------------------------------------------------------

    csv_df = pd.DataFrame(joined.drop(columns="geometry"))

    csv_df.to_csv(
        OUTPUT_CSV,
        index=False
    )

    # ---------------------------------------------------------
    # Mismatches / unmatched
    # ---------------------------------------------------------

    mismatches = csv_df[
        csv_df["ward_match_status"] == "UNMATCHED"
    ].copy()

    mismatches.to_csv(
        MISMATCH_CSV,
        index=False
    )

    # ---------------------------------------------------------
    # Save GeoJSON
    # ---------------------------------------------------------

    joined.to_file(
        OUTPUT_GEOJSON,
        driver="GeoJSON"
    )

    # ---------------------------------------------------------
    # Statistics
    # ---------------------------------------------------------

    total = len(joined)

    matched = (
        joined["ward_match_status"] == "MATCHED"
    ).sum()

    unmatched = (
        joined["ward_match_status"] == "UNMATCHED"
    ).sum()

    match_pct = (
        matched / total * 100
        if total
        else 0
    )

    print("\n----------------------------------------")
    print("VALIDATION RESULTS")
    print("----------------------------------------")

    print(f"Total stations : {total}")
    print(f"Matched wards  : {matched}")
    print(f"Unmatched      : {unmatched}")
    print(f"Match rate     : {match_pct:.2f}%")

    print("\nStations by GIS ward:")

    ward_counts = (
        joined[
            joined["gis_ward"].notna()
        ]["gis_ward"]
        .value_counts()
        .sort_index()
    )

    for ward, count in ward_counts.items():
        print(f"  {ward}: {count}")

    print("\nStation type by status:")

    print(
        pd.crosstab(
            joined["station_type"],
            joined["ward_match_status"]
        )
    )

    print("\nOutputs:")
    print(f"  CSV      : {OUTPUT_CSV}")
    print(f"  Mismatch : {MISMATCH_CSV}")
    print(f"  GeoJSON  : {OUTPUT_GEOJSON}")


if __name__ == "__main__":
    main()
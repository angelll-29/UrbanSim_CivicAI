from pathlib import Path
import pandas as pd
import geopandas as gpd

TOILETS = Path("data/processed/mumbai_public_toilets.csv")
WARDS = Path("data/spatial/mumbai_wards.geojson")

OUT_CSV = Path(
    "data/processed/mumbai_public_toilets_validated.csv"
)

MISMATCH_CSV = Path(
    "data/processed/public_toilet_ward_mismatches.csv"
)

OUT_GEOJSON = Path(
    "data/spatial/mumbai_public_toilets_validated.geojson"
)


def normalize_ward(value):
    if pd.isna(value):
        return None

    value = str(value).strip().upper()

    mapping = {
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

    return mapping.get(value, value)


def main():

    toilets = pd.read_csv(TOILETS)

    wards = gpd.read_file(WARDS)

    print(f"Toilets: {len(toilets)}")
    print(f"Ward polygons: {len(wards)}")
    print(f"Ward CRS: {wards.crs}")

    # Only spatially valid coordinates
    valid = toilets[
        toilets["coordinate_valid"] == True
    ].copy()

    valid["geometry"] = gpd.points_from_xy(
        valid["longitude"],
        valid["latitude"]
    )

    toilets_gdf = gpd.GeoDataFrame(
        valid,
        geometry="geometry",
        crs="EPSG:4326"
    )

    # Normalize source ward
    toilets_gdf["source_ward"] = (
        toilets_gdf["ward_code_source"]
        .apply(normalize_ward)
    )

    # Ensure ward layer uses WGS84
    wards = wards.to_crs("EPSG:4326")

    # Spatial join
    joined = gpd.sjoin(
        toilets_gdf,
        wards[["Name", "geometry"]],
        how="left",
        predicate="within"
    )

    joined = joined.rename(
        columns={"Name": "gis_ward"}
    )

    joined["gis_ward"] = (
    joined["gis_ward"]
    .astype("string")
    .str.replace(r"\s+", " ", regex=True)
    .str.strip()
    .apply(normalize_ward)
)
    
    # Remove spatial index column if present
    if "index_right" in joined.columns:
        joined = joined.drop(columns=["index_right"])

    # Match status
    joined["ward_match"] = (
        joined["source_ward"] == joined["gis_ward"]
    )

    joined.loc[
        joined["source_ward"].isna()
        | joined["gis_ward"].isna(),
        "ward_match"
    ] = False

    # GIS-derived final ward
    joined["urban_ward_code"] = joined["gis_ward"]

    # Identify mismatches
    mismatches = joined[
        joined["source_ward"] != joined["gis_ward"]
    ].copy()

    # Save mismatch report
    MISMATCH_CSV.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    mismatches.drop(
        columns="geometry"
    ).to_csv(
        MISMATCH_CSV,
        index=False
    )

    # Save validated CSV
    OUT_CSV.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    joined.drop(
        columns="geometry"
    ).to_csv(
        OUT_CSV,
        index=False
    )

    # Save GeoJSON
    joined.to_file(
        OUT_GEOJSON,
        driver="GeoJSON"
    )

    matched = (
        joined["gis_ward"].notna()
        & joined["source_ward"].notna()
        & joined["ward_match"]
    ).sum()

    source_missing = (
        joined["source_ward"].isna()
    ).sum()

    gis_missing = (
        joined["gis_ward"].isna()
    ).sum()

    mismatch_count = (
        (joined["source_ward"].notna())
        & (joined["gis_ward"].notna())
        & (~joined["ward_match"])
    ).sum()

    print("\nPublic Toilets GIS Validation")
    print("--------------------------------")

    print(f"Coordinate-valid toilets: {len(joined)}")
    print(f"GIS ward matched:         {matched}")
    print(f"Ward mismatches:          {mismatch_count}")
    print(f"Missing source ward:      {source_missing}")
    print(f"Outside BMC wards:        {gis_missing}")

    if len(joined) > 0:
        print(
            f"Match rate:               "
            f"{matched / len(joined) * 100:.2f}%"
        )

    print(f"\nValidated CSV:")
    print(OUT_CSV)

    print("\nMismatch report:")
    print(MISMATCH_CSV)

    print("\nValidated GeoJSON:")
    print(OUT_GEOJSON)


if __name__ == "__main__":
    main()
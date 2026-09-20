from pathlib import Path
import pandas as pd
import geopandas as gpd

POLICE = Path(
    "data/processed/mumbai_police_stations.csv"
)

WARDS = Path(
    "data/spatial/mumbai_wards.geojson"
)

OUT_CSV = Path(
    "data/processed/mumbai_police_stations_validated.csv"
)

MISMATCH_CSV = Path(
    "data/processed/police_station_ward_mismatches.csv"
)

OUT_GEOJSON = Path(
    "data/spatial/mumbai_police_stations_validated.geojson"
)


def normalize_ward(value):

    if pd.isna(value):
        return None

    value = str(value)
    value = value.replace("\n", " ")
    value = value.strip()
    value = value.replace(" ", "")

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

    police = pd.read_csv(POLICE)

    wards = gpd.read_file(WARDS)

    print(f"Police records: {len(police)}")
    print(f"Ward polygons:  {len(wards)}")
    print(f"Ward CRS:       {wards.crs}")

    valid = police[
        police["coordinate_valid"] == True
    ].copy()

    valid["geometry"] = gpd.points_from_xy(
        valid["longitude"],
        valid["latitude"]
    )

    police_gdf = gpd.GeoDataFrame(
        valid,
        geometry="geometry",
        crs="EPSG:4326"
    )

    police_gdf["source_ward"] = (
        police_gdf["ward_code_source"]
        .apply(normalize_ward)
    )

    wards = wards.to_crs("EPSG:4326")

    joined = gpd.sjoin(
        police_gdf,
        wards[["Name", "geometry"]],
        how="left",
        predicate="within"
    )

    joined = joined.rename(
        columns={
            "Name": "gis_ward"
        }
    )

    joined["gis_ward"] = (
        joined["gis_ward"]
        .astype("string")
        .str.replace(
            r"\s+",
            " ",
            regex=True
        )
        .str.strip()
        .apply(normalize_ward)
    )

    if "index_right" in joined.columns:
        joined = joined.drop(
            columns=["index_right"]
        )

    joined["ward_match"] = (
        joined["source_ward"]
        == joined["gis_ward"]
    )

    joined.loc[
        joined["source_ward"].isna()
        | joined["gis_ward"].isna(),
        "ward_match"
    ] = False

    joined["urban_ward_code"] = (
        joined["gis_ward"]
    )

    mismatches = joined[
        joined["source_ward"].notna()
        &
        joined["gis_ward"].notna()
        &
        (~joined["ward_match"])
    ].copy()

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

    joined.to_file(
        OUT_GEOJSON,
        driver="GeoJSON"
    )

    matched = (
        joined["ward_match"]
        &
        joined["gis_ward"].notna()
    ).sum()

    mismatch_count = len(mismatches)

    outside = (
        joined["gis_ward"].isna()
    ).sum()

    print("\nPolice GIS Validation")
    print("--------------------------------")

    print(
        f"Coordinate-valid records: {len(joined)}"
    )

    print(
        f"GIS ward matched:         {matched}"
    )

    print(
        f"Ward mismatches:          {mismatch_count}"
    )

    print(
        f"Outside BMC wards:        {outside}"
    )

    if len(joined) > 0:
        print(
            f"Match rate:               "
            f"{matched / len(joined) * 100:.2f}%"
        )

    print("\nSubtype among coordinate-valid records:")

    print(
        joined["subtype"]
        .value_counts(dropna=False)
        .to_string()
    )

    print("\nValidated CSV:")
    print(OUT_CSV)

    print("\nMismatch report:")
    print(MISMATCH_CSV)

    print("\nValidated GeoJSON:")
    print(OUT_GEOJSON)


if __name__ == "__main__":
    main()

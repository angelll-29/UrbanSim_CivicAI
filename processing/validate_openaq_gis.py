from pathlib import Path

import pandas as pd
import geopandas as gpd


STATIONS = Path(
    "data/processed/mumbai_air_quality_stations.csv"
)

WARDS = Path(
    "data/spatial/mumbai_wards.geojson"
)

OUT_CSV = Path(
    "data/processed/mumbai_air_quality_stations_validated.csv"
)

OUT_GEOJSON = Path(
    "data/spatial/mumbai_air_quality_stations_validated.geojson"
)

OUT_OUTSIDE = Path(
    "data/processed/mumbai_air_quality_stations_outside_bmc.csv"
)


def main():

    stations = pd.read_csv(STATIONS)

    wards = gpd.read_file(WARDS)

    print("Air-quality stations:", len(stations))
    print("Ward polygons:       ", len(wards))
    print("Ward CRS:             ", wards.crs)

    # Convert stations to GeoDataFrame.
    gdf = gpd.GeoDataFrame(
        stations.copy(),
        geometry=gpd.points_from_xy(
            stations["longitude"],
            stations["latitude"]
        ),
        crs="EPSG:4326"
    )

    # Ensure same CRS.
    wards = wards.to_crs(gdf.crs)

    # Keep original ward name from polygon.
    ward_column = "Name"

    if ward_column not in wards.columns:
        raise ValueError(
            f"Expected ward field '{ward_column}' "
            f"not found. Available fields: "
            f"{wards.columns.tolist()}"
        )

    wards_join = wards[
        [ward_column, "geometry"]
    ].rename(
        columns={
            ward_column: "gis_ward"
        }
    )

    # Spatial join.
    joined = gpd.sjoin(
        gdf,
        wards_join,
        how="left",
        predicate="within"
    )

    # Remove spatial-index helper.
    if "index_right" in joined.columns:
        joined = joined.drop(
            columns=["index_right"]
        )

    joined["urban_ward_code"] = (
        joined["gis_ward"]
        .astype("string")
        .str.strip()
    )

    # Determine BMC membership.
    matched = joined[
        joined["urban_ward_code"].notna()
    ].copy()

    outside = joined[
        joined["urban_ward_code"].isna()
    ].copy()

    # Save validated CSV without geometry.
    validated_csv = pd.DataFrame(
        matched.drop(
            columns=["geometry"]
        )
    )

    OUT_CSV.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    validated_csv.to_csv(
        OUT_CSV,
        index=False
    )

    # Save validated GeoJSON.
    matched.to_file(
        OUT_GEOJSON,
        driver="GeoJSON"
    )

    # Save outside-BMC stations separately.
    outside_csv = pd.DataFrame(
        outside.drop(
            columns=["geometry"]
        )
    )

    outside_csv.to_csv(
        OUT_OUTSIDE,
        index=False
    )

    print("\nAir Quality GIS Validation")
    print("--------------------------")

    print(
        f"Total stations:        {len(joined)}"
    )

    print(
        f"BMC ward matched:      {len(matched)}"
    )

    print(
        f"Outside BMC wards:     {len(outside)}"
    )

    match_rate = (
        len(matched)
        / len(joined)
        * 100
        if len(joined)
        else 0
    )

    print(
        f"Match rate:             "
        f"{match_rate:.2f}%"
    )

    print("\nMatched stations by provider:")

    print(
        matched["provider"]
        .value_counts(dropna=False)
        .to_string()
    )

    print("\nStations by BMC ward:")

    print(
        matched["urban_ward_code"]
        .value_counts()
        .sort_index()
        .to_string()
    )

    print(
        f"\nValidated CSV:\n{OUT_CSV}"
    )

    print(
        f"\nValidated GeoJSON:\n{OUT_GEOJSON}"
    )

    print(
        f"\nOutside-BMC CSV:\n{OUT_OUTSIDE}"
    )


if __name__ == "__main__":
    main()

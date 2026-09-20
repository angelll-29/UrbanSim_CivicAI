from pathlib import Path
import xml.etree.ElementTree as ET
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = PROJECT_ROOT / "data" / "external" / "mumbai_green_spaces.kml"

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
SPATIAL_DIR = PROJECT_ROOT / "data" / "spatial"

CSV_OUTPUT = PROCESSED_DIR / "mumbai_green_spaces.csv"
GEOJSON_OUTPUT = SPATIAL_DIR / "mumbai_green_spaces.geojson"


# ---------------------------------------------------------
# KML namespace
# ---------------------------------------------------------
NS = {
    "k": "http://www.opengis.net/kml/2.2"
}


def clean_text(value):
    """Clean whitespace from text fields."""
    if value is None:
        return None

    value = str(value)
    value = " ".join(value.split())

    return value if value else None


def parse_coordinates(value):
    """Extract longitude and latitude from KML coordinates."""
    if not value:
        return None, None

    value = value.strip()

    parts = value.split(",")

    if len(parts) < 2:
        return None, None

    try:
        longitude = float(parts[0])
        latitude = float(parts[1])

        return longitude, latitude

    except ValueError:
        return None, None


def extract_extended_data(placemark):
    """Extract KML ExtendedData SimpleData fields."""

    data = {}

    for simple_data in placemark.findall(
        ".//k:SimpleData",
        NS
    ):
        field_name = simple_data.attrib.get("name")

        if field_name:
            data[field_name] = clean_text(simple_data.text)

    return data


def main():

    print("=" * 60)
    print("UrbanSim Civic AI - Green Space Processor")
    print("=" * 60)

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input KML not found:\n{INPUT_FILE}"
        )

    print(f"\nReading:\n{INPUT_FILE}")

    tree = ET.parse(INPUT_FILE)
    root = tree.getroot()

    placemarks = root.findall(
        ".//k:Placemark",
        NS
    )

    print(f"Placemark records found: {len(placemarks)}")

    records = []

    for index, placemark in enumerate(placemarks, start=1):

        name_element = placemark.find(
            "k:name",
            NS
        )

        name = clean_text(
            name_element.text
            if name_element is not None
            else None
        )

        extended = extract_extended_data(
            placemark
        )

        coordinate_element = placemark.find(
            ".//k:Point/k:coordinates",
            NS
        )

        coordinates = (
            coordinate_element.text
            if coordinate_element is not None
            else None
        )

        longitude, latitude = parse_coordinates(
            coordinates
        )

        records.append({
            "green_space_id": extended.get(
                "OBJECTID"
            ) or index,

            "green_space_name": (
                name
                or extended.get(
                    "Miyawaki_Garden_Name"
                )
            ),

            "address": extended.get(
                "Address"
            ),

            "bmc_department": extended.get(
                "BMC_Dept_"
            ),

            "ward_code_source": extended.get(
                "Ward_s"
            ),

            "twitter_handle": extended.get(
                "Twitter_Handle"
            ),

            "website": extended.get(
                "Website"
            ),

            "latitude": latitude,

            "longitude": longitude,

            "source_file": INPUT_FILE.name,

            "source": (
                "BMC / OpenCity "
                "Mumbai Public Gardens, "
                "Parks and Zoos dataset"
            ),
        })

        if index % 100 == 0:
            print(
                f"Processed {index}/{len(placemarks)}"
            )

    df = pd.DataFrame(records)

    # -----------------------------------------------------
    # Basic validation
    # -----------------------------------------------------

    print("\nValidating records...")

    df["coordinate_valid"] = (
        df["latitude"].notna()
        & df["longitude"].notna()
        & df["latitude"].between(-90, 90)
        & df["longitude"].between(-180, 180)
    )

    before = len(df)

    df = df.drop_duplicates(
        subset=["green_space_id"],
        keep="first"
    )

    duplicates_removed = before - len(df)

    # -----------------------------------------------------
    # Create GeoDataFrame
    # -----------------------------------------------------

    valid_df = df[
        df["coordinate_valid"]
    ].copy()

    geometry = [
        Point(lon, lat)
        for lon, lat in zip(
            valid_df["longitude"],
            valid_df["latitude"]
        )
    ]

    gdf = gpd.GeoDataFrame(
        valid_df,
        geometry=geometry,
        crs="EPSG:4326"
    )

    # -----------------------------------------------------
    # Create directories
    # -----------------------------------------------------

    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    SPATIAL_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # -----------------------------------------------------
    # Save CSV
    # -----------------------------------------------------

    df.to_csv(
        CSV_OUTPUT,
        index=False
    )

    # -----------------------------------------------------
    # Save GeoJSON
    # -----------------------------------------------------

    gdf.to_file(
        GEOJSON_OUTPUT,
        driver="GeoJSON"
    )

    # -----------------------------------------------------
    # Summary
    # -----------------------------------------------------

    print("\n" + "=" * 60)
    print("GREEN SPACE PROCESSING COMPLETE")
    print("=" * 60)

    print(f"Total records:       {len(df)}")
    print(f"Valid coordinates:   {df['coordinate_valid'].sum()}")
    print(
        f"Invalid coordinates: "
        f"{(~df['coordinate_valid']).sum()}"
    )
    print(
        f"Duplicate IDs removed: "
        f"{duplicates_removed}"
    )

    print("\nWard distribution:")
    print(
        df["ward_code_source"]
        .value_counts(dropna=False)
        .sort_index()
    )

    print("\nOutputs:")

    print(
        f"CSV:      {CSV_OUTPUT}"
    )

    print(
        f"GeoJSON:  {GEOJSON_OUTPUT}"
    )


if __name__ == "__main__":
    main()
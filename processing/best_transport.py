from pathlib import Path
import xml.etree.ElementTree as ET

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "external"
    / "mumbai_best_stops_depots.kml"
)

PROCESSED_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
)

SPATIAL_DIR = (
    PROJECT_ROOT
    / "data"
    / "spatial"
)

CSV_OUTPUT = (
    PROCESSED_DIR
    / "mumbai_best_transport.csv"
)

GEOJSON_OUTPUT = (
    SPATIAL_DIR
    / "mumbai_best_transport.geojson"
)


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

    value = " ".join(str(value).split())

    return value if value else None


def parse_coordinates(value):
    """Extract longitude and latitude from KML coordinates."""

    if not value:
        return None, None

    parts = value.strip().split(",")

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
            data[field_name] = clean_text(
                simple_data.text
            )

    return data


def main():

    print("=" * 60)
    print("UrbanSim Civic AI - BEST Transport Processor")
    print("=" * 60)

    # -----------------------------------------------------
    # Check input
    # -----------------------------------------------------

    if not INPUT_FILE.exists():

        raise FileNotFoundError(
            f"BEST KML not found:\n{INPUT_FILE}"
        )

    print("\nReading:")
    print(INPUT_FILE)

    # -----------------------------------------------------
    # Parse KML
    # -----------------------------------------------------

    tree = ET.parse(INPUT_FILE)

    root = tree.getroot()

    placemarks = root.findall(
        ".//k:Placemark",
        NS
    )

    print(
        f"\nPlacemark records found: "
        f"{len(placemarks)}"
    )

    records = []

    # -----------------------------------------------------
    # Process each Placemark
    # -----------------------------------------------------

    for index, placemark in enumerate(
        placemarks,
        start=1
    ):

        # ---------------------------------------------
        # Name
        # ---------------------------------------------

        name_element = placemark.find(
            "k:name",
            NS
        )

        name = clean_text(
            name_element.text
            if name_element is not None
            else None
        )

        # ---------------------------------------------
        # Style
        # ---------------------------------------------

        style_element = placemark.find(
            "k:styleUrl",
            NS
        )

        style = clean_text(
            style_element.text
            if style_element is not None
            else None
        )

        # ---------------------------------------------
        # ExtendedData
        # ---------------------------------------------

        extended = extract_extended_data(
            placemark
        )

        # ---------------------------------------------
        # Coordinates
        # ---------------------------------------------

        coordinate_element = placemark.find(
            ".//k:Point/k:coordinates",
            NS
        )

        coordinates = (
            coordinate_element.text
            if coordinate_element is not None
            else None
        )

        longitude, latitude = (
            parse_coordinates(coordinates)
        )

        # ---------------------------------------------
        # Transport type
        # ---------------------------------------------

        if style == "#mumbai_bus_depots_style1":

            transport_type = "BUS_DEPOT"

        elif style == "#mumbai_best_stops_style":

            transport_type = "BUS_STOP"

        else:

            transport_type = "OTHER"

        # ---------------------------------------------
        # Globally unique UrbanSim ID
        # ---------------------------------------------

        if transport_type == "BUS_DEPOT":

            transport_id = f"DEPOT_{index}"

        elif transport_type == "BUS_STOP":

            transport_id = f"STOP_{index}"

        else:

            transport_id = f"OTHER_{index}"

        # ---------------------------------------------
        # Record
        # ---------------------------------------------

        records.append({

            "transport_id": transport_id,

            "object_id": extended.get(
                "OBJECTID"
            ),

            "transport_name": name,

            "transport_type": transport_type,

            "best_bus_stop_name": (
                extended.get("BEST_BUS_S")
            ),

            "bus_depot_name": (
                extended.get("BUS_DEPOT_")
            ),

            "address": (
                extended.get("ADDRESS")
            ),

            "ward_code_source": (
                extended.get("WARD")
            ),

            "best_app": (
                extended.get("BEST_APP_1")
            ),

            "best_help": (
                extended.get("BEST_HELP_")
            ),

            "twitter_handle": (
                extended.get("TWITTER_HA")
            ),

            "website": (
                extended.get("WEBSITE")
            ),

            "latitude": latitude,

            "longitude": longitude,

            "style_url": style,

            "source_file": INPUT_FILE.name,

            "source": (
                "BMC / OpenCity "
                "Mumbai BEST Stops and Depots dataset"
            ),
        })

        if index % 500 == 0:

            print(
                f"Processed "
                f"{index}/{len(placemarks)}"
            )

    # -----------------------------------------------------
    # Create DataFrame
    # -----------------------------------------------------

    df = pd.DataFrame(records)

    # -----------------------------------------------------
    # Coordinate validation
    # -----------------------------------------------------

    df["coordinate_valid"] = (

        df["latitude"].notna()

        &

        df["longitude"].notna()

        &

        df["latitude"].between(-90, 90)

        &

        df["longitude"].between(-180, 180)

    )

    # -----------------------------------------------------
    # DO NOT deduplicate by OBJECTID
    # -----------------------------------------------------
    #
    # The source uses overlapping OBJECTIDs:
    # 6243 stops + 24 depots.
    #
    # transport_id is already unique.
    # -----------------------------------------------------

    duplicates_removed = 0

    # -----------------------------------------------------
    # Create GeoDataFrame
    # -----------------------------------------------------

    valid_df = df[
        df["coordinate_valid"]
    ].copy()

    geometry = [

        Point(
            lon,
            lat
        )

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
    print("BEST TRANSPORT PROCESSING COMPLETE")
    print("=" * 60)

    print(
        f"Total records: "
        f"{len(df)}"
    )

    print(
        f"Valid coordinates: "
        f"{df['coordinate_valid'].sum()}"
    )

    print(
        f"Invalid coordinates: "
        f"{(~df['coordinate_valid']).sum()}"
    )

    print(
        f"Duplicate IDs removed: "
        f"{duplicates_removed}"
    )

    print("\nTransport types:")

    print(
        df["transport_type"]
        .value_counts(
            dropna=False
        )
    )

    print("\nOutputs:")

    print(
        f"CSV:      {CSV_OUTPUT}"
    )

    print(
        f"GeoJSON:  {GEOJSON_OUTPUT}"
    )

    print("\n" + "=" * 60)


if __name__ == "__main__":

    main()
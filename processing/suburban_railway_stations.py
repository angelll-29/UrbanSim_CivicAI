import xml.etree.ElementTree as ET
import csv
import json
from pathlib import Path


INPUT = Path("data/external/mumbai_suburban_railway_stations.kml")
CSV_OUTPUT = Path("data/processed/mumbai_suburban_railway_stations.csv")
GEOJSON_OUTPUT = Path("data/spatial/mumbai_suburban_railway_stations.geojson")

NS = {"k": "http://www.opengis.net/kml/2.2"}


def get_simple_data(placemark):
    data = {}

    for item in placemark.findall(
        ".//k:ExtendedData/k:SchemaData/k:SimpleData", NS
    ):
        name = item.attrib.get("name")
        data[name] = item.text.strip() if item.text else None

    return data


def parse_coordinates(placemark):
    point = placemark.find(".//k:Point/k:coordinates", NS)

    if point is None or not point.text:
        return None, None

    values = point.text.strip().split(",")

    try:
        longitude = float(values[0])
        latitude = float(values[1])
        return latitude, longitude
    except (ValueError, IndexError):
        return None, None


def main():

    if not INPUT.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT}")

    CSV_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    GEOJSON_OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    tree = ET.parse(INPUT)
    root = tree.getroot()

    placemarks = root.findall(".//k:Placemark", NS)

    print(f"Found {len(placemarks)} placemarks")

    records = []
    features = []

    for index, placemark in enumerate(placemarks, start=1):

        name_element = placemark.find("k:name", NS)
        station_name = (
            name_element.text.strip()
            if name_element is not None and name_element.text
            else None
        )

        data = get_simple_data(placemark)

        latitude, longitude = parse_coordinates(placemark)

        coordinate_valid = (
            latitude is not None
            and longitude is not None
            and -90 <= latitude <= 90
            and -180 <= longitude <= 180
        )

        station_id = f"SUBURBAN_{index:03d}"

        record = {
            "station_id": station_id,
            "station_name": station_name,
            "station_type": data.get("N_TYPE"),
            "region": data.get("N_REGION"),
            "label": data.get("For_Labell"),
            "fid": data.get("FID"),
            "object_id": data.get("OBJECTID_1"),
            "latitude": latitude,
            "longitude": longitude,
            "source": "BMC / OpenCity Mumbai Suburban Network 2025",
            "source_file": INPUT.name,
            "coordinate_valid": coordinate_valid,
        }

        records.append(record)

        if coordinate_valid:

            properties = {
                key: value
                for key, value in record.items()
                if key not in ["latitude", "longitude"]
            }

            feature = {
                "type": "Feature",
                "properties": properties,
                "geometry": {
                    "type": "Point",
                    "coordinates": [longitude, latitude],
                },
            }

            features.append(feature)

    # ---------------------------------------------------------
    # CSV
    # ---------------------------------------------------------

    fieldnames = [
        "station_id",
        "station_name",
        "station_type",
        "region",
        "label",
        "fid",
        "object_id",
        "latitude",
        "longitude",
        "source",
        "source_file",
        "coordinate_valid",
    ]

    with open(CSV_OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    # ---------------------------------------------------------
    # GeoJSON
    # ---------------------------------------------------------

    geojson = {
        "type": "FeatureCollection",
        "features": features,
    }

    with open(GEOJSON_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)

    # ---------------------------------------------------------
    # Summary
    # ---------------------------------------------------------

    valid_count = sum(r["coordinate_valid"] for r in records)

    regions = {}
    types = {}

    for r in records:

        region = r["region"] or "UNKNOWN"
        station_type = r["station_type"] or "UNKNOWN"

        regions[region] = regions.get(region, 0) + 1
        types[station_type] = types.get(station_type, 0) + 1

    print("\n========================================")
    print("SUBURBAN RAILWAY STATION PROCESSING")
    print("========================================")

    print(f"Input placemarks : {len(placemarks)}")
    print(f"Output records   : {len(records)}")
    print(f"Valid coordinates: {valid_count}")
    print(f"Invalid coords   : {len(records) - valid_count}")

    print("\nRegions:")
    for key, value in sorted(regions.items()):
        print(f"  {key}: {value}")

    print("\nStation Types:")
    for key, value in sorted(types.items()):
        print(f"  {key}: {value}")

    print("\nOutputs:")
    print(f"  CSV     : {CSV_OUTPUT}")
    print(f"  GeoJSON : {GEOJSON_OUTPUT}")


if __name__ == "__main__":
    main()
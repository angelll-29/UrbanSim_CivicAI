from pathlib import Path
import xml.etree.ElementTree as ET
import pandas as pd
import json

INPUT = Path("data/external/mumbai_fire_stations.kml")

CSV_OUT = Path(
    "data/processed/mumbai_fire_stations.csv"
)

GEOJSON_OUT = Path(
    "data/spatial/mumbai_fire_stations.geojson"
)

NS = {
    "kml": "http://www.opengis.net/kml/2.2"
}


def clean(value):
    if value is None:
        return None

    value = str(value).strip()

    return value if value else None


def parse_kml():

    tree = ET.parse(INPUT)
    root = tree.getroot()

    placemarks = root.findall(
        ".//kml:Placemark",
        NS
    )

    records = []

    for idx, placemark in enumerate(
        placemarks,
        start=1
    ):

        attributes = {}

        for simple_data in placemark.findall(
            ".//kml:SimpleData",
            NS
        ):

            name = simple_data.get("name")

            attributes[name] = clean(
                simple_data.text
            )

        station_name = clean(
            placemark.findtext(
                "kml:name",
                default="",
                namespaces=NS
            )
        )

        coordinates = placemark.findtext(
            ".//kml:Point/kml:coordinates",
            default="",
            namespaces=NS
        )

        latitude = None
        longitude = None

        if coordinates:

            try:

                parts = coordinates.strip().split(",")

                longitude = float(parts[0])
                latitude = float(parts[1])

            except (ValueError, IndexError):

                pass

        record = {

            "fire_station_id":
                attributes.get("FEATUREID")
                or f"FIRE_{idx:03d}",

            "object_id":
                attributes.get("OBJECTID"),

            "feature_id":
                attributes.get("FEATUREID"),

            "station_name":
                station_name,

            "type_code":
                attributes.get("TYPE"),

            "location":
                attributes.get("LOCATION"),

            "brd_line_no":
                attributes.get("BRD_LINE_NO"),

            "source_ward":
                attributes.get("WARD"),

            "created_user":
                attributes.get("CREATED_USER"),

            "created_date":
                attributes.get("CREATED_DATE"),

            "last_edited_user":
                attributes.get("LAST_EDITED_USER"),

            "last_edited_date":
                attributes.get("LAST_EDITED_DATE"),

            "edu_update_user":
                attributes.get("EDUPDATEUSER"),

            "edu_update_time":
                attributes.get("EDUPDATETIME"),

            "latitude":
                latitude,

            "longitude":
                longitude,

            "source":
                "BMC/MCGM via OpenCity",

            "source_file":
                INPUT.name,

            "verification_status":
                "SOURCE_KML"
        }

        records.append(record)

    return records


def main():

    records = parse_kml()

    df = pd.DataFrame(records)

    print(
        f"Raw fire-station records: {len(df)}"
    )

    # Coordinate validation
    df["coordinate_valid"] = (
        df["latitude"].between(-90, 90)
        &
        df["longitude"].between(-180, 180)
    )

    # Duplicate check
    before = len(df)

    df = df.drop_duplicates(
        subset=["fire_station_id"],
        keep="first"
    )

    duplicates_removed = (
        before - len(df)
    )

    # Save CSV
    CSV_OUT.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(
        CSV_OUT,
        index=False
    )

    # GeoJSON
    features = []

    for _, row in df.iterrows():

        if not row["coordinate_valid"]:
            continue

        properties = row.drop(
            ["latitude", "longitude"]
        ).to_dict()

        properties = {
            key:
                None if pd.isna(value)
                else value

            for key, value
            in properties.items()
        }

        feature = {

            "type": "Feature",

            "properties": properties,

            "geometry": {

                "type": "Point",

                "coordinates": [
                    float(row["longitude"]),
                    float(row["latitude"])
                ]
            }
        }

        features.append(feature)

    geojson = {

        "type": "FeatureCollection",

        "features": features
    }

    GEOJSON_OUT.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        GEOJSON_OUT,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            geojson,
            f,
            ensure_ascii=False,
            indent=2
        )

    print("\nFire Stations Processing Complete")
    print("-----------------------------------")

    print(
        f"Records:              {len(df)}"
    )

    print(
        f"Duplicates removed:   {duplicates_removed}"
    )

    print(
        f"Valid coordinates:    "
        f"{df['coordinate_valid'].sum()}"
    )

    print(
        f"Invalid coordinates:  "
        f"{(~df['coordinate_valid']).sum()}"
    )

    print(
        f"\nCSV:      {CSV_OUT}"
    )

    print(
        f"GeoJSON:  {GEOJSON_OUT}"
    )


if __name__ == "__main__":
    main()
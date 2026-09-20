from pathlib import Path
import xml.etree.ElementTree as ET
import pandas as pd
import json

INPUT = Path("data/external/mumbai_police_stations.kml")

CSV_OUT = Path(
    "data/processed/mumbai_police_stations.csv"
)

GEOJSON_OUT = Path(
    "data/spatial/mumbai_police_stations.geojson"
)

NS = {"kml": "http://www.opengis.net/kml/2.2"}


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
            attributes[name] = clean(simple_data.text)

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

        records.append({

            # Position-based ID guarantees every source
            # Placemark remains uniquely represented.
            "police_location_id":
                f"POLICE_{idx:03d}",

            "source_feature_id":
                attributes.get("FEATUREID"),

            "object_id":
                attributes.get("OBJECTID"),

            "feature_id":
                attributes.get("FEATUREID"),

            "name":
                station_name,

            "subtype":
                attributes.get("SUBTYPE"),

            "type_code":
                attributes.get("TYPE"),

            "location":
                attributes.get("LOCATION"),

            "ward_code_source":
                attributes.get("WARD"),

            "brd_line_no":
                attributes.get("BRD_LINE_NO"),

            "remarks":
                attributes.get("REMARKS"),

            "working_hours":
                attributes.get("WORKING_HRS"),

            "year_construct":
                attributes.get("YEAR_CONSTRUCT"),

            "no_of_floors":
                attributes.get("NO_FLOOR"),

            "no_of_rooms":
                attributes.get("NO_ROOMS"),

            "employee_quantity":
                attributes.get("EMPLOYEE_QTY"),

            "employee_male":
                attributes.get("EMPLOYEE_MALE"),

            "employee_female":
                attributes.get("EMPLOYEE_FEMALE"),

            "employee_disabled":
                attributes.get("EMPLOYEE_DIF_ABLE"),

            "cctv_service":
                attributes.get("CCTV_SERVE"),

            "fire_audit":
                attributes.get("FIRE_AUDIT"),

            "fire_extinguishing_system":
                attributes.get("FIRE_EXTING_SYS"),

            "structural_audit":
                attributes.get("STRUCTURAL_AUDIT"),

            "ramp_disabled":
                attributes.get("RAMP_DISABLED"),

            "bathroom_facility":
                attributes.get("BATHROOM_FAC"),

            "water_tank_capacity":
                attributes.get("WATER_TANK_CAPA"),

            "created_date":
                attributes.get("CREATED_DATE"),

            "created_user":
                attributes.get("CREATED_USER"),

            "last_edited_date":
                attributes.get("LAST_EDITED_DATE"),

            "last_edited_user":
                attributes.get("LAST_EDITED_USER"),

            "edu_update_time":
                attributes.get("EDUPDATETIME"),

            "edu_update_user":
                attributes.get("EDUPDATEUSER"),

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
        })

    return records


def main():

    records = parse_kml()

    df = pd.DataFrame(records)

    print(
        f"Raw police-location records: {len(df)}"
    )

    # Do NOT deduplicate by FEATUREID.
    # The source contains at least one FEATUREID
    # associated with two different facilities.

    df["coordinate_valid"] = (
        df["latitude"].between(-90, 90)
        &
        df["longitude"].between(-180, 180)
    )

    CSV_OUT.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(
        CSV_OUT,
        index=False
    )

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

        features.append({

            "type": "Feature",

            "properties": properties,

            "geometry": {

                "type": "Point",

                "coordinates": [
                    float(row["longitude"]),
                    float(row["latitude"])
                ]
            }
        })

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

    print("\nPolice Stations Processing Complete")
    print("-----------------------------------")

    print(
        f"Records retained:     {len(df)}"
    )

    print(
        f"Valid coordinates:    "
        f"{df['coordinate_valid'].sum()}"
    )

    print(
        f"Invalid coordinates:  "
        f"{(~df['coordinate_valid']).sum()}"
    )

    print("\nSubtype distribution:")
    print(
        df["subtype"]
        .value_counts(dropna=False)
        .to_string()
    )

    print("\nDuplicate source FEATUREIDs retained:")
    duplicates = (
        df["source_feature_id"]
        .value_counts()
    )

    print(
        duplicates[
            duplicates > 1
        ].to_string()
    )

    print(f"\nCSV:      {CSV_OUT}")
    print(f"GeoJSON:  {GEOJSON_OUT}")


if __name__ == "__main__":
    main()

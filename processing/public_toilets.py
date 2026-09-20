from pathlib import Path
import xml.etree.ElementTree as ET
import pandas as pd
import json

INPUT = Path("data/external/mumbai_public_toilets.kml")
CSV_OUT = Path("data/processed/mumbai_public_toilets.csv")
GEOJSON_OUT = Path("data/spatial/mumbai_public_toilets.geojson")

NS = {"kml": "http://www.opengis.net/kml/2.2"}


def clean(value):
    if value is None:
        return None
    value = str(value).strip()
    return value if value else None


def parse_kml():
    tree = ET.parse(INPUT)
    root = tree.getroot()

    placemarks = root.findall(".//kml:Placemark", NS)

    records = []

    for idx, placemark in enumerate(placemarks, start=1):

        attributes = {}

        for simple_data in placemark.findall(
            ".//kml:SimpleData", NS
        ):
            name = simple_data.get("name")
            attributes[name] = clean(simple_data.text)

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
            "toilet_id": attributes.get("GlobalID") or f"TOILET_{idx:04d}",
            "object_id": attributes.get("OBJECTID"),
            "object_id_1": attributes.get("OBJECTID_1"),
            "address": attributes.get("Address"),
            "bmc_department": attributes.get("BMC_Dept_"),
            "female_facilities": attributes.get("Count_of_F"),
            "male_facilities": attributes.get("Count_of_M"),
            "ward_code_source": attributes.get("Ward"),
            "twitter": attributes.get("Twitter_Ha"),
            "latitude": latitude,
            "longitude": longitude,
            "source": "BMC/MCGM via OpenCity",
            "source_file": INPUT.name,
            "verification_status": "SOURCE_KML"
        }

        records.append(record)

    return records


def main():
    records = parse_kml()

    df = pd.DataFrame(records)

    print(f"Raw records: {len(df)}")

    # Convert numeric fields
    df["female_facilities"] = pd.to_numeric(
        df["female_facilities"], errors="coerce"
    )

    df["male_facilities"] = pd.to_numeric(
        df["male_facilities"], errors="coerce"
    )

    # Total facility count
    df["total_facilities"] = (
        df["female_facilities"].fillna(0)
        + df["male_facilities"].fillna(0)
    )

    # Coordinate validation
    df["coordinate_valid"] = (
        df["latitude"].between(-90, 90)
        & df["longitude"].between(-180, 180)
    )

    # Remove exact duplicate GlobalIDs
    before = len(df)

    if df["toilet_id"].notna().any():
        df = df.drop_duplicates(
            subset=["toilet_id"],
            keep="first"
        )

    duplicates_removed = before - len(df)

    # Save CSV
    CSV_OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(CSV_OUT, index=False)

    # Create GeoJSON
    features = []

    for _, row in df.iterrows():

        if not row["coordinate_valid"]:
            continue

        properties = row.drop(
            ["latitude", "longitude"]
        ).to_dict()

        # Convert NaN to None
        properties = {
            k: (None if pd.isna(v) else v)
            for k, v in properties.items()
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

    GEOJSON_OUT.parent.mkdir(parents=True, exist_ok=True)

    with open(GEOJSON_OUT, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)

    print("\nPublic Toilets Processing Complete")
    print("-----------------------------------")
    print(f"Records:              {len(df)}")
    print(f"Duplicates removed:   {duplicates_removed}")
    print(
        f"Valid coordinates:    "
        f"{df['coordinate_valid'].sum()}"
    )
    print(
        f"Invalid coordinates:  "
        f"{(~df['coordinate_valid']).sum()}"
    )
    print(
        f"Total facilities:     "
        f"{df['total_facilities'].sum():.0f}"
    )
    print(f"\nCSV:      {CSV_OUT}")
    print(f"GeoJSON:  {GEOJSON_OUT}")


if __name__ == "__main__":
    main()
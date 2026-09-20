import xml.etree.ElementTree as ET
from collections import Counter, defaultdict

p = "data/external/mumbai_police_stations.kml"

root = ET.parse(p).getroot()

ns = {
    "k": "http://www.opengis.net/kml/2.2"
}

placemarks = root.findall(
    ".//k:Placemark",
    ns
)

records = []

for x in placemarks:
    feature_id = x.findtext(
        './/k:SimpleData[@name="FEATUREID"]',
        "",
        ns
    )

    name = x.findtext(
        "k:name",
        "",
        ns
    )

    coordinates = x.findtext(
        ".//k:coordinates",
        "",
        ns
    )

    records.append(
        (feature_id, name, coordinates)
    )

counts = Counter(
    r[0] for r in records
)

print("Duplicate FEATUREIDs:")
print()

for feature_id, count in counts.items():

    if feature_id and count > 1:

        print(
            f"{feature_id} -> {count} records"
        )

        for record in records:

            if record[0] == feature_id:

                print(
                    f"  Name: {record[1]}"
                )

                print(
                    f"  Coordinates: {record[2]}"
                )

        print()

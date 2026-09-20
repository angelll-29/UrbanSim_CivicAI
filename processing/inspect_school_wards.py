import geopandas as gpd
import os
import warnings

warnings.filterwarnings("ignore")

INPUT_DIR = "data/external"

FILES = [
    ("Mumbai Aided Schools Map.kml", "VillageNam"),
    ("Mumbai Unaided Schools Map.kml", "Ward"),
    ("Mumbai Municipal Primary and Secondary Schools Map.kml", "Ward")
]

print("=" * 70)
print("URBANSIM - SCHOOL WARD FIELD INSPECTION")
print("=" * 70)

for filename, ward_column in FILES:

    path = os.path.join(INPUT_DIR, filename)

    print("\n" + "=" * 70)
    print(filename)
    print("Ward field:", ward_column)
    print("=" * 70)

    gdf = gpd.read_file(path, driver="KML")

    print("Records:", len(gdf))

    if ward_column not in gdf.columns:
        print("ERROR: Ward field not found")
        continue

    values = (
        gdf[ward_column]
        .fillna("<NULL>")
        .astype(str)
        .str.strip()
        .value_counts()
    )

    print("\nUnique values:", len(values))

    print("\nWard values:")
    print(values.to_string())

print("\n" + "=" * 70)
print("WARD FIELD INSPECTION COMPLETE")
print("=" * 70)

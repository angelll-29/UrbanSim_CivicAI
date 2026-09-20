import geopandas as gpd
import os
import warnings

warnings.filterwarnings("ignore")

INPUT_DIR = "data/external"

FILES = [
    "Mumbai Aided Schools Map.kml",
    "Mumbai Unaided Schools Map.kml",
    "Mumbai Municipal Primary and Secondary Schools Map.kml"
]

print("=" * 70)
print("URBANSIM - MUMBAI SCHOOL DATA INSPECTION")
print("=" * 70)

for filename in FILES:

    path = os.path.join(INPUT_DIR, filename)

    print("\n" + "=" * 70)
    print("FILE:", filename)
    print("=" * 70)

    if not os.path.exists(path):
        print("ERROR: File not found")
        continue

    try:

        gdf = gpd.read_file(
            path,
            driver="KML"
        )

        print("Records:", len(gdf))
        print("CRS:", gdf.crs)
        print("Geometry types:")
        print(gdf.geometry.geom_type.value_counts())

        print("\nColumns:")
        for column in gdf.columns:
            print(" -", column)

        print("\nSample records:")

        display_columns = [
            column
            for column in gdf.columns
            if column != "geometry"
        ]

        print(
            gdf[display_columns]
            .head(5)
            .to_string(index=False)
        )

    except Exception as e:

        print("ERROR:", str(e))


print("\n" + "=" * 70)
print("SCHOOL DATA INSPECTION COMPLETE")
print("=" * 70)

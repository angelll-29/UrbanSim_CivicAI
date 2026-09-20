import geopandas as gpd
import os
import warnings

warnings.filterwarnings("ignore")

files = [
    "data/external/Mumbai City Dispensaries Map.kml",
    "data/external/Mumbai City Public Hospitals Map.kml",
    "data/external/Mumbai City Public Maternity Hospitals Map.kml",
    "data/external/Mumbai City Public Veterinary Hospitals Map.kml",
    "data/external/Mumbai City UPHCs Map.kml"
]

print("=" * 80)
print("MUMBAI HEALTHCARE DATASET INSPECTION")
print("=" * 80)

for file in files:

    print("\nFILE:", os.path.basename(file))

    gdf = gpd.read_file(file, driver="KML")

    print("Records:", len(gdf))
    print("CRS:", gdf.crs)
    print("Columns:")

    for column in gdf.columns:
        print("  -", column)

    print("\nFirst 5 facility names:")

    if "Name" in gdf.columns:
        print(gdf["Name"].head(5).to_string(index=False))

    print("-" * 80)

print("\nINSPECTION COMPLETE")

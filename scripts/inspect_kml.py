import geopandas as gpd
import os
import glob

files = glob.glob("data/external/*.kml")

print("KML DATASETS:")
print("=" * 70)

for f in files:
    print("\nFILE:", os.path.basename(f))

    gdf = gpd.read_file(f, driver="KML")

    print("Records:", len(gdf))
    print("Columns:", list(gdf.columns))
    print("CRS:", gdf.crs)

    if "Name" in gdf.columns:
        print("\nFirst 5 names:")
        print(gdf["Name"].head(5).to_string(index=False))

    print("-" * 70)

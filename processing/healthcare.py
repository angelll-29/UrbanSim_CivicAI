import geopandas as gpd
import pandas as pd
import os
import re
import warnings

warnings.filterwarnings("ignore")

INPUT_DIR = "data/external"
PROCESSED_DIR = "data/processed"
SPATIAL_DIR = "data/spatial"

os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(SPATIAL_DIR, exist_ok=True)

DATASETS = [
    {
        "file": "Mumbai City Dispensaries Map.kml",
        "service_type": "dispensary",
        "name_col": "Current_Na",
        "address_col": "Current_co",
        "ward_col": "Ward",
        "id_col": "OBJECTID"
    },
    {
        "file": "Mumbai City Public Hospitals Map.kml",
        "service_type": "hospital",
        "name_col": "NAME_OF_HO",
        "address_col": "ADDRESS",
        "ward_col": "WARD",
        "id_col": "OBJECTID_1"
    },
    {
        "file": "Mumbai City Public Maternity Hospitals Map.kml",
        "service_type": "maternity_hospital",
        "name_col": "Name_of_Mat_Home",
        "address_col": "Address",
        "ward_col": "Ward",
        "id_col": "OBJECTID"
    },
    {
        "file": "Mumbai City Public Veterinary Hospitals Map.kml",
        "service_type": "veterinary_hospital",
        "name_col": "NAME2",
        "address_col": "LOCATION",
        "ward_col": None,
        "id_col": "OBJECTID"
    },
    {
        "file": "Mumbai City UPHCs Map.kml",
        "service_type": "uphc",
        "name_col": "UPHC_Name",
        "address_col": "UPHC_Addre",
        "ward_col": "Ward",
        "id_col": "OBJECTID"
    }
]


def clean_text(value):
    if pd.isna(value):
        return None

    value = str(value)
    value = re.sub(r"\s+", " ", value)
    value = value.strip()

    return value if value else None


all_records = []

print("=" * 70)
print("URBANSIM - MUMBAI HEALTHCARE DATA PROCESSOR")
print("=" * 70)

for config in DATASETS:

    path = os.path.join(INPUT_DIR, config["file"])

    print("\nProcessing:", config["file"])

    gdf = gpd.read_file(path, driver="KML")

    print("Source records:", len(gdf))

    records = []

    for index, row in gdf.iterrows():

        name = clean_text(row.get(config["name_col"]))
        address = clean_text(row.get(config["address_col"]))

        ward = None

        if config["ward_col"]:
            ward = clean_text(row.get(config["ward_col"]))

        source_id = clean_text(row.get(config["id_col"]))

        point = row.geometry

        if point is None or point.is_empty:
            continue

        records.append({
            "facility_id": f"{config['service_type'].upper()}_{index + 1:04d}",
            "name": name,
            "service_type": config["service_type"],
            "address": address,
            "ward_code": ward,
            "longitude": point.x,
            "latitude": point.y,
            "source": "Mumbai OpenCity / BMC",
            "source_file": config["file"],
            "source_id": source_id,
            "verification_status": "source_verified",
            "geometry": point
        })

    all_records.extend(records)

    print("Processed:", len(records))


healthcare = gpd.GeoDataFrame(
    all_records,
    geometry="geometry",
    crs="EPSG:4326"
)

before = len(healthcare)

healthcare = healthcare.drop_duplicates(
    subset=["name", "service_type", "latitude", "longitude"]
).copy()

duplicates_removed = before - len(healthcare)

healthcare["facility_id"] = [
    f"HC_{i:05d}" for i in range(1, len(healthcare) + 1)
]

geojson_path = os.path.join(
    SPATIAL_DIR,
    "mumbai_healthcare_facilities.geojson"
)

healthcare.to_file(
    geojson_path,
    driver="GeoJSON"
)

csv_path = os.path.join(
    PROCESSED_DIR,
    "mumbai_healthcare_facilities.csv"
)

csv_df = healthcare.copy()
csv_df["geometry"] = csv_df.geometry.to_wkt()

csv_df.to_csv(
    csv_path,
    index=False
)

print("\n" + "=" * 70)
print("HEALTHCARE PROCESSING COMPLETE")
print("=" * 70)

print("Total facilities:", len(healthcare))
print("Duplicates removed:", duplicates_removed)

print("\nSERVICE TYPE DISTRIBUTION")
print("-" * 40)
print(healthcare["service_type"].value_counts())

print("\nWARD DISTRIBUTION")
print("-" * 40)
print(healthcare["ward_code"].value_counts(dropna=False))

print("\nOUTPUT FILES")
print("-" * 40)
print(csv_path)
print(geojson_path)

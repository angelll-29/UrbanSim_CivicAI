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
        "file": "Mumbai Aided Schools Map.kml",
        "category": "aided",
        "name_col": "SchName",
        "address_col": "Address",
        "class_from": "Cls_From",
        "class_to": "Cls_To",
        "type_col": "Sch_Type",
        "ward_col": "VillageNam",
        "id_col": "OBJECTID_1",
        "website_col": "Website"
    },
    {
        "file": "Mumbai Unaided Schools Map.kml",
        "category": "unaided",
        "name_col": "Name2",
        "address_col": "Address",
        "class_from": "Cls_From",
        "class_to": "Cls_To",
        "type_col": "School_Typ",
        "ward_col": "Ward",
        "id_col": "OBJECTID_1",
        "website_col": "Website"
    },
    {
        "file": "Mumbai Municipal Primary and Secondary Schools Map.kml",
        "category": "municipal",
        "name_col": "Name2",
        "address_col": "Address",
        "class_from": "Class_From",
        "class_to": "Class_To",
        "type_col": "School_Typ",
        "ward_col": "Ward",
        "id_col": "OBJECTID_1",
        "website_col": "Website"
    }
]


def clean_text(value):

    if pd.isna(value):
        return None

    value = str(value)

    value = re.sub(r"\s+", " ", value)

    value = value.strip()

    return value if value else None


def normalize_ward(value):

    value = clean_text(value)

    if value is None:
        return None

    value = value.upper()

    value = re.sub(r"[^A-Z0-9]", "", value)

    return value if value else None


def clean_number(value):

    if pd.isna(value):
        return None

    try:
        return float(value)
    except:
        return None


all_records = []

print("=" * 70)
print("URBANSIM - MUMBAI SCHOOL DATA PROCESSOR")
print("=" * 70)


for config in DATASETS:

    filename = config["file"]

    path = os.path.join(INPUT_DIR, filename)

    print("\n" + "=" * 70)
    print("Processing:", filename)
    print("=" * 70)

    if not os.path.exists(path):

        print("ERROR: File not found")
        continue

    gdf = gpd.read_file(
        path,
        driver="KML"
    )

    print("Source records:", len(gdf))

    processed = 0
    skipped = 0

    for index, row in gdf.iterrows():

        geometry = row.geometry

        if geometry is None or geometry.is_empty:

            skipped += 1
            continue

        if geometry.geom_type != "Point":

            skipped += 1
            continue

        name = clean_text(
            row.get(config["name_col"])
        )

        address = clean_text(
            row.get(config["address_col"])
        )

        ward = normalize_ward(
            row.get(config["ward_col"])
        )

        school_type = clean_text(
            row.get(config["type_col"])
        )

        class_from = clean_text(
            row.get(config["class_from"])
        )

        class_to = clean_text(
            row.get(config["class_to"])
        )

        website = clean_text(
            row.get(config["website_col"])
        )

        source_id = clean_text(
            row.get(config["id_col"])
        )

        latitude = geometry.y
        longitude = geometry.x

        all_records.append({

            "school_id": (
                f"{config['category'].upper()}_"
                f"{index + 1:04d}"
            ),

            "school_name": name,

            "school_category": config["category"],

            "school_type": school_type,

            "address": address,

            "class_from": class_from,

            "class_to": class_to,

            "ward_code_source": ward,

            "latitude": latitude,

            "longitude": longitude,

            "source_file": filename,

            "source_id": source_id,

            "website": website,

            "source": "Mumbai OpenCity / BMC",

            "verification_status": "source_verified",

            "geometry": geometry
        })

        processed += 1

    print("Processed:", processed)
    print("Skipped:", skipped)


# ------------------------------------------------------------
# Create GeoDataFrame
# ------------------------------------------------------------

schools = gpd.GeoDataFrame(
    all_records,
    geometry="geometry",
    crs="EPSG:4326"
)

print("\n" + "=" * 70)
print("INITIAL SCHOOL DATASET")
print("=" * 70)

print("Total processed records:", len(schools))


# ------------------------------------------------------------
# Coordinate validation
# ------------------------------------------------------------

schools["coordinate_valid"] = (
    schools["latitude"].between(-90, 90)
    &
    schools["longitude"].between(-180, 180)
)


invalid_coordinates = (
    ~schools["coordinate_valid"]
).sum()

print(
    "Invalid coordinates:",
    invalid_coordinates
)


# ------------------------------------------------------------
# Exact duplicate detection
# ------------------------------------------------------------

before = len(schools)

schools = schools.drop_duplicates(
    subset=[
        "school_name",
        "school_category",
        "latitude",
        "longitude"
    ]
).copy()

duplicates_removed = before - len(schools)

print(
    "Exact duplicates removed:",
    duplicates_removed
)


# ------------------------------------------------------------
# Generate final IDs
# ------------------------------------------------------------

schools["school_id"] = [
    f"SCH_{i:05d}"
    for i in range(1, len(schools) + 1)
]


# ------------------------------------------------------------
# School category distribution
# ------------------------------------------------------------

print("\nSCHOOL CATEGORY DISTRIBUTION")
print("-" * 40)

print(
    schools["school_category"]
    .value_counts()
)


# ------------------------------------------------------------
# School type distribution
# ------------------------------------------------------------

print("\nSCHOOL TYPE DISTRIBUTION")
print("-" * 40)

print(
    schools["school_type"]
    .value_counts(dropna=False)
    .head(20)
)


# ------------------------------------------------------------
# Source ward distribution
# ------------------------------------------------------------

print("\nSOURCE WARD DISTRIBUTION")
print("-" * 40)

print(
    schools["ward_code_source"]
    .value_counts(dropna=False)
)


# ------------------------------------------------------------
# Save CSV
# ------------------------------------------------------------

csv_file = os.path.join(
    PROCESSED_DIR,
    "mumbai_schools.csv"
)

csv_output = schools.copy()

csv_output["geometry"] = (
    csv_output.geometry.to_wkt()
)

csv_output.to_csv(
    csv_file,
    index=False
)


# ------------------------------------------------------------
# Save GeoJSON
# ------------------------------------------------------------

geojson_file = os.path.join(
    SPATIAL_DIR,
    "mumbai_schools.geojson"
)

schools.to_file(
    geojson_file,
    driver="GeoJSON"
)


# ------------------------------------------------------------
# Save invalid-coordinate report
# ------------------------------------------------------------

invalid_file = os.path.join(
    PROCESSED_DIR,
    "school_invalid_coordinates.csv"
)

schools[
    ~schools["coordinate_valid"]
].to_csv(
    invalid_file,
    index=False
)


print("\n" + "=" * 70)
print("SCHOOL PROCESSING COMPLETE")
print("=" * 70)

print("Final schools:", len(schools))

print(
    "Duplicates removed:",
    duplicates_removed
)

print(
    "Invalid coordinates:",
    invalid_coordinates
)

print("\nCreated files:")

print(
    "data/processed/mumbai_schools.csv"
)

print(
    "data/spatial/mumbai_schools.geojson"
)

print(
    "data/processed/school_invalid_coordinates.csv"
)

print("\nNo original KML files were modified.")

print("=" * 70)

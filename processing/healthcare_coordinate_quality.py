import geopandas as gpd
import pandas as pd
import os

INPUT_FILE = "data/spatial/mumbai_healthcare_validated.geojson"
OUTPUT_DIR = "data/processed"

os.makedirs(OUTPUT_DIR, exist_ok=True)

print("=" * 70)
print("URBANSIM - HEALTHCARE COORDINATE ANOMALY DETECTOR")
print("=" * 70)

gdf = gpd.read_file(INPUT_FILE)

print("\nTotal facilities:", len(gdf))

# ------------------------------------------------------------
# Coordinate validation
# ------------------------------------------------------------

gdf["coordinate_key"] = (
    gdf["latitude"].round(6).astype(str)
    + ","
    + gdf["longitude"].round(6).astype(str)
)

# ------------------------------------------------------------
# Shared coordinates
# ------------------------------------------------------------

coordinate_counts = (
    gdf.groupby("coordinate_key")
    .size()
    .reset_index(name="facility_count")
)

shared_coordinates = coordinate_counts[
    coordinate_counts["facility_count"] > 1
].copy()

gdf["coordinate_status"] = "unique_coordinate"

gdf.loc[
    gdf["coordinate_key"].isin(
        shared_coordinates["coordinate_key"]
    ),
    "coordinate_status"
] = "shared_coordinate"

# ------------------------------------------------------------
# Duplicate names
# ------------------------------------------------------------

name_counts = (
    gdf.groupby("name")
    .size()
    .reset_index(name="name_count")
)

duplicate_names = name_counts[
    name_counts["name_count"] > 1
].copy()

gdf["name_status"] = "unique_name"

gdf.loc[
    gdf["name"].isin(
        duplicate_names["name"]
    ),
    "name_status"
] = "duplicate_name"

# ------------------------------------------------------------
# Suspicious exact coordinate duplicates
# ------------------------------------------------------------

suspicious = gdf[
    gdf["coordinate_status"] == "shared_coordinate"
].copy()

# ------------------------------------------------------------
# Print summary
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("COORDINATE QUALITY SUMMARY")
print("=" * 70)

print(
    "\nUnique coordinate groups:",
    len(coordinate_counts)
)

print(
    "Shared coordinate groups:",
    len(shared_coordinates)
)

print(
    "Facilities using shared coordinates:",
    len(suspicious)
)

print(
    "Duplicate facility names:",
    len(gdf[gdf["name_status"] == "duplicate_name"])
)

# ------------------------------------------------------------
# Show shared coordinates
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("SHARED COORDINATES")
print("=" * 70)

if len(suspicious) == 0:

    print("No shared coordinates found.")

else:

    display_columns = [
        "facility_id",
        "name",
        "service_type",
        "source_ward",
        "gis_ward",
        "latitude",
        "longitude",
        "coordinate_key"
    ]

    print(
        suspicious[
            display_columns
        ].sort_values(
            ["latitude", "longitude"]
        ).to_string(index=False)
    )

# ------------------------------------------------------------
# Save anomaly report
# ------------------------------------------------------------

anomaly_file = os.path.join(
    OUTPUT_DIR,
    "healthcare_coordinate_anomalies.csv"
)

suspicious[
    [
        "facility_id",
        "name",
        "service_type",
        "source_ward",
        "gis_ward",
        "latitude",
        "longitude",
        "coordinate_status",
        "name_status"
    ]
].to_csv(
    anomaly_file,
    index=False
)

# ------------------------------------------------------------
# Save duplicate-name report
# ------------------------------------------------------------

name_file = os.path.join(
    OUTPUT_DIR,
    "healthcare_duplicate_names.csv"
)

gdf[
    gdf["name_status"] == "duplicate_name"
][
    [
        "facility_id",
        "name",
        "service_type",
        "source_ward",
        "gis_ward",
        "latitude",
        "longitude"
    ]
].to_csv(
    name_file,
    index=False
)

print("\n" + "=" * 70)
print("ANOMALY DETECTION COMPLETE")
print("=" * 70)

print("\nCreated:")
print("data/processed/healthcare_coordinate_anomalies.csv")
print("data/processed/healthcare_duplicate_names.csv")

print("\nNo source data was modified.")

print("=" * 70)

import geopandas as gpd
import pandas as pd
import os
import math
import warnings

warnings.filterwarnings("ignore")

HEALTHCARE_FILE = "data/spatial/mumbai_healthcare_validated.geojson"
WARDS_FILE = "data/spatial/mumbai_wards.geojson"

OUTPUT_DIR = "data/processed"

os.makedirs(OUTPUT_DIR, exist_ok=True)


print("=" * 70)
print("URBANSIM - HEALTHCARE GIS QUALITY ANALYSIS")
print("=" * 70)


# ------------------------------------------------------------
# 1. Load data
# ------------------------------------------------------------

print("\nLoading healthcare layer...")

healthcare = gpd.read_file(HEALTHCARE_FILE)

print("Healthcare records:", len(healthcare))


print("\nLoading Mumbai ward boundaries...")

wards = gpd.read_file(WARDS_FILE)

print("Ward polygons:", len(wards))


# ------------------------------------------------------------
# 2. CRS
# ------------------------------------------------------------

if healthcare.crs != wards.crs:
    healthcare = healthcare.to_crs(wards.crs)


# ------------------------------------------------------------
# 3. Identify ward column
# ------------------------------------------------------------

ward_column = None

for column in ["ward_code", "ward_name", "Ward", "WARD", "Name", "name"]:
    if column in wards.columns:
        ward_column = column
        break

if ward_column is None:
    raise ValueError("Ward identification column not found.")

print("Ward column:", ward_column)


# ------------------------------------------------------------
# 4. Prepare ward layer
# ------------------------------------------------------------

ward_layer = wards[
    [ward_column, "geometry"]
].copy()

ward_layer = ward_layer.rename(
    columns={ward_column: "nearest_gis_ward"}
)


# ------------------------------------------------------------
# 5. Spatial join
# ------------------------------------------------------------

print("\nRunning spatial analysis...")

joined = gpd.sjoin(
    healthcare,
    ward_layer,
    how="left",
    predicate="within"
)

joined = joined.drop(
    columns=["index_right"],
    errors="ignore"
)


# ------------------------------------------------------------
# 6. Check coordinate validity
# ------------------------------------------------------------

def valid_coordinate(row):

    lon = row.get("longitude")
    lat = row.get("latitude")

    if pd.isna(lon) or pd.isna(lat):
        return False

    try:
        lon = float(lon)
        lat = float(lat)

        return (
            -180 <= lon <= 180
            and -90 <= lat <= 90
        )

    except:
        return False


joined["coordinate_valid"] = joined.apply(
    valid_coordinate,
    axis=1
)


# ------------------------------------------------------------
# 7. Determine status
# ------------------------------------------------------------

def status(row):

    original_status = row.get("validation_status")

    if not row["coordinate_valid"]:
        return "invalid_coordinates"

    if pd.isna(row.get("gis_ward")):
        return "outside_or_unmatched"

    if original_status == "match":
        return "match"

    return "ward_mismatch"


joined["quality_status"] = joined.apply(
    status,
    axis=1
)


# ------------------------------------------------------------
# 8. Analyze mismatch patterns
# ------------------------------------------------------------

mismatch = joined[
    joined["quality_status"] == "ward_mismatch"
].copy()


print("\n" + "=" * 70)
print("QUALITY SUMMARY")
print("=" * 70)

print("\nTotal facilities:", len(joined))

print("\nQuality status:")
print(
    joined["quality_status"]
    .value_counts(dropna=False)
)


# ------------------------------------------------------------
# 9. Source ward -> GIS ward matrix
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("SOURCE WARD -> GIS WARD MISMATCH PATTERNS")
print("=" * 70)

if len(mismatch) > 0:

    matrix = pd.crosstab(
        mismatch["source_ward"],
        mismatch["gis_ward"]
    )

    print(matrix.to_string())

else:

    print("No ward mismatches found.")


# ------------------------------------------------------------
# 10. Detailed mismatch report
# ------------------------------------------------------------

report_columns = [
    "facility_id",
    "name",
    "service_type",
    "source_ward",
    "gis_ward",
    "nearest_gis_ward",
    "quality_status",
    "latitude",
    "longitude"
]

report_columns = [
    column for column in report_columns
    if column in joined.columns
]

quality_report = joined[
    joined["quality_status"] != "match"
][report_columns].copy()


# ------------------------------------------------------------
# 11. Save quality report
# ------------------------------------------------------------

quality_report_path = os.path.join(
    OUTPUT_DIR,
    "healthcare_gis_quality_report.csv"
)

quality_report.to_csv(
    quality_report_path,
    index=False
)


# ------------------------------------------------------------
# 12. Save ward mismatch matrix
# ------------------------------------------------------------

matrix_path = os.path.join(
    OUTPUT_DIR,
    "healthcare_ward_mismatch_matrix.csv"
)

if len(mismatch) > 0:

    matrix.to_csv(matrix_path)

else:

    pd.DataFrame().to_csv(matrix_path)


# ------------------------------------------------------------
# 13. Save complete analysis dataset
# ------------------------------------------------------------

full_path = os.path.join(
    OUTPUT_DIR,
    "mumbai_healthcare_gis_quality_checked.csv"
)

full_output = joined.copy()

if "geometry" in full_output.columns:
    full_output["geometry"] = full_output.geometry.to_wkt()

full_output.to_csv(
    full_path,
    index=False
)


# ------------------------------------------------------------
# 14. Display outside/unmatched facilities
# ------------------------------------------------------------

outside = joined[
    joined["quality_status"] == "outside_or_unmatched"
].copy()

print("\n" + "=" * 70)
print("OUTSIDE / UNMATCHED FACILITIES")
print("=" * 70)

if len(outside) > 0:

    print(
        outside[
            [
                "facility_id",
                "name",
                "service_type",
                "source_ward",
                "latitude",
                "longitude"
            ]
        ].to_string(index=False)
    )

else:

    print("None")


# ------------------------------------------------------------
# 15. Coordinate problems
# ------------------------------------------------------------

invalid = joined[
    joined["quality_status"] == "invalid_coordinates"
]

print("\n" + "=" * 70)
print("INVALID COORDINATES")
print("=" * 70)

print("Invalid coordinate records:", len(invalid))


# ------------------------------------------------------------
# 16. Output
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("GIS QUALITY ANALYSIS COMPLETE")
print("=" * 70)

print("\nCreated:")

print(
    "data/processed/healthcare_gis_quality_report.csv"
)

print(
    "data/processed/healthcare_ward_mismatch_matrix.csv"
)

print(
    "data/processed/mumbai_healthcare_gis_quality_checked.csv"
)

print("\nNo original healthcare or ward files were modified.")

print("=" * 70)

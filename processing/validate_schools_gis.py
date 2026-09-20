import geopandas as gpd
import pandas as pd
import os
import re
import warnings

warnings.filterwarnings("ignore")

SCHOOLS_FILE = "data/spatial/mumbai_schools.geojson"
WARDS_FILE = "data/spatial/mumbai_wards.geojson"

PROCESSED_DIR = "data/processed"
SPATIAL_DIR = "data/spatial"

os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(SPATIAL_DIR, exist_ok=True)


def clean_ward(value):

    if pd.isna(value):
        return None

    value = str(value).strip().upper()

    # Remove spaces and the word WARD
    value = value.replace("WARD", "")
    value = re.sub(r"\s+", "", value)

    # Remove separators
    value = value.replace("/", "")
    value = value.replace("-", "")
    
    if value == "PN1":
        value = "PN"

    return value if value else None


print("=" * 70)
print("URBANSIM - MUMBAI SCHOOL GIS WARD VALIDATION")
print("=" * 70)


# ------------------------------------------------------------
# 1. Load schools
# ------------------------------------------------------------

print("\nLoading schools...")

schools = gpd.read_file(SCHOOLS_FILE)

print("School records:", len(schools))
print("School CRS:", schools.crs)


# ------------------------------------------------------------
# 2. Load wards
# ------------------------------------------------------------

print("\nLoading Mumbai wards...")

wards = gpd.read_file(WARDS_FILE)

print("Ward polygons:", len(wards))
print("Ward CRS:", wards.crs)


# ------------------------------------------------------------
# 3. CRS alignment
# ------------------------------------------------------------

if schools.crs != wards.crs:

    print("\nConverting school CRS...")

    schools = schools.to_crs(wards.crs)


# ------------------------------------------------------------
# 4. Identify ward column
# ------------------------------------------------------------

ward_column = None

for column in [
    "ward_code",
    "ward_name",
    "Ward",
    "WARD",
    "Name",
    "name"
]:

    if column in wards.columns:

        ward_column = column
        break


if ward_column is None:

    raise ValueError(
        "Could not identify ward column."
    )


print("Ward identification column:", ward_column)


# ------------------------------------------------------------
# 5. Preserve raw source ward
# ------------------------------------------------------------

schools["ward_code_source_raw"] = (
    schools["ward_code_source"]
    .astype("string")
)


# ------------------------------------------------------------
# 6. Normalize source ward
# ------------------------------------------------------------

schools["ward_code_source"] = (
    schools["ward_code_source"]
    .apply(clean_ward)
)


# ------------------------------------------------------------
# 7. Normalize GIS ward
# ------------------------------------------------------------

wards["gis_ward"] = (
    wards[ward_column]
    .apply(clean_ward)
)


# ------------------------------------------------------------
# 8. Prepare ward polygons
# ------------------------------------------------------------

ward_layer = wards[
    ["gis_ward", "geometry"]
].copy()


# ------------------------------------------------------------
# 9. Spatial join
# ------------------------------------------------------------

print("\nPerforming spatial join...")

joined = gpd.sjoin(
    schools,
    ward_layer,
    how="left",
    predicate="within"
)

joined = joined.drop(
    columns=["index_right"],
    errors="ignore"
)


# ------------------------------------------------------------
# 10. Determine final UrbanSim ward
# ------------------------------------------------------------

joined["urban_ward_code"] = joined["gis_ward"]


# ------------------------------------------------------------
# 11. Validation status
# ------------------------------------------------------------

def get_status(row):

    source = row["ward_code_source"]
    gis = row["gis_ward"]

    if pd.isna(gis):

        return "outside_or_unmatched"

    if source is None or pd.isna(source):

        return "source_ward_missing"

    if source == gis:

        return "match"

    return "ward_mismatch"


joined["validation_status"] = joined.apply(
    get_status,
    axis=1
)


# ------------------------------------------------------------
# 12. Summary
# ------------------------------------------------------------

total = len(joined)

matches = (
    joined["validation_status"] == "match"
).sum()

mismatches = (
    joined["validation_status"] == "ward_mismatch"
).sum()

missing = (
    joined["validation_status"] == "source_ward_missing"
).sum()

outside = (
    joined["validation_status"] == "outside_or_unmatched"
).sum()


print("\n" + "=" * 70)
print("SCHOOL GIS VALIDATION RESULTS")
print("=" * 70)

print("Total schools:", total)
print("Ward matches:", matches)
print("Ward mismatches:", mismatches)
print("Missing source ward:", missing)
print("Outside/unmatched:", outside)


if total > 0:

    percentage = (
        matches / total
    ) * 100

else:

    percentage = 0


print(
    "Ward match percentage:",
    round(percentage, 2),
    "%"
)


# ------------------------------------------------------------
# 13. Source ward distribution
# ------------------------------------------------------------

print("\nNORMALIZED SOURCE WARD DISTRIBUTION")
print("-" * 40)

print(
    joined["ward_code_source"]
    .value_counts(dropna=False)
)


# ------------------------------------------------------------
# 14. GIS ward distribution
# ------------------------------------------------------------

print("\nGIS-DERIVED WARD DISTRIBUTION")
print("-" * 40)

print(
    joined["gis_ward"]
    .value_counts(dropna=False)
)


# ------------------------------------------------------------
# 15. Mismatch matrix
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("SOURCE WARD -> GIS WARD")
print("=" * 70)

mismatch_data = joined[
    joined["validation_status"] == "ward_mismatch"
]

if len(mismatch_data) > 0:

    matrix = pd.crosstab(
        mismatch_data["ward_code_source"],
        mismatch_data["gis_ward"]
    )

    print(matrix.to_string())

else:

    print("No mismatches found.")


# ------------------------------------------------------------
# 16. Save validated CSV
# ------------------------------------------------------------

csv_file = os.path.join(
    PROCESSED_DIR,
    "mumbai_schools_validated.csv"
)

csv_output = joined.copy()

csv_output["geometry"] = (
    csv_output.geometry.to_wkt()
)

csv_output.to_csv(
    csv_file,
    index=False
)


# ------------------------------------------------------------
# 17. Save mismatch report
# ------------------------------------------------------------

mismatch_file = os.path.join(
    PROCESSED_DIR,
    "school_ward_mismatches.csv"
)

joined[
    joined["validation_status"] != "match"
].to_csv(
    mismatch_file,
    index=False
)


# ------------------------------------------------------------
# 18. Save spatial GeoJSON
# ------------------------------------------------------------

geojson_file = os.path.join(
    SPATIAL_DIR,
    "mumbai_schools_validated.geojson"
)

joined.to_file(
    geojson_file,
    driver="GeoJSON"
)


print("\n" + "=" * 70)
print("SCHOOL GIS VALIDATION COMPLETE")
print("=" * 70)

print("\nCreated:")
print(
    "data/processed/mumbai_schools_validated.csv"
)

print(
    "data/processed/school_ward_mismatches.csv"
)

print(
    "data/spatial/mumbai_schools_validated.geojson"
)

print("\nOriginal KML files were not modified.")

print("=" * 70)

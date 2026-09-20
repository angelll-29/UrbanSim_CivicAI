import geopandas as gpd
import pandas as pd
import os
import re
import warnings

warnings.filterwarnings("ignore")

HEALTHCARE_FILE = "data/spatial/mumbai_healthcare_facilities.geojson"
WARDS_FILE = "data/spatial/mumbai_wards.geojson"

PROCESSED_DIR = "data/processed"
SPATIAL_DIR = "data/spatial"

os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(SPATIAL_DIR, exist_ok=True)


def normalize_ward(value):
    if pd.isna(value):
        return None

    value = str(value).strip().upper()
    value = re.sub(r"[^A-Z0-9]", "", value)

    return value if value else None


print("=" * 70)
print("URBANSIM - HEALTHCARE GIS WARD VALIDATION")
print("=" * 70)

# ------------------------------------------------------------
# 1. Load healthcare facilities
# ------------------------------------------------------------

print("\nLoading healthcare facilities...")

healthcare = gpd.read_file(HEALTHCARE_FILE)

print("Healthcare records:", len(healthcare))
print("Healthcare CRS:", healthcare.crs)


# ------------------------------------------------------------
# 2. Load Mumbai wards
# ------------------------------------------------------------

print("\nLoading Mumbai ward boundaries...")

wards = gpd.read_file(WARDS_FILE)

print("Ward polygons:", len(wards))
print("Ward CRS:", wards.crs)


# ------------------------------------------------------------
# 3. Check CRS
# ------------------------------------------------------------

if healthcare.crs != wards.crs:
    print("\nConverting healthcare CRS to ward CRS...")
    healthcare = healthcare.to_crs(wards.crs)


# ------------------------------------------------------------
# 4. Identify ward-code column
# ------------------------------------------------------------

possible_ward_columns = [
    "ward_code",
    "ward_name",
    "Ward",
    "WARD",
    "name",
    "Name"
]

ward_column = None

for column in possible_ward_columns:
    if column in wards.columns:
        ward_column = column
        break

if ward_column is None:
    raise ValueError(
        "Could not identify the ward code/name column in ward GeoJSON."
    )

print("Ward identification column:", ward_column)


# ------------------------------------------------------------
# 5. Create normalized source ward
# ------------------------------------------------------------

healthcare["source_ward"] = healthcare["ward_code"].apply(
    normalize_ward
)

wards["gis_ward"] = wards[ward_column].apply(
    normalize_ward
)


# ------------------------------------------------------------
# 6. Keep only required ward information
# ------------------------------------------------------------

wards_join = wards[
    ["gis_ward", "geometry"]
].copy()


# ------------------------------------------------------------
# 7. Spatial join
# ------------------------------------------------------------

print("\nPerforming spatial join...")

joined = gpd.sjoin(
    healthcare,
    wards_join,
    how="left",
    predicate="within"
)

joined = joined.drop(
    columns=["index_right"],
    errors="ignore"
)


# ------------------------------------------------------------
# 8. Validation status
# ------------------------------------------------------------

joined["ward_match"] = (
    joined["source_ward"] == joined["gis_ward"]
)

joined.loc[
    joined["source_ward"].isna() |
    joined["gis_ward"].isna(),
    "ward_match"
] = False


def validation_status(row):

    source = row["source_ward"]
    gis = row["gis_ward"]

    if gis is None or pd.isna(gis):
        return "outside_or_unmatched"

    if source is None or pd.isna(source):
        return "source_ward_missing"

    if source == gis:
        return "match"

    return "mismatch"


joined["validation_status"] = joined.apply(
    validation_status,
    axis=1
)


# ------------------------------------------------------------
# 9. Summary
# ------------------------------------------------------------

total = len(joined)

matches = (
    joined["validation_status"] == "match"
).sum()

mismatches = (
    joined["validation_status"] == "mismatch"
).sum()

missing_source = (
    joined["validation_status"] == "source_ward_missing"
).sum()

outside = (
    joined["validation_status"] == "outside_or_unmatched"
).sum()


print("\n" + "=" * 70)
print("GIS VALIDATION RESULTS")
print("=" * 70)

print("Total healthcare facilities:", total)
print("Ward matches:", matches)
print("Ward mismatches:", mismatches)
print("Missing source ward:", missing_source)
print("Outside/unmatched ward:", outside)


# ------------------------------------------------------------
# 10. Match percentage
# ------------------------------------------------------------

if total > 0:
    match_percentage = (matches / total) * 100
else:
    match_percentage = 0

print(
    "Ward match percentage:",
    round(match_percentage, 2),
    "%"
)


# ------------------------------------------------------------
# 11. Mismatch table
# ------------------------------------------------------------

mismatch_columns = [
    "facility_id",
    "name",
    "service_type",
    "source_ward",
    "gis_ward",
    "validation_status",
    "latitude",
    "longitude"
]

mismatches_df = joined[
    joined["validation_status"] != "match"
][mismatch_columns].copy()


# ------------------------------------------------------------
# 12. Save full validated dataset
# ------------------------------------------------------------

output_csv = os.path.join(
    PROCESSED_DIR,
    "mumbai_healthcare_validated.csv"
)

csv_output = joined.copy()

if "geometry" in csv_output.columns:
    csv_output["geometry"] = csv_output.geometry.to_wkt()

csv_output.to_csv(
    output_csv,
    index=False
)


# ------------------------------------------------------------
# 13. Save mismatch report
# ------------------------------------------------------------

mismatch_csv = os.path.join(
    PROCESSED_DIR,
    "healthcare_ward_mismatches.csv"
)

mismatches_df.to_csv(
    mismatch_csv,
    index=False
)


# ------------------------------------------------------------
# 14. Save spatial output
# ------------------------------------------------------------

spatial_output = os.path.join(
    SPATIAL_DIR,
    "mumbai_healthcare_validated.geojson"
)

joined.to_file(
    spatial_output,
    driver="GeoJSON"
)


# ------------------------------------------------------------
# 15. Ward distribution based on GIS
# ------------------------------------------------------------

print("\nGIS-DERIVED WARD DISTRIBUTION")
print("-" * 40)

print(
    joined["gis_ward"]
    .value_counts(dropna=False)
)


# ------------------------------------------------------------
# 16. Mismatch details
# ------------------------------------------------------------

print("\nNON-MATCHED RECORDS")
print("-" * 40)

if len(mismatches_df) == 0:

    print("No mismatches found.")

else:

    print(
        mismatches_df[
            [
                "facility_id",
                "name",
                "source_ward",
                "gis_ward",
                "validation_status"
            ]
        ].to_string(index=False)
    )


# ------------------------------------------------------------
# 17. Output files
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("GIS VALIDATION COMPLETE")
print("=" * 70)

print("\nCreated files:")
print(output_csv)
print(mismatch_csv)
print(spatial_output)

print("\nThese outputs preserve both:")
print("- Source ward from the healthcare dataset")
print("- GIS-derived ward from the 24 Mumbai ward polygons")

print("=" * 70)

import pandas as pd
import geopandas as gpd
from pathlib import Path

# --------------------------------------------------
# Files
# --------------------------------------------------

COMPLAINTS_FILE = Path(
    "data/processed/complaints_transformed.csv"
)

WARD_FILE = Path(
    "data/spatial/mumbai_wards.geojson"
)

OUTPUT_CSV = Path(
    "data/processed/mumbai_complaints_validated.csv"
)

OUTPUT_MISMATCH = Path(
    "data/processed/complaint_ward_mismatches.csv"
)

OUTPUT_GEOJSON = Path(
    "data/spatial/mumbai_complaints_validated.geojson"
)


print("=" * 70)
print("URBANSIM - COMPLAINT GIS WARD VALIDATION")
print("=" * 70)


# --------------------------------------------------
# Load complaints
# --------------------------------------------------

print("\nLoading complaints...")

complaints = pd.read_csv(COMPLAINTS_FILE)

print("Complaint records:", len(complaints))


# --------------------------------------------------
# Validate coordinates
# --------------------------------------------------

complaints["latitude"] = pd.to_numeric(
    complaints["latitude"],
    errors="coerce"
)

complaints["longitude"] = pd.to_numeric(
    complaints["longitude"],
    errors="coerce"
)

valid_coordinates = (
    complaints["latitude"].notna()
    & complaints["longitude"].notna()
)

complaints = complaints[valid_coordinates].copy()

print("Valid coordinate records:", len(complaints))


# --------------------------------------------------
# Create complaint points
# --------------------------------------------------

complaints_gdf = gpd.GeoDataFrame(
    complaints,
    geometry=gpd.points_from_xy(
        complaints["longitude"],
        complaints["latitude"]
    ),
    crs="EPSG:4326"
)


# --------------------------------------------------
# Load Mumbai wards
# --------------------------------------------------

print("\nLoading Mumbai ward boundaries...")

wards = gpd.read_file(WARD_FILE)

print("Ward polygons:", len(wards))
print("Ward CRS:", wards.crs)


# --------------------------------------------------
# Normalize CRS
# --------------------------------------------------

if wards.crs != complaints_gdf.crs:
    wards = wards.to_crs(complaints_gdf.crs)


# --------------------------------------------------
# Identify ward column
# --------------------------------------------------

if "ward_code" in wards.columns:
    ward_column = "ward_code"
elif "Name" in wards.columns:
    ward_column = "Name"
else:
    raise ValueError(
        "Could not find ward identification column."
    )

print("Ward identification column:", ward_column)


# --------------------------------------------------
# Spatial join
# --------------------------------------------------

print("\nPerforming spatial join...")

joined = gpd.sjoin(
    complaints_gdf,
    wards[[ward_column, "geometry"]],
    how="left",
    predicate="within"
)

joined = joined.rename(
    columns={ward_column: "gis_ward"}
)

# Clean ward names coming from the GIS polygon layer
joined["gis_ward"] = (
    joined["gis_ward"]
    .astype(str)
    .str.replace(r"[\r\n\t]+", "", regex=True)
    .str.strip()
    .str.upper()
)

WARD_NORMALIZATION = {
    "H/E": "HE",
    "H/W": "HW",
    "K/E": "KE",
    "K/W": "KW",
    "M/E": "ME",
    "M/W": "MW",
    "P/N": "PN",
    "P/S": "PS",
    "R/C": "RC",
    "R/N": "RN",
    "R/S": "RS",
    "F/N": "FN",
    "F/S": "FS",
    "G/N": "GN",
    "G/S": "GS",
}

joined["gis_ward"] = (
    joined["gis_ward"]
    .replace(WARD_NORMALIZATION)
)

# --------------------------------------------------
# Remove spatial join index if present
# --------------------------------------------------

if "index_right" in joined.columns:
    joined = joined.drop(columns=["index_right"])


# --------------------------------------------------
# Validation status
# --------------------------------------------------

joined["validation_status"] = joined.apply(
    lambda row: (
        "gis_ward_assigned"
        if pd.notna(row["gis_ward"])
        else "outside_or_unmatched"
    ),
    axis=1
)


# --------------------------------------------------
# Results
# --------------------------------------------------

total = len(joined)

matched = (
    joined["gis_ward"].notna()
).sum()

unmatched = total - matched

match_percentage = (
    matched / total * 100
    if total > 0 else 0
)


print("\n" + "=" * 70)
print("GIS VALIDATION RESULTS")
print("=" * 70)

print("Total complaints:", total)
print("GIS ward matches:", matched)
print("Outside/unmatched:", unmatched)
print(
    "GIS ward match percentage:",
    round(match_percentage, 2),
    "%"
)


# --------------------------------------------------
# Ward distribution
# --------------------------------------------------

print("\nGIS-DERIVED WARD DISTRIBUTION")
print("-" * 40)

print(
    joined["gis_ward"]
    .value_counts(dropna=False)
    .sort_index()
    .to_string()
)


# --------------------------------------------------
# Non-matched records
# --------------------------------------------------

nonmatched = joined[
    joined["gis_ward"].isna()
].copy()

print("\nNON-MATCHED RECORDS")
print("-" * 40)

if len(nonmatched) > 0:
    display_columns = [
        "complaint_id",
        "ward_id",
        "category",
        "latitude",
        "longitude",
        "status",
        "validation_status"
    ]

    print(
        nonmatched[
            display_columns
        ].to_string(index=False)
    )
else:
    print("None")


# --------------------------------------------------
# Save CSV
# --------------------------------------------------

csv_output = joined.copy()

# Convert geometry to WKT for CSV
csv_output["geometry"] = (
    csv_output.geometry.astype(str)
)

csv_output.to_csv(
    OUTPUT_CSV,
    index=False
)


# --------------------------------------------------
# Save mismatch file
# --------------------------------------------------

if len(nonmatched) > 0:
    mismatch_output = nonmatched.copy()
    mismatch_output["geometry"] = (
        mismatch_output.geometry.astype(str)
    )

    mismatch_output.to_csv(
        OUTPUT_MISMATCH,
        index=False
    )
else:
    pd.DataFrame(
        columns=[
            "complaint_id",
            "ward_id",
            "category",
            "latitude",
            "longitude",
            "status",
            "validation_status"
        ]
    ).to_csv(
        OUTPUT_MISMATCH,
        index=False
    )


# --------------------------------------------------
# Save GeoJSON
# --------------------------------------------------

joined.to_file(
    OUTPUT_GEOJSON,
    driver="GeoJSON"
)


print("\n" + "=" * 70)
print("GIS VALIDATION COMPLETE")
print("=" * 70)

print("\nCreated files:")
print(OUTPUT_CSV)
print(OUTPUT_MISMATCH)
print(OUTPUT_GEOJSON)

print("\nThe dataset preserves:")
print("- Original complaint ward_id")
print("- GIS-derived BMC ward")
print("- Complaint coordinates")
print("- Complaint category/status")
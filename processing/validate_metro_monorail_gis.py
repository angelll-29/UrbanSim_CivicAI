from pathlib import Path

import geopandas as gpd
import pandas as pd


# ============================================================
# FILES
# ============================================================

STATIONS_FILE = Path(
    "data/processed/mumbai_metro_monorail_stations.csv"
)

WARDS_FILE = Path(
    "data/spatial/mumbai_wards.geojson"
)

OUTPUT_CSV = Path(
    "data/processed/mumbai_metro_monorail_validated.csv"
)

OUTPUT_GEOJSON = Path(
    "data/spatial/mumbai_metro_monorail_validated.geojson"
)

MISMATCH_FILE = Path(
    "data/processed/metro_monorail_ward_mismatches.csv"
)


print("=" * 70)
print("URBANSIM - METRO + MONORAIL GIS VALIDATION")
print("=" * 70)


# ============================================================
# LOAD
# ============================================================

df = pd.read_csv(STATIONS_FILE)

print(f"\nStation records: {len(df)}")

# Only stations with coordinates can be spatially joined.
geo_df = df[
    df["latitude"].notna()
    & df["longitude"].notna()
].copy()

print(f"Stations with coordinates: {len(geo_df)}")
print(f"Stations without coordinates: {len(df) - len(geo_df)}")


# ============================================================
# CREATE STATION GEODATAFRAME
# ============================================================

stations = gpd.GeoDataFrame(
    geo_df,
    geometry=gpd.points_from_xy(
        geo_df["longitude"],
        geo_df["latitude"]
    ),
    crs="EPSG:4326",
)


# ============================================================
# LOAD BMC WARDS
# ============================================================

wards = gpd.read_file(WARDS_FILE)

print(f"BMC ward polygons: {len(wards)}")
print(f"Ward CRS: {wards.crs}")


# Ensure same CRS

if wards.crs != stations.crs:
    wards = wards.to_crs(stations.crs)


# ============================================================
# IDENTIFY WARD FIELD
# ============================================================

print("\nWard columns:")
print(wards.columns.tolist())


# Your existing Mumbai ward GeoJSON uses "Name".
WARD_FIELD = "Name"

if WARD_FIELD not in wards.columns:
    raise ValueError(
        f"Ward field '{WARD_FIELD}' not found. "
        f"Available fields: {wards.columns.tolist()}"
    )


# ============================================================
# SPATIAL JOIN
# ============================================================

joined = gpd.sjoin(
    stations,
    wards[[WARD_FIELD, "geometry"]],
    how="left",
    predicate="within",
)


# ============================================================
# CLEAN WARD COLUMN
# ============================================================

joined = joined.rename(
    columns={
        WARD_FIELD: "gis_ward"
    }
)

joined = joined.drop(
    columns=["index_right"],
    errors="ignore",
)


# ============================================================
# NORMALIZE WARD CODES
# ============================================================

def normalize_ward(value):

    if pd.isna(value):
        return pd.NA

    value = str(value).strip().upper()

    mapping = {
        "F/N": "FN",
        "F/S": "FS",
        "G/N": "GN",
        "G/S": "GS",
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
    }

    return mapping.get(value, value)


joined["gis_ward"] = joined["gis_ward"].apply(
    normalize_ward
)


# ============================================================
# VALIDATION STATUS
# ============================================================

joined["gis_match"] = joined["gis_ward"].notna()

joined["gis_match_status"] = joined["gis_match"].map(
    {
        True: "MATCHED",
        False: "OUTSIDE_BMC_WARDS",
    }
)


# ============================================================
# SAVE CSV
# ============================================================

csv_output = joined.drop(
    columns=["geometry"]
)

csv_output.to_csv(
    OUTPUT_CSV,
    index=False,
)


# ============================================================
# SAVE GEOJSON
# ============================================================

joined.to_file(
    OUTPUT_GEOJSON,
    driver="GeoJSON",
)


# ============================================================
# SAVE OUTSIDE-BMC RECORDS
# ============================================================

outside = joined[
    joined["gis_ward"].isna()
].copy()

outside.drop(
    columns=["geometry"],
    errors="ignore",
).to_csv(
    MISMATCH_FILE,
    index=False,
)


# ============================================================
# REPORT
# ============================================================

matched = int(joined["gis_match"].sum())
outside_count = int((~joined["gis_match"]).sum())

print("\n" + "=" * 70)
print("GIS VALIDATION COMPLETE")
print("=" * 70)

print(f"Coordinates processed : {len(joined)}")
print(f"BMC ward matched      : {matched}")
print(f"Outside BMC wards     : {outside_count}")

print(
    f"Match rate            : "
    f"{matched / len(joined) * 100:.2f}%"
)

print("\nTransport mode:")
print(
    joined["transport_mode"]
    .value_counts()
    .to_string()
)

print("\nWard distribution:")

print(
    joined["gis_ward"]
    .value_counts()
    .sort_index()
    .to_string()
)

print("\nOutput CSV:")
print(OUTPUT_CSV)

print("\nOutput GeoJSON:")
print(OUTPUT_GEOJSON)

print("\nOutside-BMC file:")
print(MISMATCH_FILE)

print("=" * 70)
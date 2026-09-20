from pathlib import Path

import pandas as pd


# ============================================================
# FILES
# ============================================================

INPUT_FILE = Path(
    "data/processed/mumbai_metro_monorail_validated.csv"
)

OUTPUT_FILE = Path(
    "data/processed/mumbai_metro_monorail_ward_summary.csv"
)


# ============================================================
# LOAD DATA
# ============================================================

df = pd.read_csv(INPUT_FILE)

print("=" * 70)
print("URBANSIM - METRO + MONORAIL WARD SUMMARY")
print("=" * 70)

print(f"\nValidated station records: {len(df)}")


# Only records assigned to a BMC ward

df = df[
    df["gis_ward"].notna()
].copy()

print(f"BMC ward-assigned records: {len(df)}")


# ============================================================
# CREATE INDICATORS
# ============================================================

df["is_metro"] = (
    df["transport_mode"] == "Metro"
).astype(int)

df["is_monorail"] = (
    df["transport_mode"] == "Monorail"
).astype(int)

df["is_operational"] = (
    df["status"].astype(str).str.lower()
    == "operational"
).astype(int)

df["is_under_construction"] = (
    df["status"].astype(str).str.lower()
    == "under construction"
).astype(int)


# ============================================================
# WARD AGGREGATION
# ============================================================

summary = (
    df.groupby("gis_ward")
    .agg(
        metro_station_count=("is_metro", "sum"),
        monorail_station_count=("is_monorail", "sum"),
        operational_station_count=(
            "is_operational",
            "sum",
        ),
        under_construction_station_count=(
            "is_under_construction",
            "sum",
        ),
        total_metro_monorail_stations=(
            "station_id",
            "count",
        ),
    )
    .reset_index()
)


# ============================================================
# RENAME WARD
# ============================================================

summary = summary.rename(
    columns={
        "gis_ward": "ward_code"
    }
)


# ============================================================
# ENSURE ALL 24 BMC WARDS EXIST
# ============================================================

BMC_WARDS = [
    "A",
    "B",
    "C",
    "D",
    "E",
    "FN",
    "FS",
    "GN",
    "GS",
    "HE",
    "HW",
    "KE",
    "KW",
    "L",
    "ME",
    "MW",
    "N",
    "PN",
    "PS",
    "RC",
    "RN",
    "RS",
    "S",
    "T",
]

ward_master = pd.DataFrame(
    {
        "ward_code": BMC_WARDS
    }
)

summary = ward_master.merge(
    summary,
    on="ward_code",
    how="left",
)


# Fill only aggregation counts with zero.

count_columns = [
    "metro_station_count",
    "monorail_station_count",
    "operational_station_count",
    "under_construction_station_count",
    "total_metro_monorail_stations",
]

summary[count_columns] = (
    summary[count_columns]
    .fillna(0)
    .astype(int)
)


# ============================================================
# DERIVED INDICATORS
# ============================================================

summary["metro_share_pct"] = (
    summary["metro_station_count"]
    / summary["total_metro_monorail_stations"]
    .replace(0, pd.NA)
    * 100
)

summary["monorail_share_pct"] = (
    summary["monorail_station_count"]
    / summary["total_metro_monorail_stations"]
    .replace(0, pd.NA)
    * 100
)


# ============================================================
# SAVE
# ============================================================

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True,
)

summary.to_csv(
    OUTPUT_FILE,
    index=False,
)


# ============================================================
# REPORT
# ============================================================

print("\nWard summary:")
print(
    summary.to_string(index=False)
)

print("\nTotals:")
print(
    summary[count_columns]
    .sum()
    .to_string()
)

print("\nOutput:")
print(OUTPUT_FILE)

print("=" * 70)
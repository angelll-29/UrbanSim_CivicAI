from pathlib import Path

import pandas as pd


# ============================================================
# FILES
# ============================================================

BASE_FILE = Path(
    "data/processed/mumbai_ward_civic_intelligence_base_multimodal.csv"
)

METRO_MONO_FILE = Path(
    "data/processed/mumbai_metro_monorail_ward_summary.csv"
)

OUTPUT_FILE = Path(
    "data/processed/mumbai_ward_civic_intelligence_base_full_transport.csv"
)


# ============================================================
# LOAD
# ============================================================

base = pd.read_csv(BASE_FILE)
transport = pd.read_csv(METRO_MONO_FILE)

print("=" * 70)
print("URBANSIM - FULL TRANSPORT INTEGRATION")
print("=" * 70)

print(f"\nBase wards: {len(base)}")
print(f"Metro/Monorail wards: {len(transport)}")


# ============================================================
# CHECK WARD COLUMN
# ============================================================

print("\nBase columns containing ward:")
print(
    [
        col for col in base.columns
        if "ward" in col.lower()
    ]
)

print("\nTransport columns:")
print(transport.columns.tolist())


# Existing datasets use ward_code.
WARD_COLUMN = "ward_code"

if WARD_COLUMN not in base.columns:
    raise ValueError(
        f"'{WARD_COLUMN}' not found in base dataset."
    )

if WARD_COLUMN not in transport.columns:
    raise ValueError(
        f"'{WARD_COLUMN}' not found in transport dataset."
    )


# ============================================================
# REMOVE OLD METRO/MONORAIL COLUMNS IF RE-RUNNING
# ============================================================

transport_columns = [
    "metro_station_count",
    "monorail_station_count",
    "operational_station_count",
    "under_construction_station_count",
    "total_metro_monorail_stations",
    "metro_share_pct",
    "monorail_share_pct",
]

existing_columns = [
    col for col in transport_columns
    if col in base.columns
]

if existing_columns:
    base = base.drop(
        columns=existing_columns
    )


# ============================================================
# MERGE
# ============================================================

merged = base.merge(
    transport,
    on=WARD_COLUMN,
    how="left",
    validate="one_to_one",
)


# ============================================================
# VALIDATE
# ============================================================

if len(merged) != 24:
    raise ValueError(
        f"Expected 24 wards after merge, "
        f"got {len(merged)}."
    )


# No missing transport counts.

for col in transport_columns:

    if col in merged.columns:

        merged[col] = merged[col].fillna(0)


# ============================================================
# SAVE
# ============================================================

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True,
)

merged.to_csv(
    OUTPUT_FILE,
    index=False,
)


# ============================================================
# REPORT
# ============================================================

print("\n" + "=" * 70)
print("INTEGRATION COMPLETE")
print("=" * 70)

print(f"Wards: {len(merged)}")
print(f"Columns: {len(merged.columns)}")

print("\nTransport totals:")

for col in [
    "bus_stop_count",
    "bus_depot_count",
    "railway_station_count",
    "metro_station_count",
    "monorail_station_count",
    "total_metro_monorail_stations",
]:
    if col in merged.columns:
        print(
            f"{col:35s}: "
            f"{merged[col].sum():.0f}"
        )

print("\nOutput:")
print(OUTPUT_FILE)

print("=" * 70)
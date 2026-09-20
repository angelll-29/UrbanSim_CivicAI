from pathlib import Path
import pandas as pd

INPUT = Path(
    "data/processed/mumbai_air_quality_stations_validated.csv"
)

OUTPUT = Path(
    "data/processed/mumbai_air_quality_stations_validated.csv"
)

WARD_MAP = {
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

df = pd.read_csv(INPUT)

df["gis_ward"] = (
    df["gis_ward"]
    .astype(str)
    .str.strip()
)

df["urban_ward_code"] = (
    df["gis_ward"]
    .replace(WARD_MAP)
)

df.to_csv(
    OUTPUT,
    index=False
)

print("Environmental ward normalization complete.")
print()
print(
    df["urban_ward_code"]
    .value_counts()
    .sort_index()
    .to_string()
)

print()
print("Unique BMC wards represented:",
      df["urban_ward_code"].nunique())

print("Output:", OUTPUT)

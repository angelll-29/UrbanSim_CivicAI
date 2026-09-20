from pathlib import Path

import geopandas as gpd
import pandas as pd


WARD_FILE = Path(
    "data/spatial/mumbai_wards.geojson"
)

POPULATION_FILE = Path(
    "data/processed/mumbai_ward_civic_intelligence_base_population.csv"
)

OUTPUT_FILE = Path(
    "data/processed/mumbai_ward_area_density.csv"
)


print("=" * 70)
print("URBANSIM - WARD AREA + POPULATION DENSITY")
print("=" * 70)


# ============================================================
# LOAD WARDS
# ============================================================

wards = gpd.read_file(WARD_FILE)

print(f"\nWard polygons: {len(wards)}")
print(f"Original CRS: {wards.crs}")


# ============================================================
# PROJECT TO METRIC CRS
# ============================================================

# EPSG:32643 = WGS 84 / UTM zone 43N
# Suitable for Mumbai-area metric calculations.

wards_metric = wards.to_crs("EPSG:32643")


# ============================================================
# CALCULATE AREA
# ============================================================

wards_metric["area_sq_m"] = (
    wards_metric.geometry.area
)

wards_metric["area_sq_km"] = (
    wards_metric["area_sq_m"] / 1_000_000
)


# ============================================================
# PREPARE WARD DATA
# ============================================================

area = wards_metric[
    ["Name", "area_sq_m", "area_sq_km"]
].copy()

area = area.rename(
    columns={
        "Name": "ward_code"
    }
)


# ============================================================
# NORMALIZE WARD CODES
# ============================================================

def normalize_ward(value):

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


area["ward_code"] = area["ward_code"].apply(
    normalize_ward
)


# ============================================================
# LOAD POPULATION
# ============================================================

population = pd.read_csv(
    POPULATION_FILE
)

population = population[
    [
        "ward_code",
        "population_2011"
    ]
]


# ============================================================
# MERGE
# ============================================================

result = area.merge(
    population,
    on="ward_code",
    how="left",
    validate="one_to_one"
)


# ============================================================
# VALIDATE
# ============================================================

if len(result) != 24:
    raise ValueError(
        f"Expected 24 wards, got {len(result)}"
    )

if result["population_2011"].isna().any():
    raise ValueError(
        "Population missing for one or more wards."
    )


# ============================================================
# POPULATION DENSITY
# ============================================================

result["population_density_per_sq_km"] = (
    result["population_2011"]
    / result["area_sq_km"]
)


# ============================================================
# ROUND
# ============================================================

result["area_sq_m"] = result["area_sq_m"].round(2)
result["area_sq_km"] = result["area_sq_km"].round(4)

result["population_density_per_sq_km"] = (
    result["population_density_per_sq_km"]
    .round(2)
)


# ============================================================
# SAVE
# ============================================================

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)

result.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# REPORT
# ============================================================

print("\nWard area + density:")
print(
    result[
        [
            "ward_code",
            "area_sq_km",
            "population_2011",
            "population_density_per_sq_km"
        ]
    ]
    .sort_values("ward_code")
    .to_string(index=False)
)

print("\nTotal mapped area:")
print(
    f"{result['area_sq_km'].sum():.2f} km²"
)

print("\nOutput:")
print(OUTPUT_FILE)

print("=" * 70)
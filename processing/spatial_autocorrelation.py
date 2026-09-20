import geopandas as gpd
import pandas as pd
import numpy as np
from libpysal.weights import Queen
from esda.moran import Moran, Moran_Local

INPUT = "data/spatial/mumbai_urban_stress_v2.geojson"
CSV_OUTPUT = "data/processed/mumbai_urban_stress_spatial_stats.csv"
GEOJSON_OUTPUT = "data/spatial/mumbai_urban_stress_hotspots.geojson"

print("Loading Urban Stress GIS layer...")
gdf = gpd.read_file(INPUT)

# Use the actual fields present in the UrbanSim GIS layer
gdf = gdf.sort_values("ward_code").reset_index(drop=True)

if "urban_stress_index" not in gdf.columns:
    raise ValueError("urban_stress_index field not found.")

y = gdf["urban_stress_index"].astype(float).to_numpy()

print(f"Wards: {len(gdf)}")
print(f"Stress range: {y.min():.2f} - {y.max():.2f}")

# ---------------------------------------------------------
# 1. Queen contiguity
# ---------------------------------------------------------
print("\nBuilding Queen contiguity weights...")

w = Queen.from_dataframe(gdf, use_index=False)
w.transform = "r"

print(f"Number of spatial islands: {len(w.islands)}")

if w.islands:
    print("WARNING: Spatial islands detected:")
    print(w.islands)

# ---------------------------------------------------------
# 2. Global Moran's I
# ---------------------------------------------------------
print("\nCalculating Global Moran's I...")

moran = Moran(y, w, permutations=999)

print(f"Moran's I: {moran.I:.4f}")
print(f"Expected I: {moran.EI:.4f}")
print(f"Permutation p-value: {moran.p_sim:.4f}")
print(f"z-score: {moran.z_sim:.4f}")

# ---------------------------------------------------------
# 3. Local Moran's I (LISA)
# ---------------------------------------------------------
print("\nCalculating Local Moran's I (LISA)...")

local = Moran_Local(y, w, permutations=999, seed=42)

z = (y - y.mean()) / y.std(ddof=1)
lag_z = w.sparse @ z

def classify_lisa(z_value, lag_value, p_value):
    if p_value >= 0.05:
        return "Not Significant"

    if z_value >= 0 and lag_value >= 0:
        return "High-High"

    if z_value < 0 and lag_value < 0:
        return "Low-Low"

    if z_value >= 0 and lag_value < 0:
        return "High-Low"

    return "Low-High"

gdf["moran_local_i"] = local.Is
gdf["moran_local_p"] = local.p_sim
gdf["moran_local_z"] = local.z_sim
gdf["spatial_lag_z"] = lag_z

gdf["lisa_cluster"] = [
    classify_lisa(zv, lv, pv)
    for zv, lv, pv in zip(z, lag_z, local.p_sim)
]

gdf["lisa_significant"] = gdf["moran_local_p"] < 0.05

# Global statistics
gdf["global_moran_i"] = moran.I
gdf["global_moran_expected_i"] = moran.EI
gdf["global_moran_p"] = moran.p_sim
gdf["global_moran_z"] = moran.z_sim

# ---------------------------------------------------------
# 4. Save CSV
# ---------------------------------------------------------
csv_columns = [
    "ward_code",
    "urban_stress_index",
    "urban_stress_band",
    "moran_local_i",
    "moran_local_p",
    "moran_local_z",
    "spatial_lag_z",
    "lisa_cluster",
    "lisa_significant",
    "global_moran_i",
    "global_moran_expected_i",
    "global_moran_p",
    "global_moran_z",
]

result = gdf[csv_columns].copy()
result.to_csv(CSV_OUTPUT, index=False)

# ---------------------------------------------------------
# 5. Save GIS layer
# ---------------------------------------------------------
gdf.to_file(GEOJSON_OUTPUT, driver="GeoJSON")

# ---------------------------------------------------------
# 6. Summary
# ---------------------------------------------------------
print("\n========================================")
print("SPATIAL ANALYSIS COMPLETE")
print("========================================")

print(f"\nGlobal Moran's I : {moran.I:.4f}")
print(f"Expected I       : {moran.EI:.4f}")
print(f"Permutation p    : {moran.p_sim:.4f}")
print(f"z-score          : {moran.z_sim:.4f}")

print("\nLISA cluster counts:")
print(result["lisa_cluster"].value_counts())

print("\nSignificant wards:")
significant = result[result["lisa_significant"]]

if len(significant) == 0:
    print("No statistically significant local clusters at p < 0.05.")
else:
    print(
        significant[
            [
                "ward_code",
                "urban_stress_index",
                "moran_local_i",
                "moran_local_p",
                "lisa_cluster",
            ]
        ].to_string(index=False)
    )

print(f"\nSaved:")
print(CSV_OUTPUT)
print(GEOJSON_OUTPUT)

import pandas as pd
import numpy as np
from pathlib import Path

FEATURE_FILE = Path("data/processed/urban_ai_features.csv")
CLUSTER_FILE = Path("data/processed/mumbai_ward_clusters.csv")

OUTPUT_PROFILE = Path(
    "data/processed/urban_cluster_profiles.csv"
)

OUTPUT_ZSCORES = Path(
    "data/processed/urban_cluster_feature_zscores.csv"
)

# --------------------------------------------------
# Load data
# --------------------------------------------------
features = pd.read_csv(FEATURE_FILE)
clusters = pd.read_csv(CLUSTER_FILE)

df = features.merge(
    clusters[["ward_code", "cluster_id", "cluster"]],
    on="ward_code",
    how="left"
)

feature_cols = [
    c for c in features.columns
    if c != "ward_code"
]

# --------------------------------------------------
# Cluster profile
# --------------------------------------------------
profile = (
    df.groupby("cluster")[feature_cols]
    .mean()
    .round(4)
)

profile.to_csv(OUTPUT_PROFILE)

# --------------------------------------------------
# Overall means
# --------------------------------------------------
overall_mean = df[feature_cols].mean()

# --------------------------------------------------
# Standardized cluster differences
# --------------------------------------------------
overall_std = df[feature_cols].std(ddof=0)

zscore = (
    profile - overall_mean
) / overall_std.replace(0, np.nan)

zscore = zscore.round(3)

zscore.to_csv(OUTPUT_ZSCORES)

print("=" * 70)
print("URBANSIM CLUSTER PROFILING")
print("=" * 70)

print("\nCluster sizes:")
print(
    df.groupby(["cluster_id", "cluster"])
      .size()
      .to_string()
)

print("\nCluster mean profiles:")
print(profile.to_string())

print("\n" + "=" * 70)
print("MOST DISTINCTIVE FEATURES BY CLUSTER")
print("=" * 70)

for cluster in profile.index:

    print(f"\n{cluster}")
    print("-" * 50)

    values = zscore.loc[cluster].sort_values(
        key=lambda x: x.abs(),
        ascending=False
    )

    print(values.head(8).to_string())

print("\n" + "=" * 70)
print("WARD MEMBERSHIP")
print("=" * 70)

for cluster in sorted(df["cluster"].unique()):

    wards = (
        df.loc[
            df["cluster"] == cluster,
            "ward_code"
        ]
        .sort_values()
        .tolist()
    )

    print(f"\n{cluster}: {', '.join(wards)}")

print("\nSaved:")
print(OUTPUT_PROFILE)
print(OUTPUT_ZSCORES)

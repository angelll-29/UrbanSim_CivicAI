import pandas as pd
import numpy as np
from pathlib import Path

from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, davies_bouldin_score
from sklearn.preprocessing import StandardScaler
import tensorflow as tf

INPUT = Path("data/processed/urban_ward_embeddings_validated.csv")
ENCODER_INPUT = Path("data/processed/urban_ai_features.csv")

OUTPUT_RESULTS = Path(
    "data/processed/urban_clustering_evaluation.csv"
)

OUTPUT_ASSIGNMENTS = Path(
    "data/processed/mumbai_ward_clusters.csv"
)

# --------------------------------------------------
# Load embeddings
# --------------------------------------------------
df = pd.read_csv(INPUT)

wards = df["ward_code"].copy()

embedding_cols = [
    "embedding_1",
    "embedding_2",
    "embedding_3",
    "embedding_4"
]

X = df[embedding_cols].astype(float).values

print("=" * 60)
print("URBANSIM DEEP CLUSTERING")
print("=" * 60)

print("\nSamples:", X.shape[0])
print("Embedding dimensions:", X.shape[1])

# --------------------------------------------------
# Standardize latent embeddings
# --------------------------------------------------
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# --------------------------------------------------
# Test K values
# --------------------------------------------------
results = []

for k in range(2, 7):

    model = KMeans(
        n_clusters=k,
        random_state=42,
        n_init=50
    )

    labels = model.fit_predict(X_scaled)

    silhouette = silhouette_score(
        X_scaled,
        labels
    )

    davies_bouldin = davies_bouldin_score(
        X_scaled,
        labels
    )

    cluster_sizes = np.bincount(labels)

    results.append({
        "k": k,
        "silhouette_score": silhouette,
        "davies_bouldin_score": davies_bouldin,
        "min_cluster_size": cluster_sizes.min(),
        "max_cluster_size": cluster_sizes.max()
    })

results_df = pd.DataFrame(results)

# --------------------------------------------------
# Display evaluation
# --------------------------------------------------
print("\nClustering evaluation:")
print(
    results_df.to_string(index=False)
)

# --------------------------------------------------
# Select candidate K
# --------------------------------------------------
best_silhouette_k = int(
    results_df.loc[
        results_df["silhouette_score"].idxmax(),
        "k"
    ]
)

best_db_k = int(
    results_df.loc[
        results_df["davies_bouldin_score"].idxmin(),
        "k"
    ]
)

print("\nBest silhouette K:", best_silhouette_k)
print("Best Davies-Bouldin K:", best_db_k)

# --------------------------------------------------
# Use silhouette-selected K for initial model
# --------------------------------------------------
selected_k = best_silhouette_k

final_model = KMeans(
    n_clusters=selected_k,
    random_state=42,
    n_init=100
)

final_labels = final_model.fit_predict(X_scaled)

# Make labels human-readable
cluster_names = {
    i: f"Cluster_{i + 1}"
    for i in range(selected_k)
}

assignments = pd.DataFrame({
    "ward_code": wards,
    "cluster_id": final_labels,
    "cluster": [
        cluster_names[x]
        for x in final_labels
    ]
})

# --------------------------------------------------
# Cluster size
# --------------------------------------------------
cluster_counts = (
    assignments["cluster"]
    .value_counts()
    .sort_index()
)

print("\nSelected K:", selected_k)

print("\nCluster sizes:")
print(cluster_counts.to_string())

print("\nWard assignments:")
print(
    assignments
    .sort_values(["cluster_id", "ward_code"])
    .to_string(index=False)
)

# --------------------------------------------------
# Save
# --------------------------------------------------
OUTPUT_RESULTS.parent.mkdir(
    parents=True,
    exist_ok=True
)

results_df.to_csv(
    OUTPUT_RESULTS,
    index=False
)

assignments.to_csv(
    OUTPUT_ASSIGNMENTS,
    index=False
)

print("\nSaved:")
print(OUTPUT_RESULTS)
print(OUTPUT_ASSIGNMENTS)

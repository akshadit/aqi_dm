"""
K-Means Clustering Module for AirInsight
Groups multidimensional air pollution observations into clusters based on pollutant signatures.
Features: PM2.5, PM10, NO2, SO2, CO, O3.
Includes:
- Feature scaling with StandardScaler
- Elbow method inertia curve calculation
- Silhouette score evaluation
- 2D PCA projection for dimensional reduction and visualization
- Statistical profile extraction and dynamic cluster labeling based on measured levels
"""

from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from data.preprocessing import get_scaled_features
from config import POLLUTANT_FEATURES


def compute_elbow_curve(
    df: pd.DataFrame,
    features: List[str] = POLLUTANT_FEATURES,
    k_range: range = range(2, 10)
) -> Dict[str, Any]:
    """
    Computes WCSS (Within-Cluster Sum of Squares / Inertia) and Silhouette Scores
    for a range of k values to determine the optimal number of clusters.
    """
    valid_df = df[features].dropna()
    if len(valid_df) < max(k_range):
        return {"k_values": [], "inertias": [], "silhouette_scores": []}

    scaled_data, _ = get_scaled_features(valid_df, features)
    inertias = []
    sil_scores = []
    k_vals = list(k_range)

    for k in k_vals:
        km = KMeans(n_clusters=k, init="k-means++", n_init=10, random_state=42)
        km.fit(scaled_data)
        inertias.append(round(float(km.inertia_), 2))
        try:
            sil = silhouette_score(scaled_data, km.labels_)
            sil_scores.append(round(float(sil), 4))
        except Exception:
            sil_scores.append(0.0)

    return {
        "k_values": k_vals,
        "inertias": inertias,
        "silhouette_scores": sil_scores
    }


def perform_kmeans_clustering(
    df: pd.DataFrame,
    n_clusters: int = 4,
    features: List[str] = POLLUTANT_FEATURES
) -> Dict[str, Any]:
    """
    Executes K-Means clustering on the dataset.
    Returns:
        - Clustered DataFrame with 'cluster' label and PCA coordinates (pca_1, pca_2)
        - PCA explained variance
        - Cluster profiles (mean values per pollutant)
        - Interpretations derived from data (not hardcoded assumptions)
        - Silhouette score and Inertia
    """
    valid_df = df.copy()
    valid_df = valid_df.dropna(subset=features).reset_index(drop=True)

    if len(valid_df) < n_clusters:
        raise ValueError(f"Insufficient samples ({len(valid_df)}) for {n_clusters} clusters.")

    # 1. Scale features
    scaled_data, scaler = get_scaled_features(valid_df, features)

    # 2. Train K-Means
    kmeans = KMeans(n_clusters=n_clusters, init="k-means++", n_init=10, random_state=42)
    cluster_labels = kmeans.fit_predict(scaled_data)
    valid_df["cluster"] = cluster_labels

    # 3. Compute evaluation metrics
    inertia = float(kmeans.inertia_)
    try:
        sil_score = float(silhouette_score(scaled_data, cluster_labels))
    except Exception:
        sil_score = 0.0

    # 4. 2D PCA Projection for visualization
    pca = PCA(n_components=2, random_state=42)
    pca_coords = pca.fit_transform(scaled_data)
    valid_df["pca_1"] = pca_coords[:, 0]
    valid_df["pca_2"] = pca_coords[:, 1]
    explained_var = [round(float(v) * 100, 2) for v in pca.explained_variance_ratio_]

    # 5. Extract Cluster Statistical Profiles in original units
    profile_df = valid_df.groupby("cluster")[features].agg(["mean", "median", "std", "count"])
    
    # 6. Dynamic Interpretation of each cluster based on measured pollutant levels
    cluster_summaries = []
    overall_means = valid_df[features].mean()

    for c in range(n_clusters):
        c_data = valid_df[valid_df["cluster"] == c]
        c_means = c_data[features].mean()
        c_count = len(c_data)
        c_pct = round((c_count / len(valid_df)) * 100, 1)

        # Contrast with overall dataset mean
        elevated = []
        low = []
        for feat in features:
            if c_means[feat] > overall_means[feat] * 1.25:
                elevated.append(feat.upper().replace("_", "."))
            elif c_means[feat] < overall_means[feat] * 0.75:
                low.append(feat.upper().replace("_", "."))

        # Scientific naming based on measured signature
        if "PM2.5" in elevated and "PM10" in elevated:
            if "NO2" in elevated or "CO" in elevated:
                archetype = "Severe Combustion & Traffic Dust (Severe Industrial/Urban)"
            else:
                archetype = "Elevated Particulate Matter (Dust/Haze)"
        elif "O3" in elevated:
            archetype = "Photochemical Smog (Elevated Ozone)"
        elif not elevated:
            archetype = "Clean / Baseline Ambient Air"
        elif "NO2" in elevated or "CO" in elevated:
            archetype = "Vehicular Exhaust Dominant"
        else:
            archetype = "Moderate Mixed Urban Pollution"

        cluster_summaries.append({
            "cluster": c,
            "count": c_count,
            "percentage": c_pct,
            "archetype": archetype,
            "means": {k: round(float(v), 2) for k, v in c_means.items()},
            "elevated_pollutants": elevated if elevated else ["None (Near/Below Average)"],
            "low_pollutants": low if low else ["None"]
        })

    return {
        "df_clustered": valid_df,
        "kmeans_model": kmeans,
        "scaler": scaler,
        "inertia": round(inertia, 2),
        "silhouette_score": round(sil_score, 4),
        "explained_variance": explained_var,
        "cluster_summaries": cluster_summaries,
        "profile_df": profile_df
    }


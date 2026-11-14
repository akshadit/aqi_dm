"""
Page 4: K-Means Clustering Module
Discovers pollution archetype patterns across observations.
Includes:
- Dynamic cluster count selection
- Elbow method inertia analysis
- 2D PCA cluster projection
- Statistically driven cluster interpretations (No arbitrary assumptions)
"""

import streamlit as st
import pandas as pd
from data.dataset_manager import get_cleaned_dataset
from algorithms.clustering import compute_elbow_curve, perform_kmeans_clustering
from visualizations.charts import plot_elbow_curve, plot_pca_clusters
from database.db import save_mining_result
from config import POLLUTANT_FEATURES, POLLUTANT_DISPLAY_NAMES


def render_clustering_page():
    st.markdown("## 🔬 Algorithm 1: K-Means Pollution Pattern Clustering")
    st.markdown(
        "Groups multidimensional air pollution observations into clusters based on shared chemical signatures "
        "(PM2.5, PM10, NO₂, SO₂, CO, and O₃). Feature scaling via `StandardScaler` ensures distance balance."
    )

    cleaned_df, _ = get_cleaned_dataset()
    if cleaned_df.empty or len(cleaned_df) < 10:
        st.warning("Insufficient cleaned data available for clustering. Please fetch data first.")
        return

    # Parameters Controls
    col_k, col_act = st.columns([2, 1])
    with col_k:
        k_val = st.slider("Select Number of Clusters (k):", min_value=2, max_value=8, value=4, step=1)
    with col_act:
        st.write("")
        st.write("")
        run_elbow_btn = st.button("📈 Compute Elbow Curve")

    # Optional Elbow Analysis
    if run_elbow_btn or "elbow_data" in st.session_state:
        if run_elbow_btn:
            with st.spinner("Computing Within-Cluster Sum of Squares (Inertia) for k=2..9..."):
                elbow_res = compute_elbow_curve(cleaned_df, k_range=range(2, 10))
                st.session_state["elbow_data"] = elbow_res
        else:
            elbow_res = st.session_state["elbow_data"]

        if elbow_res.get("k_values"):
            fig_elbow = plot_elbow_curve(
                elbow_res["k_values"],
                elbow_res["inertias"],
                elbow_res["silhouette_scores"]
            )
            st.plotly_chart(fig_elbow, use_container_width=True)

    st.markdown("---")
    st.markdown(f"### 📍 Clustering Execution (k = {k_val})")

    try:
        results = perform_kmeans_clustering(cleaned_df, n_clusters=k_val)
        st.session_state["clustering_res"] = results

        # Save to database
        save_mining_result("K-Means", {
            "n_clusters": k_val,
            "inertia": results["inertia"],
            "silhouette_score": results["silhouette_score"],
            "cluster_summaries": results["cluster_summaries"]
        })

        # KPI Metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Clusters (k)", k_val)
        m2.metric("Inertia (WCSS)", f"{results['inertia']:,.1f}")
        m3.metric("Silhouette Score", f"{results['silhouette_score']:.4f}")
        m4.metric("PCA Explained Variance", f"{sum(results['explained_variance']):.1f}%")

        # 2D PCA Cluster Map
        st.markdown("#### 🗺️ 2D PCA Dimensionality Reduction Projection")
        fig_pca = plot_pca_clusters(results["df_clustered"], results["explained_variance"])
        st.plotly_chart(fig_pca, use_container_width=True)

        # Cluster Characteristics & Dynamic Scientific Interpretations
        st.markdown("---")
        st.markdown("### 🧬 Discovered Cluster Profiles & Interpretations")
        st.caption("Profiles are inferred strictly from empirical measurements, not pre-assigned labels.")

        for summ in results["cluster_summaries"]:
            c_id = summ["cluster"]
            archetype = summ["archetype"]
            count = summ["count"]
            pct = summ["percentage"]
            elevated = ", ".join(summ["elevated_pollutants"])

            with st.expander(f"**Cluster {c_id}:** {archetype} ({count} samples, {pct}%)", expanded=True):
                st.write(f"- **Key Elevated Markers:** `{elevated}`")
                
                # Mean values table
                means_df = pd.DataFrame([summ["means"]])
                means_df.columns = [POLLUTANT_DISPLAY_NAMES.get(c, c) for c in means_df.columns]
                st.dataframe(means_df, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Clustering error: {e}")


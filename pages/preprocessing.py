"""
Page 3: Data Preprocessing Pipeline Module
Displays before/after audit reports, missing value imputation, duplicate elimination,
and IQR outlier boundary detection and capping.
"""

import streamlit as st
import pandas as pd
from data.dataset_manager import get_raw_dataset
from data.preprocessing import run_preprocessing_pipeline
from config import POLLUTANT_FEATURES, POLLUTANT_DISPLAY_NAMES


def render_preprocessing_page():
    st.markdown("## 🧹 Data Preprocessing & Quality Engineering")
    st.markdown(
        "Standardizes raw atmospheric sensor streams into clean, scientifically validated "
        "matrices for machine learning and association discovery."
    )

    raw_df = get_raw_dataset(record_type="observed")
    if raw_df.empty:
        st.warning("No records found in database. Ingest records first in 'Live Data Explorer'.")
        return

    # Configuration Options
    col_opt1, col_opt2 = st.columns(2)
    with col_opt1:
        outlier_mode = st.selectbox(
            "Outlier Handling Technique (IQR 1.5 Standard):",
            options=["cap", "remove", "none"],
            format_func=lambda x: {
                "cap": "Cap to IQR Bounds (Winsorization - Recommended)",
                "remove": "Remove Outlier Rows",
                "none": "Keep Outliers Unaltered"
            }[x]
        )
    with col_opt2:
        st.write("")
        st.write("")
        run_prep_btn = st.button("⚡ Execute Preprocessing Pipeline", use_container_width=True)

    # Run preprocessing
    cleaned_df, report = run_preprocessing_pipeline(
        raw_df,
        features=POLLUTANT_FEATURES,
        handle_outliers_method=outlier_mode
    )
    st.session_state["cleaned_df"] = cleaned_df
    st.session_state["prep_report"] = report

    # Audit Metrics Row
    st.markdown("### 📋 Preprocessing Quality Audit Summary")
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.metric("Initial Collected Records", f"{report['initial_records']:,}")
    with kpi2:
        st.metric("Duplicates Eliminated", f"{report['duplicates_removed']:,}")
    with kpi3:
        total_outliers = sum(v["count"] for v in report["outliers_detected"].values())
        st.metric("Total Outliers Detected", f"{total_outliers:,}")
    with kpi4:
        st.metric("Final Usable Records", f"{report['final_records']:,}")

    # Missing Values & Outlier Analysis Tables
    st.markdown("---")
    st.markdown("### 🔍 Feature-Level Integrity Analysis")
    col_t1, col_t2 = st.columns(2)

    with col_t1:
        st.markdown("#### Missing Values Treatment")
        st.caption("Strategy: Time-series forward & backward propagation per city (Zero-imputation avoided).")
        missing_rows = []
        for feat in POLLUTANT_FEATURES:
            init_na = report["initial_missing_counts"].get(feat, 0)
            final_na = report["missing_after_imputation"].get(feat, 0)
            missing_rows.append({
                "Pollutant": POLLUTANT_DISPLAY_NAMES.get(feat, feat),
                "Initial Missing": init_na,
                "After Imputation": final_na
            })
        st.dataframe(pd.DataFrame(missing_rows), use_container_width=True, hide_index=True)

    with col_t2:
        st.markdown("#### IQR Outlier Detection Bounds")
        st.caption("Lower Bound: $Q1 - 1.5 \\times IQR$, Upper Bound: $Q3 + 1.5 \\times IQR$.")
        outlier_rows = []
        for feat, info in report["outliers_detected"].items():
            outlier_rows.append({
                "Feature": POLLUTANT_DISPLAY_NAMES.get(feat, feat),
                "Outliers Count": info["count"],
                "Lower Bound": info["lower_bound"],
                "Upper Bound": info["upper_bound"]
            })
        st.dataframe(pd.DataFrame(outlier_rows), use_container_width=True, hide_index=True)

    # Before & After Dataset Preview Tabs
    st.markdown("---")
    st.markdown("### 📊 Dataset Previews")
    tab_clean, tab_raw = st.tabs(["Cleaned & Validated Dataset", "Raw Unprocessed Dataset"])

    with tab_clean:
        st.dataframe(cleaned_df.head(50), use_container_width=True)
    with tab_raw:
        st.dataframe(raw_df.head(50), use_container_width=True)


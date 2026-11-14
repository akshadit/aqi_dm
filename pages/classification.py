"""
Page 5: Decision Tree Classification Module
Predicts EPA AQI categories from chemical pollutant concentrations.
Includes:
- Strict target leakage avoidance (AQI withheld from X)
- Hyperparameter tuning (depth, criterion)
- Comprehensive evaluation metrics (Accuracy, Precision, Recall, F1, Confusion Matrix)
- Interactive manual single-sample predictor
"""

import streamlit as st
import pandas as pd
from data.dataset_manager import get_cleaned_dataset
from algorithms.classification import (
    train_decision_tree_classifier,
    predict_single_sample,
    assign_aqi_category
)
from visualizations.charts import plot_confusion_matrix, plot_feature_importance, get_aqi_color
from database.db import save_mining_result
from config import POLLUTANT_FEATURES, POLLUTANT_DISPLAY_NAMES


def render_classification_page():
    st.markdown("## 🌲 Algorithm 2: Decision Tree Air Quality Classification")
    st.markdown(
        "Trains a supervised **Decision Tree Classifier** to classify atmospheric states into official "
        "US EPA health tiers (Good, Moderate, Sensitive, Unhealthy, Very Unhealthy, Hazardous)."
    )

    st.info(
        "🛡️ **Target Leakage Prevention Safeguard:** Continuous AQI is strictly excluded from the "
        "input feature matrix X. The classifier independently learns the non-linear decision boundaries "
        "and critical concentration thresholds that trigger higher pollution tiers."
    )

    cleaned_df, _ = get_cleaned_dataset()
    if cleaned_df.empty or len(cleaned_df) < 20:
        st.warning("Insufficient data available for classification. Ingest records first in 'Live Data Explorer'.")
        return

    # Hyperparameters Sidebar / Expander
    with st.expander("⚙️ Model Training Hyperparameters", expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            max_depth = st.slider("Max Tree Depth:", min_value=2, max_value=8, value=4, step=1)
        with c2:
            criterion = st.selectbox("Split Criterion:", ["gini", "entropy"])
        with c3:
            st.write("")
            st.write("")
            train_btn = st.button("🚀 Train Decision Tree", use_container_width=True)

    # Trigger training or reload session model
    if train_btn or "dt_results" not in st.session_state:
        with st.spinner("Training Decision Tree and evaluating on holdout test set..."):
            try:
                dt_res = train_decision_tree_classifier(
                    cleaned_df,
                    max_depth=max_depth,
                    criterion=criterion
                )
                st.session_state["dt_results"] = dt_res
                # Save to database
                save_mining_result("Decision Tree", {
                    "accuracy": dt_res["accuracy"],
                    "f1_score": dt_res["f1_score"],
                    "max_depth": max_depth,
                    "criterion": criterion
                })
            except Exception as e:
                st.error(f"Training failed: {e}")
                return

    dt_res = st.session_state["dt_results"]

    # Metrics Display
    st.markdown("### 🎯 Classification Performance on Test Split (20% Holdout)")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Overall Accuracy", f"{dt_res['accuracy']:.1f}%")
    k2.metric("Weighted Precision", f"{dt_res['precision']:.1f}%")
    k3.metric("Weighted Recall", f"{dt_res['recall']:.1f}%")
    k4.metric("Weighted F1-Score", f"{dt_res['f1_score']:.1f}%")

    col_cm, col_imp = st.columns(2)
    with col_cm:
        fig_cm = plot_confusion_matrix(dt_res["confusion_matrix"], dt_res["confusion_matrix_labels"])
        st.plotly_chart(fig_cm, use_container_width=True)

    with col_imp:
        fig_imp = plot_feature_importance(dt_res["feature_importances"])
        st.plotly_chart(fig_imp, use_container_width=True)

    # Decision Logic Rules Expander
    with st.expander("📜 Interpretable Decision Logic (Tree Splitting Rules)"):
        st.code(dt_res["tree_text"], language="text")

    # Interactive Live Sample Predictor
    st.markdown("---")
    st.markdown("### 🧪 Live AQI Category Simulator")
    st.markdown("Adjust individual pollutant concentrations below to observe real-time tree inference:")

    s1, s2, s3 = st.columns(3)
    with s1:
        sim_pm25 = st.slider("PM2.5 (µg/m³):", min_value=0.0, max_value=300.0, value=45.0, step=1.0)
        sim_pm10 = st.slider("PM10 (µg/m³):", min_value=0.0, max_value=400.0, value=85.0, step=1.0)
    with s2:
        sim_no2 = st.slider("NO₂ (µg/m³):", min_value=0.0, max_value=200.0, value=35.0, step=1.0)
        sim_so2 = st.slider("SO₂ (µg/m³):", min_value=0.0, max_value=150.0, value=15.0, step=1.0)
    with s3:
        sim_co = st.slider("CO (µg/m³):", min_value=0.0, max_value=10000.0, value=900.0, step=50.0)
        sim_o3 = st.slider("O₃ (µg/m³):", min_value=0.0, max_value=250.0, value=40.0, step=1.0)

    sample_dict = {
        "pm2_5": sim_pm25,
        "pm10": sim_pm10,
        "no2": sim_no2,
        "so2": sim_so2,
        "co": sim_co,
        "o3": sim_o3
    }

    predicted_cat, prob_dist = predict_single_sample(dt_res["model"], dt_res["features"], sample_dict)
    cat_color = get_aqi_color({"Good": 25, "Moderate": 75, "Unhealthy for Sensitive Groups": 125, "Unhealthy": 175, "Very Unhealthy": 250, "Hazardous": 350}.get(predicted_cat, 50))

    st.markdown(f"""
    <div style="background-color: white; padding: 18px; border-radius: 8px; border-left: 8px solid {cat_color}; margin-top: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
        <p style="margin: 0; color: #64748B; font-weight: 600; font-size: 0.9rem;">MODEL PREDICTED CLASSIFICATION</p>
        <h2 style="margin: 4px 0; color: {cat_color};">{predicted_cat}</h2>
        <p style="margin: 0; color: #334155; font-size: 0.9rem;">Class Probabilities: {', '.join([f'{k}: {v}%' for k, v in prob_dist.items() if v > 0])}</p>
    </div>
    """, unsafe_allow_html=True)


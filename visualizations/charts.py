"""
Data Visualization Module for AirInsight
Generates clean, publication-grade interactive Plotly charts adhering to
environmental analytics design standards:
- Modern typography
- Clean white/light aesthetic
- High-contrast accessible color scales
- Hover tooltips with units
"""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from config import AQI_CATEGORIES, POLLUTANT_DISPLAY_NAMES


def get_aqi_color(aqi_val: float) -> str:
    """Returns official hex color corresponding to an AQI value."""
    if pd.isna(aqi_val):
        return "#94A3B8"
    for cat in AQI_CATEGORIES:
        if cat["min"] <= aqi_val <= cat["max"]:
            return cat["color"]
    return "#881337"


def plot_city_comparison_bar(df_summary: pd.DataFrame) -> go.Figure:
    """
    Renders comparative bar chart of current AQI across cities with category colors.
    """
    colors = [get_aqi_color(val) for val in df_summary["us_aqi"]]
    fig = go.Figure(go.Bar(
        x=df_summary["city_name"],
        y=df_summary["us_aqi"],
        marker_color=colors,
        text=df_summary["us_aqi"].apply(lambda v: f"{int(v)}" if pd.notna(v) else "N/A"),
        textposition="outside"
    ))
    fig.update_layout(
        title="<b>Real-Time US AQI Comparison Across Cities</b>",
        xaxis_title="City",
        yaxis_title="US AQI Index",
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        margin=dict(l=40, r=40, t=50, b=40),
        yaxis=dict(gridcolor="#F1F5F9", range=[0, max(250, df_summary["us_aqi"].max() * 1.25)])
    )
    return fig


def plot_hourly_pollutants(df_city: pd.DataFrame, pollutant: str = "pm2_5") -> go.Figure:
    """
    Plots historical observations alongside forecasted values with clear demarcation.
    """
    df = df_city.copy().sort_values("timestamp")
    obs = df[df["record_type"] == "observed"]
    fc = df[df["record_type"] == "forecast"]

    disp_name = POLLUTANT_DISPLAY_NAMES.get(pollutant, pollutant.upper())
    fig = go.Figure()

    if not obs.empty:
        fig.add_trace(go.Scatter(
            x=obs["timestamp"],
            y=obs[pollutant],
            mode="lines",
            name="Observed (API)",
            line=dict(color="#0284C7", width=2.5)
        ))

    if not fc.empty:
        fig.add_trace(go.Scatter(
            x=fc["timestamp"],
            y=fc[pollutant],
            mode="lines",
            name="Forecast (Projected)",
            line=dict(color="#F97316", width=2.5, dash="dash")
        ))

    fig.update_layout(
        title=f"<b>Hourly Trajectory: {disp_name}</b>",
        xaxis_title="Timestamp (UTC)",
        yaxis_title=disp_name,
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        yaxis=dict(gridcolor="#F1F5F9")
    )
    return fig


def plot_elbow_curve(k_vals: List[int], inertias: List[float], sil_scores: List[float]) -> go.Figure:
    """
    Plots the Elbow Curve (Inertia vs k) with Silhouette scores.
    """
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=k_vals,
        y=inertias,
        mode="lines+markers",
        name="Inertia (WCSS)",
        line=dict(color="#0284C7", width=3),
        marker=dict(size=8, color="#0F172A")
    ))
    fig.update_layout(
        title="<b>Elbow Method for Optimal Clusters (k)</b>",
        xaxis_title="Number of Clusters (k)",
        yaxis_title="Within-Cluster Sum of Squares (Inertia)",
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        xaxis=dict(tickmode="linear", dtick=1),
        yaxis=dict(gridcolor="#F1F5F9")
    )
    return fig


def plot_pca_clusters(df_clustered: pd.DataFrame, explained_variance: List[float]) -> go.Figure:
    """
    Renders 2D PCA cluster projection scatter plot with explained variance ratios.
    """
    fig = px.scatter(
        df_clustered,
        x="pca_1",
        y="pca_2",
        color=df_clustered["cluster"].astype(str),
        hover_data=["city_name", "timestamp", "pm2_5", "pm10", "no2", "us_aqi"],
        labels={"cluster": "Cluster ID"},
        color_discrete_sequence=px.colors.qualitative.Bold
    )
    fig.update_layout(
        title=f"<b>K-Means 2D PCA Projection</b> (PCA-1: {explained_variance[0]}%, PCA-2: {explained_variance[1]}%)",
        xaxis_title="Principal Component 1",
        yaxis_title="Principal Component 2",
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        xaxis=dict(gridcolor="#F1F5F9"),
        yaxis=dict(gridcolor="#F1F5F9")
    )
    return fig


def plot_confusion_matrix(cm: List[List[int]], labels: List[str]) -> go.Figure:
    """
    Heatmap of confusion matrix for Decision Tree evaluation.
    """
    cm_arr = np.array(cm)
    fig = go.Figure(data=go.Heatmap(
        z=cm_arr,
        x=labels,
        y=labels,
        colorscale="Blues",
        text=cm_arr,
        texttemplate="%{text}",
        textfont={"size": 14}
    ))
    fig.update_layout(
        title="<b>Decision Tree Confusion Matrix</b>",
        xaxis_title="Predicted AQI Category",
        yaxis_title="Actual Ground Truth Category",
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF"
    )
    return fig


def plot_feature_importance(importances: Dict[str, float]) -> go.Figure:
    """
    Horizontal bar chart of Gini feature importances.
    """
    feats = list(importances.keys())
    scores = list(importances.values())
    fig = go.Figure(go.Bar(
        x=scores,
        y=[POLLUTANT_DISPLAY_NAMES.get(f, f.upper()) for f in feats],
        orientation="h",
        marker_color="#0284C7"
    ))
    fig.update_layout(
        title="<b>Decision Tree Feature Importance (Gini Metric)</b>",
        xaxis_title="Relative Importance Weight",
        yaxis_title="Pollutant Feature",
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        yaxis=dict(autorange="reversed"),
        xaxis=dict(gridcolor="#F1F5F9")
    )
    return fig


def plot_association_rules_scatter(rules_df: pd.DataFrame) -> go.Figure:
    """
    Scatter plot of discovered association rules: Support vs Confidence, colored by Lift.
    """
    if rules_df.empty:
        return go.Figure()

    fig = px.scatter(
        rules_df,
        x="support",
        y="confidence",
        size="lift",
        color="lift",
        hover_data=["antecedents_str", "consequents_str"],
        labels={"support": "Support", "confidence": "Confidence", "lift": "Lift"},
        color_continuous_scale="Viridis"
    )
    fig.update_layout(
        title="<b>Discovered Association Rules (Support vs Confidence, Size/Color: Lift)</b>",
        xaxis_title="Support",
        yaxis_title="Confidence",
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        xaxis=dict(gridcolor="#F1F5F9"),
        yaxis=dict(gridcolor="#F1F5F9")
    )
    return fig


def plot_regression_actual_vs_pred(hist_df: pd.DataFrame, future_df: pd.DataFrame, pollutant: str) -> go.Figure:
    """
    Plots actual historical observations, in-sample linear fit, and future trend extrapolation.
    """
    disp_name = POLLUTANT_DISPLAY_NAMES.get(pollutant, pollutant.upper())
    fig = go.Figure()

    # Actual Observations
    fig.add_trace(go.Scatter(
        x=hist_df["timestamp"],
        y=hist_df[pollutant],
        mode="markers",
        name="Actual Observations",
        marker=dict(color="#0F172A", size=5, opacity=0.6)
    ))

    # In-sample Fitted Trend Line
    fig.add_trace(go.Scatter(
        x=hist_df["timestamp"],
        y=hist_df["predicted"],
        mode="lines",
        name="OLS Regression Line (Fitted)",
        line=dict(color="#0284C7", width=2.5)
    ))

    # Out-of-sample Extrapolation Line
    fig.add_trace(go.Scatter(
        x=future_df["timestamp"],
        y=future_df["predicted_trend"],
        mode="lines",
        name="Future Extrapolated Trend",
        line=dict(color="#EF4444", width=2.5, dash="dot")
    ))

    fig.update_layout(
        title=f"<b>Linear Regression Trend Analysis: {disp_name}</b>",
        xaxis_title="Timestamp",
        yaxis_title=disp_name,
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        yaxis=dict(gridcolor="#F1F5F9")
    )
    return fig


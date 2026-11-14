"""
Page 1: Overview Module
Displays project executive summary, current AQI dashboard, pollutant cards,
and multi-city spatial comparison.
"""

import streamlit as st
import pandas as pd
from database.db import get_cities, get_records
from data.dataset_manager import get_raw_dataset
from visualizations.charts import plot_city_comparison_bar, get_aqi_color
from config import AQI_CATEGORIES, POLLUTANT_DISPLAY_NAMES


def render_overview_page():
    st.markdown("## 🌍 AirInsight: Overview & Live Pollution Index")
    st.markdown(
        "*A Data Mining, Environmental Pattern Discovery, and Air Quality Intelligence System.*"
    )

    # Load dataset
    raw_df = get_raw_dataset()
    cities = get_cities()

    if raw_df.empty or not cities:
        st.warning("No records currently loaded in database. Please navigate to 'Live Data Explorer' to fetch data.")
        return

    # Multi-City Summary Computation
    obs_df = raw_df[raw_df["record_type"] == "observed"]
    if obs_df.empty:
        obs_df = raw_df

    # Latest record per city
    latest_per_city = obs_df.sort_values("timestamp").groupby("city_id").last().reset_index()

    # Top KPI Bar: Multi-City Quick Glance
    st.markdown("### 📊 Real-Time Multi-City Comparison")
    fig_comp = plot_city_comparison_bar(latest_per_city)
    st.plotly_chart(fig_comp, use_container_width=True)

    # City Selector for Detailed View
    st.markdown("---")
    st.markdown("### 🏙️ Detailed City Snapshot")
    city_names = [c["city_name"] for c in cities]
    selected_city_name = st.selectbox("Select City for Detailed Breakdown:", city_names, index=0)

    selected_city = next(c for c in cities if c["city_name"] == selected_city_name)
    city_records = obs_df[obs_df["city_id"] == selected_city["id"]].sort_values("timestamp")

    if city_records.empty:
        st.info(f"No observed records available for {selected_city_name}.")
        return

    latest_row = city_records.iloc[-1]
    us_aqi_val = latest_row["us_aqi"] if pd.notna(latest_row["us_aqi"]) else 0.0

    # Determine AQI Tier
    aqi_tier = "Hazardous"
    aqi_color = "#881337"
    aqi_desc = "Health warning of emergency conditions."
    for cat in AQI_CATEGORIES:
        if cat["min"] <= us_aqi_val <= cat["max"]:
            aqi_tier = cat["label"]
            aqi_color = cat["color"]
            aqi_desc = cat["desc"]
            break

    # KPI Metric Cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div style="background-color: white; padding: 16px; border-radius: 8px; border-left: 6px solid {aqi_color}; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
            <p style="margin: 0; color: #64748B; font-size: 0.85rem; font-weight: 600;">US AQI</p>
            <h2 style="margin: 4px 0; color: {aqi_color};">{int(us_aqi_val)}</h2>
            <p style="margin: 0; color: #0F172A; font-weight: 600; font-size: 0.95rem;">{aqi_tier}</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        pm25_val = latest_row.get("pm2_5", 0.0)
        st.metric(label="PM2.5 (Fine Particulates)", value=f"{pm25_val:.1f} µg/m³")

    with col3:
        pm10_val = latest_row.get("pm10", 0.0)
        st.metric(label="PM10 (Coarse Particulates)", value=f"{pm10_val:.1f} µg/m³")

    with col4:
        ts_val = latest_row.get("timestamp", "N/A")
        st.metric(label="Last Recorded (UTC)", value=str(ts_val).replace("T", " "))

    # Additional Pollutants Row
    st.markdown("#### Supplementary Atmospheric Pollutants")
    pcol1, pcol2, pcol3, pcol4 = st.columns(4)
    with pcol1:
        st.metric(label="Nitrogen Dioxide (NO₂)", value=f"{latest_row.get('no2', 0.0):.1f} µg/m³")
    with pcol2:
        st.metric(label="Sulphur Dioxide (SO₂)", value=f"{latest_row.get('so2', 0.0):.1f} µg/m³")
    with pcol3:
        st.metric(label="Carbon Monoxide (CO)", value=f"{latest_row.get('co', 0.0):.1f} µg/m³")
    with pcol4:
        st.metric(label="Ozone (O₃)", value=f"{latest_row.get('o3', 0.0):.1f} µg/m³")

    # Advisory Note
    st.info(f"**Health Advisory ({aqi_tier}):** {aqi_desc}")


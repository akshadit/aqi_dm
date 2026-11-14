"""
Page 2: Live Data Explorer Module
Enables fetching live and forecast data via Open-Meteo API, dynamic location discovery
via Open-Meteo Geocoding API, and temporal sequence visualization.
"""

import streamlit as st
import pandas as pd
from database.db import get_cities, add_city, get_records
from api.geocoding_api import search_city
from data.collector import collect_city_data, collect_all_cities_data
from visualizations.charts import plot_hourly_pollutants
from config import POLLUTANT_FEATURES, POLLUTANT_DISPLAY_NAMES


def render_live_data_page():
    st.markdown("## 📡 Live Air Quality Data Explorer & API Ingestion")
    st.markdown(
        "Directly interfaces with the **Open-Meteo Atmospheric Air Quality API** to acquire "
        "continuous hourly measurements and 3-day projected forecasts."
    )

    cities = get_cities()
    city_names = [c["city_name"] for c in cities]

    # Action Row: City Selection and Ingestion Buttons
    col_sel, col_btn1, col_btn2 = st.columns([2, 1.2, 1.2])
    with col_sel:
        selected_city_name = st.selectbox("Select Target City:", city_names, index=0)
    with col_btn1:
        st.write("")
        st.write("")
        fetch_single_btn = st.button("🔄 Fetch Live for City", use_container_width=True)
    with col_btn2:
        st.write("")
        st.write("")
        fetch_all_btn = st.button("🌐 Ingest All Cities", use_container_width=True)

    selected_city = next(c for c in cities if c["city_name"] == selected_city_name)

    # Ingestion Actions
    if fetch_single_btn:
        with st.spinner(f"Querying Open-Meteo API for {selected_city_name}..."):
            res = collect_city_data(selected_city["id"], past_days=14, forecast_days=3)
            if res.get("success"):
                cached_tag = " (from Cache)" if res.get("is_cached") else ""
                st.success(f"Successfully processed {res['fetched_count']} records for {selected_city_name}{cached_tag}.")
            else:
                st.error(f"API Fetch Error: {res.get('error')}")

    if fetch_all_btn:
        with st.spinner("Ingesting data for all registered cities..."):
            all_res = collect_all_cities_data(past_days=14, forecast_days=3)
            success_count = sum(1 for r in all_res if r.get("success"))
            st.success(f"Batch Ingestion Complete: {success_count}/{len(all_res)} cities updated successfully.")

    # Location Expansion Expander (Add New City)
    with st.expander("➕ Discover and Register New City (Open-Meteo Geocoding)"):
        search_query = st.text_input("Enter City Name to Search:", placeholder="e.g. Pune, Jaipur, London")
        if st.button("🔍 Search Geocoding API"):
            if search_query.strip():
                with st.spinner("Resolving coordinates..."):
                    candidates = search_city(search_query)
                    if candidates:
                        st.session_state["geo_candidates"] = candidates
                    else:
                        st.warning("No coordinates resolved for query. Verify spelling or connectivity.")

        if "geo_candidates" in st.session_state and st.session_state["geo_candidates"]:
            cand = st.session_state["geo_candidates"][0]
            st.write(f"**Found:** {cand['name']}, {cand.get('admin1', '')} ({cand['country']}) — Lat: {cand['latitude']:.4f}, Lon: {cand['longitude']:.4f}")
            if st.button(f"Add '{cand['name']}' to Database"):
                new_id = add_city(cand["name"], cand["latitude"], cand["longitude"], cand["country"])
                st.success(f"Added {cand['name']} (ID: {new_id}). Refreshing list...")
                st.rerun()

    # Load City Records
    city_records = get_records(city_id=selected_city["id"], as_df=True)
    if city_records.empty:
        st.info(f"No records available for {selected_city_name}. Click 'Fetch Live for City' to initialize.")
        return

    st.markdown("---")
    st.markdown(f"### 📈 Atmospheric Time-Series: **{selected_city_name}**")

    # Pollutant Selector
    selected_pollutant = st.selectbox(
        "Select Pollutant to Visualize:",
        options=POLLUTANT_FEATURES + ["us_aqi", "dust"],
        format_func=lambda x: POLLUTANT_DISPLAY_NAMES.get(x, x.upper())
    )

    fig_time = plot_hourly_pollutants(city_records, pollutant=selected_pollutant)
    st.plotly_chart(fig_time, use_container_width=True)

    # Data Source & Provenance Details
    with st.expander("ℹ️ Data Provenance & Telemetry Metadata"):
        obs_count = len(city_records[city_records["record_type"] == "observed"])
        fc_count = len(city_records[city_records["record_type"] == "forecast"])
        st.write(f"- **Primary Ingestion Provider:** Open-Meteo Air Quality API (`Copernicus Atmosphere CAMS & ECMWF`)")
        st.write(f"- **Target Coordinates:** Latitude {selected_city['latitude']:.4f}, Longitude {selected_city['longitude']:.4f}")
        st.write(f"- **Recorded Observations:** {obs_count} hourly samples")
        st.write(f"- **Forward Projections (Forecast):** {fc_count} hourly projected samples")
        st.write(f"- **Timestamp Standard:** Coordinated Universal Time (UTC)")


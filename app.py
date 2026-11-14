"""
AirInsight: API-Based Air Quality Data Mining, Pollution Pattern Analysis and Prediction System
Main Application Entry Point (Streamlit Multi-Page Coordinator)
"""

import streamlit as st
from pathlib import Path
from database.db import init_db, get_database_stats
from data.collector import seed_baseline_data_if_empty
from config import UI_THEME

# Page configuration
st.set_page_config(
    page_title="AirInsight | Air Quality Data Mining",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Environmental Analytics Theme)
st.markdown(f"""
<style>
    /* Main Background and Fonts */
    .stApp {{
        background-color: {UI_THEME['bg_color']};
        color: {UI_THEME['text_dark']};
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }}
    
    /* Header Styling */
    h1, h2, h3, h4 {{
        color: {UI_THEME['text_dark']};
        font-weight: 700;
        letter-spacing: -0.02em;
    }}
    
    /* Cards and Containers */
    div[data-testid="stMetric"] {{
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 14px 18px;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
    }}
    div[data-testid="stMetricLabel"] {{
        color: {UI_THEME['text_muted']};
        font-size: 0.85rem;
        font-weight: 600;
    }}
    div[data-testid="stMetricValue"] {{
        color: {UI_THEME['text_dark']};
        font-weight: 700;
    }}
    
    /* Buttons */
    .stButton>button {{
        background-color: {UI_THEME['primary']};
        color: #FFFFFF;
        border-radius: 6px;
        border: none;
        padding: 8px 16px;
        font-weight: 600;
        transition: background-color 0.15s ease-in-out;
    }}
    .stButton>button:hover {{
        background-color: #0369A1;
        color: #FFFFFF;
    }}
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {{
        background-color: #FFFFFF;
        border-right: 1px solid #E2E8F0;
    }}
    
    /* Clean up excess padding */
    .block-container {{
        padding-top: 2rem;
        padding-bottom: 3rem;
    }}
</style>
""", unsafe_allow_html=True)


# Initialize Database and Seed Baseline Data if First Run
@st.cache_resource
def bootstrap_system():
    init_db()
    seed_baseline_data_if_empty()
    return True

bootstrap_system()

# Sidebar Navigation
st.sidebar.markdown("""
<div style="padding: 10px 0 20px 0; border-bottom: 1px solid #E2E8F0; margin-bottom: 15px;">
    <h2 style="margin: 0; color: #0284C7; font-size: 1.5rem; display: flex; align-items: center; gap: 8px;">
        🌍 AirInsight
    </h2>
    <p style="margin: 4px 0 0 0; color: #64748B; font-size: 0.85rem; font-weight: 500;">
        Data Mining & Pollution Intelligence
    </p>
</div>
""", unsafe_allow_html=True)

nav_selection = st.sidebar.radio(
    "Navigation Modules:",
    options=[
        "1. Overview & Snapshot",
        "2. Live Data Explorer",
        "3. Data Preprocessing",
        "4. K-Means Clustering",
        "5. Decision Tree Classification",
        "6. Association Rule Mining",
        "7. Trend Analysis",
        "8. Dataset & Reports"
    ],
    index=0
)

# Sidebar System Telemetry
st.sidebar.markdown("---")
stats = get_database_stats()
st.sidebar.markdown(f"""
<div style="font-size: 0.8rem; color: #64748B; line-height: 1.6;">
    <p style="margin: 0; font-weight: 600; color: #334155;">SYSTEM STATUS</p>
    • Database: <b>SQLite Active</b><br>
    • Monitored Cities: <b>{stats['cities_count']}</b><br>
    • Stored Records: <b>{stats['total_records']:,}</b><br>
    • API Source: <b>Open-Meteo</b>
</div>
""", unsafe_allow_html=True)

# Import and Render Respective Pages
if nav_selection == "1. Overview & Snapshot":
    from pages.overview import render_overview_page
    render_overview_page()

elif nav_selection == "2. Live Data Explorer":
    from pages.live_data import render_live_data_page
    render_live_data_page()

elif nav_selection == "3. Data Preprocessing":
    from pages.preprocessing import render_preprocessing_page
    render_preprocessing_page()

elif nav_selection == "4. K-Means Clustering":
    from pages.clustering import render_clustering_page
    render_clustering_page()

elif nav_selection == "5. Decision Tree Classification":
    from pages.classification import render_classification_page
    render_classification_page()

elif nav_selection == "6. Association Rule Mining":
    from pages.association import render_association_page
    render_association_page()

elif nav_selection == "7. Trend Analysis":
    from pages.trends import render_trends_page
    render_trends_page()

elif nav_selection == "8. Dataset & Reports":
    from pages.reports import render_reports_page
    render_reports_page()


"""
AirInsight Configuration Module
Defines project settings, API endpoints, initial cities, AQI standards, and UI constants.
"""

from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "database" / "airinsight.db"
CACHE_DIR = BASE_DIR / "data" / "cache"
REPORTS_DIR = BASE_DIR / "data" / "reports"

# Ensure directories exist
DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# API Endpoints
OPEN_METEO_AQ_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
OPEN_METEO_GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
OPENAQ_URL = "https://api.openaq.org/v2/latest"

API_TIMEOUT = 12  # seconds
API_MAX_RETRIES = 3
API_BACKOFF_FACTOR = 1.5

# Initial Demonstration Cities
DEFAULT_CITIES = [
    {"name": "Bengaluru", "latitude": 12.9716, "longitude": 77.5946, "country": "India"},
    {"name": "Delhi", "latitude": 28.6139, "longitude": 77.2090, "country": "India"},
    {"name": "Mumbai", "latitude": 19.0760, "longitude": 72.8777, "country": "India"},
    {"name": "Chennai", "latitude": 13.0827, "longitude": 80.2707, "country": "India"},
    {"name": "Hyderabad", "latitude": 17.3850, "longitude": 78.4867, "country": "India"},
    {"name": "Kolkata", "latitude": 22.5726, "longitude": 88.3639, "country": "India"},
]

# Core Features for Mining
POLLUTANT_FEATURES = ["pm2_5", "pm10", "no2", "so2", "co", "o3"]
POLLUTANT_DISPLAY_NAMES = {
    "pm2_5": "PM2.5 (µg/m³)",
    "pm10": "PM10 (µg/m³)",
    "no2": "NO₂ (µg/m³)",
    "so2": "SO₂ (µg/m³)",
    "co": "CO (µg/m³)",
    "o3": "O₃ (µg/m³)",
    "us_aqi": "US AQI",
    "european_aqi": "European AQI",
}

# US EPA Standard AQI Categories and Breakpoints
AQI_CATEGORIES = [
    {"label": "Good", "min": 0, "max": 50, "color": "#10B981", "desc": "Air quality is satisfactory."},
    {"label": "Moderate", "min": 51, "max": 100, "color": "#FBBF24", "desc": "Acceptable air quality."},
    {"label": "Unhealthy for Sensitive Groups", "min": 101, "max": 150, "color": "#F97316", "desc": "Sensitive groups may experience health effects."},
    {"label": "Unhealthy", "min": 151, "max": 200, "color": "#EF4444", "desc": "Everyone may begin to experience health effects."},
    {"label": "Very Unhealthy", "min": 201, "max": 300, "color": "#8B5CF6", "desc": "Health warnings of emergency conditions."},
    {"label": "Hazardous", "min": 301, "max": 500, "color": "#881337", "desc": "Health alert: serious health effects for everyone."},
]

# Discretization Thresholds for Association Rule Mining (Low, Medium, High)
# Based on WHO & CPCB air quality benchmark guidelines
BIN_THRESHOLDS = {
    "pm2_5": [0, 30, 60, 1000],
    "pm10": [0, 50, 100, 1000],
    "no2": [0, 40, 80, 1000],
    "co": [0, 1000, 2000, 50000],
    "so2": [0, 20, 50, 1000],
    "o3": [0, 50, 100, 1000],
}
BIN_LABELS = ["Low", "Medium", "High"]

# UI Palette - Environmental Analytics
UI_THEME = {
    "bg_color": "#F8FAFC",
    "sidebar_bg": "#0F172A",
    "card_bg": "#FFFFFF",
    "text_dark": "#0F172A",
    "text_muted": "#475569",
    "primary": "#0284C7",   # Blue
    "secondary": "#059669", # Green
    "accent": "#6366F1",
    "border": "#E2E8F0"
}


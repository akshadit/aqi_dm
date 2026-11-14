"""
Air Quality API Integration Module
Fetches real-world air pollution metrics from Open-Meteo Air Quality API.
Handles rate limits, retries, caching, and distinguishes observed vs forecast records.
"""

import os
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
import requests
from config import OPEN_METEO_AQ_URL, API_TIMEOUT, API_MAX_RETRIES, API_BACKOFF_FACTOR, CACHE_DIR


def _get_cache_key(latitude: float, longitude: float, past_days: int, forecast_days: int) -> Path:
    """Generates file path for caching query responses."""
    lat_str = f"{latitude:.2f}".replace(".", "_")
    lon_str = f"{longitude:.2f}".replace(".", "_")
    filename = f"aq_{lat_str}_{lon_str}_{past_days}p_{forecast_days}f.json"
    return CACHE_DIR / filename


def fetch_air_quality(
    latitude: float,
    longitude: float,
    past_days: int = 14,
    forecast_days: int = 3,
    use_cache: bool = True
) -> Dict[str, Any]:
    """
    Fetches hourly pollutant metrics from Open-Meteo API.
    Returns parsed dictionary of pollutant time series.
    """
    cache_file = _get_cache_key(latitude, longitude, past_days, forecast_days)
    
    # Check cache (valid for 1 hour)
    if use_cache and cache_file.exists():
        file_age = time.time() - cache_file.stat().st_mtime
        if file_age < 3600:  # 1 hour cache
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": [
            "pm10",
            "pm2_5",
            "carbon_monoxide",
            "nitrogen_dioxide",
            "sulphur_dioxide",
            "ozone",
            "dust",
            "european_aqi",
            "us_aqi"
        ],
        "past_days": past_days,
        "forecast_days": forecast_days,
        "timezone": "UTC"
    }

    last_error = None
    for attempt in range(API_MAX_RETRIES):
        try:
            response = requests.get(
                OPEN_METEO_AQ_URL,
                params=params,
                timeout=API_TIMEOUT
            )
            response.raise_for_status()
            data = response.json()
            
            # Cache successful response
            try:
                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(data, f)
            except Exception:
                pass
                
            return data
        except (requests.RequestException, ValueError) as e:
            last_error = e
            time.sleep(API_BACKOFF_FACTOR ** attempt)

    # If API fails but stale cache exists, serve stale cache
    if cache_file.exists():
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cached_data = json.load(f)
                cached_data["_cached_fallback"] = True
                return cached_data
        except Exception:
            pass

    raise ConnectionError(f"Failed to fetch air quality data after {API_MAX_RETRIES} attempts: {last_error}")


def transform_api_response_to_records(
    api_data: Dict[str, Any],
    city_id: int,
    data_source: str = "Open-Meteo"
) -> List[Dict[str, Any]]:
    """
    Parses Open-Meteo hourly response into standardized dictionary records suitable
    for SQLite insertion and DataFrame conversion.
    Clearly tags 'observed' vs 'forecast' based on current UTC time.
    """
    if "hourly" not in api_data:
        return []

    hourly = api_data["hourly"]
    timestamps = hourly.get("time", [])
    now_utc_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M")

    records = []
    num_entries = len(timestamps)

    for i in range(num_entries):
        ts = timestamps[i]
        record_type = "observed" if ts <= now_utc_str else "forecast"

        rec = {
            "city_id": city_id,
            "timestamp": ts,
            "pm2_5": hourly.get("pm2_5", [None])[i],
            "pm10": hourly.get("pm10", [None])[i],
            "co": hourly.get("carbon_monoxide", [None])[i],
            "no2": hourly.get("nitrogen_dioxide", [None])[i],
            "so2": hourly.get("sulphur_dioxide", [None])[i],
            "o3": hourly.get("ozone", [None])[i],
            "dust": hourly.get("dust", [None])[i],
            "european_aqi": hourly.get("european_aqi", [None])[i],
            "us_aqi": hourly.get("us_aqi", [None])[i],
            "data_source": data_source,
            "record_type": record_type
        }
        records.append(rec)

    return records


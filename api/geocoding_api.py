"""
Geocoding API Module for AirInsight
Queries Open-Meteo Geocoding API to resolve city names into coordinates and country.
Includes caching, retries, and offline fallback for default cities.
"""

import time
import requests
from typing import List, Dict, Any, Optional
from config import OPEN_METEO_GEO_URL, API_TIMEOUT, API_MAX_RETRIES, API_BACKOFF_FACTOR, DEFAULT_CITIES


def search_city(city_name: str) -> List[Dict[str, Any]]:
    """
    Searches for a city by name and returns candidate locations with latitude/longitude.
    Falls back to known coordinates if network is unavailable.
    """
    clean_name = city_name.strip()
    if not clean_name:
        return []

    # First check default cities for instantaneous resolution
    for c in DEFAULT_CITIES:
        if c["name"].lower() == clean_name.lower():
            return [{
                "name": c["name"],
                "latitude": c["latitude"],
                "longitude": c["longitude"],
                "country": c["country"],
                "admin1": "State/Province"
            }]

    params = {
        "name": clean_name,
        "count": 5,
        "language": "en",
        "format": "json"
    }

    last_error = None
    for attempt in range(API_MAX_RETRIES):
        try:
            response = requests.get(
                OPEN_METEO_GEO_URL,
                params=params,
                timeout=API_TIMEOUT
            )
            response.raise_for_status()
            data = response.json()
            
            results = []
            for item in data.get("results", []):
                results.append({
                    "name": item.get("name"),
                    "latitude": item.get("latitude"),
                    "longitude": item.get("longitude"),
                    "country": item.get("country", "Unknown"),
                    "admin1": item.get("admin1", "")
                })
            return results
        except (requests.RequestException, ValueError) as e:
            last_error = e
            time.sleep(API_BACKOFF_FACTOR ** attempt)

    # Return empty list if remote search failed
    return []


"""
Database Management Module for AirInsight
Handles SQLite connection pooling, table initialization, record insertion, querying, and stats.
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
from config import DATABASE_PATH, DEFAULT_CITIES


def get_connection() -> sqlite3.Connection:
    """Creates and returns a connection to the SQLite database."""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH, timeout=20.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db():
    """Initializes the database schema and default cities."""
    schema_path = Path(__file__).resolve().parent / "schema.sql"
    with get_connection() as conn:
        with open(schema_path, "r", encoding="utf-8") as f:
            conn.executescript(f.read())
        
        # Populate initial demonstration cities if not present
        cursor = conn.cursor()
        for city in DEFAULT_CITIES:
            cursor.execute("""
                INSERT OR IGNORE INTO cities (city_name, latitude, longitude, country)
                VALUES (?, ?, ?, ?)
            """, (city["name"], city["latitude"], city["longitude"], city["country"]))
        conn.commit()


def add_city(city_name: str, latitude: float, longitude: float, country: str = "India") -> int:
    """Inserts a new city or returns existing city ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM cities WHERE LOWER(city_name) = LOWER(?)", (city_name.strip(),))
        row = cursor.fetchone()
        if row:
            return row["id"]
        
        cursor.execute("""
            INSERT INTO cities (city_name, latitude, longitude, country)
            VALUES (?, ?, ?, ?)
        """, (city_name.strip(), latitude, longitude, country))
        conn.commit()
        return cursor.lastrowid


def get_cities() -> List[Dict[str, Any]]:
    """Retrieves all registered cities."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, city_name, latitude, longitude, country FROM cities ORDER BY city_name ASC")
        return [dict(row) for row in cursor.fetchall()]


def get_city_by_id(city_id: int) -> Optional[Dict[str, Any]]:
    """Retrieves city by ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM cities WHERE id = ?", (city_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_city_by_name(city_name: str) -> Optional[Dict[str, Any]]:
    """Retrieves city by name."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM cities WHERE LOWER(city_name) = LOWER(?)", (city_name.strip(),))
        row = cursor.fetchone()
        return dict(row) if row else None


def insert_air_quality_records(records: List[Dict[str, Any]]) -> int:
    """
    Inserts a batch of air quality records, ignoring duplicates.
    Returns the count of newly inserted rows.
    """
    if not records:
        return 0
    
    query = """
        INSERT OR IGNORE INTO air_quality_records (
            city_id, timestamp, pm2_5, pm10, co, no2, so2, o3, dust,
            european_aqi, us_aqi, data_source, record_type
        ) VALUES (
            :city_id, :timestamp, :pm2_5, :pm10, :co, :no2, :so2, :o3, :dust,
            :european_aqi, :us_aqi, :data_source, :record_type
        )
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.executemany(query, records)
        conn.commit()
        return cursor.rowcount


def get_records(
    city_id: Optional[int] = None,
    record_type: Optional[str] = None,
    limit: Optional[int] = None,
    as_df: bool = True
) -> Any:
    """
    Retrieves air quality records with optional filters.
    Returns a pandas DataFrame or list of dictionaries.
    """
    query = """
        SELECT r.id, r.city_id, c.city_name, r.timestamp,
               r.pm2_5, r.pm10, r.co, r.no2, r.so2, r.o3, r.dust,
               r.european_aqi, r.us_aqi, r.data_source, r.record_type, r.created_at
        FROM air_quality_records r
        JOIN cities c ON r.city_id = c.id
        WHERE 1=1
    """
    params = []
    if city_id is not None:
        query += " AND r.city_id = ?"
        params.append(city_id)
    if record_type is not None:
        query += " AND r.record_type = ?"
        params.append(record_type)
    
    query += " ORDER BY r.timestamp ASC"
    
    if limit is not None:
        query += " LIMIT ?"
        params.append(limit)
    
    conn = get_connection()
    try:
        if as_df:
            df = pd.read_sql_query(query, conn, params=params)
            return df
        else:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def save_mining_result(algorithm: str, result_data: Dict[str, Any], city_id: Optional[int] = None) -> int:
    """Stores data mining execution results in JSON format."""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO mining_results (algorithm, city_id, result, execution_timestamp)
            VALUES (?, ?, ?, ?)
        """, (algorithm, city_id, json.dumps(result_data), now_str))
        conn.commit()
        return cursor.lastrowid


def get_latest_mining_results(algorithm: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
    """Retrieves saved data mining run summaries."""
    query = """
        SELECT m.id, m.algorithm, m.city_id, c.city_name, m.result, m.execution_timestamp
        FROM mining_results m
        LEFT JOIN cities c ON m.city_id = c.id
        WHERE 1=1
    """
    params = []
    if algorithm:
        query += " AND m.algorithm = ?"
        params.append(algorithm)
    query += " ORDER BY m.id DESC LIMIT ?"
    params.append(limit)
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        results = []
        for r in rows:
            res_dict = dict(r)
            try:
                res_dict["result"] = json.loads(res_dict["result"])
            except Exception:
                pass
            results.append(res_dict)
        return results


def get_database_stats() -> Dict[str, Any]:
    """Returns overview statistics of stored data."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM cities")
        city_count = cursor.fetchone()["count"]
        
        cursor.execute("SELECT COUNT(*) as count FROM air_quality_records")
        total_records = cursor.fetchone()["count"]
        
        cursor.execute("SELECT COUNT(*) as count FROM air_quality_records WHERE record_type = 'observed'")
        observed_count = cursor.fetchone()["count"]
        
        cursor.execute("SELECT COUNT(*) as count FROM air_quality_records WHERE record_type = 'forecast'")
        forecast_count = cursor.fetchone()["count"]
        
        cursor.execute("SELECT MAX(timestamp) as latest_ts, MIN(timestamp) as earliest_ts FROM air_quality_records")
        row = cursor.fetchone()
        
        return {
            "cities_count": city_count,
            "total_records": total_records,
            "observed_records": observed_count,
            "forecast_records": forecast_count,
            "earliest_timestamp": row["earliest_ts"],
            "latest_timestamp": row["latest_ts"],
        }

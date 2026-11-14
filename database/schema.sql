-- AirInsight SQLite Schema Definition

CREATE TABLE IF NOT EXISTS cities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    city_name TEXT NOT NULL UNIQUE,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    country TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS air_quality_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    city_id INTEGER NOT NULL,
    timestamp TEXT NOT NULL,
    pm2_5 REAL,
    pm10 REAL,
    co REAL,
    no2 REAL,
    so2 REAL,
    o3 REAL,
    dust REAL,
    european_aqi REAL,
    us_aqi REAL,
    data_source TEXT NOT NULL,
    record_type TEXT NOT NULL, -- 'observed' or 'forecast'
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(city_id) REFERENCES cities(id) ON DELETE CASCADE,
    UNIQUE(city_id, timestamp, record_type, data_source)
);

CREATE INDEX IF NOT EXISTS idx_records_city_time 
ON air_quality_records(city_id, timestamp);

CREATE INDEX IF NOT EXISTS idx_records_type 
ON air_quality_records(record_type);

CREATE TABLE IF NOT EXISTS mining_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    algorithm TEXT NOT NULL,
    city_id INTEGER,
    result TEXT NOT NULL, -- JSON serialized metrics, parameters & findings
    execution_timestamp TEXT NOT NULL,
    FOREIGN KEY(city_id) REFERENCES cities(id) ON DELETE SET NULL
);


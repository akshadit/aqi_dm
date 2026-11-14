"""
Dataset Manager Module for AirInsight
Orchestrates loading raw data from the database, executing the preprocessing pipeline,
caching cleaned datasets, and exporting datasets and audit logs as CSV.
"""

from typing import Optional, Tuple, Dict, Any
import pandas as pd
from database.db import get_records, init_db
from data.collector import seed_baseline_data_if_empty
from data.preprocessing import run_preprocessing_pipeline
from config import POLLUTANT_FEATURES


def get_raw_dataset(city_id: Optional[int] = None, record_type: Optional[str] = "observed") -> pd.DataFrame:
    """
    Loads raw records from SQLite. Ensures DB is initialized and seeded if empty.
    """
    init_db()
    df = get_records(city_id=city_id, record_type=record_type, as_df=True)
    if df.empty:
        seed_baseline_data_if_empty()
        df = get_records(city_id=city_id, record_type=record_type, as_df=True)
    return df


def get_cleaned_dataset(
    city_id: Optional[int] = None,
    record_type: Optional[str] = "observed",
    handle_outliers_method: str = "cap"
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Retrieves records and runs the complete preprocessing pipeline.
    Returns (cleaned_df, preprocessing_report).
    """
    raw_df = get_raw_dataset(city_id=city_id, record_type=record_type)
    cleaned_df, report = run_preprocessing_pipeline(
        raw_df,
        features=POLLUTANT_FEATURES,
        handle_outliers_method=handle_outliers_method
    )
    return cleaned_df, report


def export_dataframe_to_csv(df: pd.DataFrame) -> bytes:
    """Encodes a DataFrame into UTF-8 CSV bytes for Streamlit download buttons."""
    return df.to_csv(index=False).encode("utf-8")


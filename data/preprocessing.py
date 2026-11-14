"""
Data Preprocessing Pipeline Module for AirInsight
Implements:
- Data validation and type coercion
- Duplicate detection and removal
- Missing value analysis and time-series-aware imputation (no zero-replacement)
- IQR-based outlier detection and capping/flagging
- StandardScaler feature normalization
- Comprehensive before/after preprocessing audit report
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple, List, Optional
from sklearn.preprocessing import StandardScaler
from config import POLLUTANT_FEATURES


def validate_and_format_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensures timestamps are datetime objects and pollutant fields are numeric.
    """
    df = df.copy()
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df = df.sort_values(by=["city_id", "timestamp"]).reset_index(drop=True)

    numeric_cols = [c for c in POLLUTANT_FEATURES if c in df.columns] + ["us_aqi", "european_aqi", "dust"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def detect_outliers_iqr(series: pd.Series) -> Tuple[pd.Series, float, float, int]:
    """
    Identifies outliers using the 1.5 * IQR standard rule:
    IQR = Q3 - Q1
    Lower Bound = Q1 - 1.5 * IQR
    Upper Bound = Q3 + 1.5 * IQR
    Returns (outlier_mask, lower_bound, upper_bound, count).
    """
    clean_series = series.dropna()
    if len(clean_series) < 4:
        return pd.Series(False, index=series.index), 0.0, 0.0, 0

    q1 = clean_series.quantile(0.25)
    q3 = clean_series.quantile(0.75)
    iqr = q3 - q1
    lower_bound = max(0.0, q1 - 1.5 * iqr)  # Pollutant concentrations cannot be negative
    upper_bound = q3 + 1.5 * iqr

    outlier_mask = (series < lower_bound) | (series > upper_bound)
    outlier_count = int(outlier_mask.sum())
    return outlier_mask, lower_bound, upper_bound, outlier_count


def run_preprocessing_pipeline(
    df: pd.DataFrame,
    features: Optional[List[str]] = None,
    handle_outliers_method: str = "cap"  # "cap", "remove", or "none"
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Executes the complete preprocessing pipeline on raw records.
    Returns:
        cleaned_df: Cleaned and prepared DataFrame
        report: Dictionary containing step-by-step audit statistics
    """
    if features is None:
        features = [f for f in POLLUTANT_FEATURES if f in df.columns]

    initial_count = len(df)
    report = {
        "initial_records": initial_count,
        "initial_missing_counts": {},
        "duplicates_removed": 0,
        "outliers_detected": {},
        "missing_after_imputation": {},
        "final_records": 0,
        "features_processed": features
    }

    if df.empty:
        report["final_records"] = 0
        return df, report

    # Step 1: Type conversion and sorting
    working_df = validate_and_format_dataframe(df)

    # Step 2: Record missing values before cleaning
    for col in features + ["us_aqi"]:
        if col in working_df.columns:
            report["initial_missing_counts"][col] = int(working_df[col].isna().sum())

    # Step 3: Duplicate removal based on city and timestamp
    subset_cols = ["city_id", "timestamp", "record_type"] if "city_id" in working_df.columns else ["timestamp"]
    before_dedup = len(working_df)
    working_df = working_df.drop_duplicates(subset=subset_cols, keep="last").reset_index(drop=True)
    report["duplicates_removed"] = before_dedup - len(working_df)

    # Step 4: Missing value handling using forward-fill + backward-fill per city
    # (Avoid replacing missing pollutant levels with 0, as 0 means pure air which is scientifically invalid)
    if "city_id" in working_df.columns:
        for col in features:
            if col in working_df.columns:
                working_df[col] = (
                    working_df.groupby("city_id")[col]
                    .transform(lambda s: s.ffill().bfill())
                )
                # If still NaN for a city (entire column was empty), fill with global feature median
                if working_df[col].isna().any():
                    median_val = working_df[col].median()
                    working_df[col] = working_df[col].fillna(median_val if not pd.isna(median_val) else 0.0)
    else:
        for col in features:
            if col in working_df.columns:
                working_df[col] = working_df[col].ffill().bfill().fillna(working_df[col].median())

    # Check remaining missing
    for col in features:
        if col in working_df.columns:
            report["missing_after_imputation"][col] = int(working_df[col].isna().sum())

    # Step 5: IQR Outlier Detection
    combined_outlier_mask = pd.Series(False, index=working_df.index)
    for col in features:
        if col in working_df.columns:
            mask, lb, ub, count = detect_outliers_iqr(working_df[col])
            report["outliers_detected"][col] = {
                "count": count,
                "lower_bound": round(lb, 2),
                "upper_bound": round(ub, 2)
            }
            if handle_outliers_method == "cap":
                # Winsorization / Capping to upper/lower bound
                working_df[col] = working_df[col].clip(lower=lb, upper=ub)
            elif handle_outliers_method == "remove":
                combined_outlier_mask = combined_outlier_mask | mask

    if handle_outliers_method == "remove" and combined_outlier_mask.any():
        working_df = working_df[~combined_outlier_mask].reset_index(drop=True)

    report["final_records"] = len(working_df)
    return working_df, report


def get_scaled_features(
    df: pd.DataFrame,
    feature_cols: List[str]
) -> Tuple[np.ndarray, StandardScaler]:
    """
    Standardizes features using StandardScaler (zero mean, unit variance).
    Formula: z = (x - u) / s
    Returns scaled numpy array and the fitted scaler.
    """
    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(df[feature_cols])
    return scaled_data, scaler


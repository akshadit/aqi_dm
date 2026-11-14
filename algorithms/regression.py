"""
Linear Regression Trend Analysis Module for AirInsight
Analyzes historical pollutant concentration trajectories over time.
Models trend dynamics using Ordinary Least Squares (OLS) Linear Regression:
    y = b0 + b1 * t
Evaluates predictive performance via MAE, RMSE, and R² Score.

ACADEMIC CAVEAT:
Explicitly distinguishes statistical trend extrapolation from meteorological forecasting.
Weather parameters (wind speed, humidity, temperature inversion, boundary layer height)
govern atmospheric dispersion; linear trend captures baseline trajectory direction.
"""

from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


def analyze_pollutant_trend(
    df: pd.DataFrame,
    target_pollutant: str = "pm2_5",
    forecast_hours: int = 24
) -> Dict[str, Any]:
    """
    Fits a linear regression model on chronological time-series observations
    to evaluate directional trend (slope) and extrapolate baseline short-term trajectory.
    """
    valid_df = df.copy()
    if "timestamp" not in valid_df.columns or target_pollutant not in valid_df.columns:
        raise ValueError(f"DataFrame must contain 'timestamp' and '{target_pollutant}' columns.")

    valid_df["timestamp"] = pd.to_datetime(valid_df["timestamp"], errors="coerce")
    valid_df = valid_df.dropna(subset=["timestamp", target_pollutant]).sort_values("timestamp").reset_index(drop=True)

    if len(valid_df) < 10:
        raise ValueError(f"Insufficient data points ({len(valid_df)}) for reliable trend regression.")

    # Convert timestamps to numeric time index (hours elapsed from start)
    start_time = valid_df["timestamp"].iloc[0]
    valid_df["hours_elapsed"] = (valid_df["timestamp"] - start_time).dt.total_seconds() / 3600.0

    X = valid_df[["hours_elapsed"]].values
    y = valid_df[target_pollutant].values

    # Train / Test split using chronological order (80% train, 20% test)
    split_idx = int(len(valid_df) * 0.8)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]

    model = LinearRegression()
    model.fit(X_train, y_train)

    # In-sample & Out-of-sample predictions
    y_pred_train = model.predict(X_train)
    y_pred_test = model.predict(X_test)
    y_pred_all = model.predict(X)

    valid_df["predicted"] = y_pred_all
    valid_df["residual"] = y - y_pred_all

    # Performance Metrics on Test Set
    mae = float(mean_absolute_error(y_test, y_pred_test))
    mse = float(mean_squared_error(y_test, y_pred_test))
    rmse = float(np.sqrt(mse))
    r2 = float(r2_score(y_test, y_pred_test))

    slope = float(model.coef_[0])  # Change in concentration per hour
    intercept = float(model.intercept_)
    change_per_day = slope * 24.0

    # Trend Direction Interpretation
    if abs(change_per_day) < 0.5:
        trend_status = "Stable / Plateau"
        trend_desc = f"Concentrations remain relatively steady with minimal drift ({change_per_day:+.2f} µg/m³ per day)."
    elif change_per_day > 0:
        trend_status = "Upward / Deteriorating"
        trend_desc = f"Pollution shows an escalating trend, accumulating at {change_per_day:+.2f} µg/m³ per day."
    else:
        trend_status = "Downward / Improving"
        trend_desc = f"Pollution levels are declining at a rate of {change_per_day:+.2f} µg/m³ per day."

    # Extrapolate future short-term trend line
    last_hour = valid_df["hours_elapsed"].iloc[-1]
    future_hours = np.array([[last_hour + h] for h in range(1, forecast_hours + 1)])
    future_timestamps = [valid_df["timestamp"].iloc[-1] + pd.Timedelta(hours=h) for h in range(1, forecast_hours + 1)]
    future_preds = np.maximum(0.0, model.predict(future_hours))  # Pollution cannot be negative

    future_df = pd.DataFrame({
        "timestamp": future_timestamps,
        "hours_elapsed": future_hours.flatten(),
        "predicted_trend": future_preds,
        "record_type": "trend_extrapolation"
    })

    return {
        "model": model,
        "target_pollutant": target_pollutant,
        "slope_per_hour": round(slope, 4),
        "change_per_day": round(change_per_day, 2),
        "intercept": round(intercept, 2),
        "trend_status": trend_status,
        "trend_desc": trend_desc,
        "mae": round(mae, 2),
        "rmse": round(rmse, 2),
        "r2_score": round(r2, 4),
        "historical_df": valid_df,
        "future_df": future_df,
        "train_samples": len(X_train),
        "test_samples": len(X_test)
    }


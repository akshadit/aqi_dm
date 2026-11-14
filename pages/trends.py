"""
Page 7: Linear Regression Trend Analysis Module
Models historical pollutant concentration trajectories and evaluates short-term trends.
Includes:
- City and pollutant selection
- Ordinary Least Squares regression fitting
- Evaluation metrics: MAE, RMSE, and R² Score
- Actual vs Predicted overlay with future extrapolation line
- Academic distinction between statistical trend extrapolation and physical forecasting
"""

import streamlit as st
import pandas as pd
from database.db import get_cities, get_records, save_mining_result
from algorithms.regression import analyze_pollutant_trend
from visualizations.charts import plot_regression_actual_vs_pred
from config import POLLUTANT_FEATURES, POLLUTANT_DISPLAY_NAMES


def render_trends_page():
    st.markdown("## 📈 Algorithm 4: Linear Regression Trend Analysis")
    st.markdown(
        "Analyzes historical time-series observations to estimate the direction and rate of change (slope) "
        "of atmospheric pollutants using **Ordinary Least Squares (OLS) Linear Regression**."
    )

    st.warning(
        "⚠️ **Academic Methodological Distinction:** Linear regression provides statistical trend "
        "extrapolation based on historical trajectory. It does not replace numerical meteorological dispersion "
        "models (which account for boundary layer mixing, humidity, and wind vectors). Results represent baseline drift."
    )

    cities = get_cities()
    city_names = [c["city_name"] for c in cities]

    # City & Pollutant Selection
    c1, c2, c3 = st.columns([1.5, 1.5, 1])
    with c1:
        selected_city_name = st.selectbox("Select City for Trend Analysis:", city_names, index=0)
    with c2:
        selected_pollutant = st.selectbox(
            "Select Target Pollutant:",
            options=POLLUTANT_FEATURES + ["us_aqi"],
            format_func=lambda x: POLLUTANT_DISPLAY_NAMES.get(x, x.upper())
        )
    with c3:
        forecast_hours = st.slider("Extrapolation Horizon (Hours):", min_value=12, max_value=72, value=24, step=12)

    selected_city = next(c for c in cities if c["city_name"] == selected_city_name)
    df_city = get_records(city_id=selected_city["id"], record_type="observed", as_df=True)

    if df_city.empty or len(df_city) < 10:
        st.info(f"Insufficient historical observed records for {selected_city_name}. Please ingest live data first.")
        return

    try:
        trend_res = analyze_pollutant_trend(
            df_city,
            target_pollutant=selected_pollutant,
            forecast_hours=forecast_hours
        )
        st.session_state["trend_res"] = trend_res

        # Save to database
        save_mining_result("Linear Regression", {
            "city": selected_city_name,
            "pollutant": selected_pollutant,
            "slope": trend_res["slope_per_hour"],
            "mae": trend_res["mae"],
            "rmse": trend_res["rmse"],
            "r2_score": trend_res["r2_score"]
        }, city_id=selected_city["id"])

        # Display Metrics
        st.markdown(f"### 🎯 Evaluation & Trend Dynamics ({selected_city_name} - {POLLUTANT_DISPLAY_NAMES.get(selected_pollutant, selected_pollutant)})")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Trajectory Status", trend_res["trend_status"])
        m2.metric("Drift Rate", f"{trend_res['change_per_day']:+.2f} units/day")
        m3.metric("Mean Absolute Error (MAE)", f"{trend_res['mae']:.2f}")
        m4.metric("Root Mean Sq Error (RMSE)", f"{trend_res['rmse']:.2f}")

        # Scientific Narrative Box
        st.info(f"**Interpretation:** {trend_res['trend_desc']} (Coefficient of Determination $R^2 = {trend_res['r2_score']:.4f}$ on holdout 20% test slice).")

        # Regression Plot
        st.markdown("#### 📉 Fitted Trend & Future Extrapolation")
        fig_reg = plot_regression_actual_vs_pred(
            trend_res["historical_df"],
            trend_res["future_df"],
            pollutant=selected_pollutant
        )
        st.plotly_chart(fig_reg, use_container_width=True)

        # Tabular View of Extrapolations
        with st.expander("📋 View Extrapolated Values Table"):
            st.dataframe(trend_res["future_df"][["timestamp", "predicted_trend"]], use_container_width=True)

    except Exception as e:
        st.error(f"Trend analysis error: {e}")


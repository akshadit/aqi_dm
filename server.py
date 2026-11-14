"""
AirInsight Modern Web API Server (FastAPI)
Exposes RESTful endpoints for the modern web frontend dashboard:
- Telemetry & Overview
- API Ingestion & Dynamic Geocoding
- Preprocessing Audit
- 4 Data Mining Algorithms (K-Means, Decision Tree, Apriori, Linear Regression)
- Interactive Predictions & CSV Exports
- Serves the frontend web client static assets
"""

import io
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, Query, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from database.db import (
    init_db, get_cities, add_city, get_city_by_id, get_records,
    get_database_stats, get_latest_mining_results, save_mining_result
)
from data.collector import collect_city_data, collect_all_cities_data, seed_baseline_data_if_empty
from data.dataset_manager import get_raw_dataset, get_cleaned_dataset, export_dataframe_to_csv
from data.preprocessing import run_preprocessing_pipeline
from algorithms.clustering import compute_elbow_curve, perform_kmeans_clustering
from algorithms.classification import train_decision_tree_classifier, predict_single_sample
from algorithms.association_rules import mine_association_rules
from algorithms.regression import analyze_pollutant_trend
from visualizations.reports import generate_academic_project_report
from api.geocoding_api import search_city
from config import POLLUTANT_FEATURES, AQI_CATEGORIES

# Initialize Database
init_db()
seed_baseline_data_if_empty()

app = FastAPI(
    title="AirInsight API",
    description="REST API for Air Quality Data Mining, Pattern Discovery, and Machine Learning",
    version="2.0.0"
)

# Enable CORS for external or local web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request Models
class AddCityRequest(BaseModel):
    name: str
    latitude: float
    longitude: float
    country: str = "India"

class KMeansRequest(BaseModel):
    k: int = 4

class DecisionTreeRequest(BaseModel):
    max_depth: int = 4
    criterion: str = "gini"

class PredictSampleRequest(BaseModel):
    pm2_5: float
    pm10: float
    no2: float
    so2: float
    co: float
    o3: float

class AprioriRequest(BaseModel):
    min_support: float = 0.10
    min_confidence: float = 0.50
    min_lift: float = 1.0

class RegressionRequest(BaseModel):
    city_id: int
    pollutant: str = "pm2_5"
    forecast_hours: int = 24


# In-memory model cache for fast interactive inference
DT_CACHE = {"model": None, "features": None, "classes": None}


# --- REST API Endpoints ---

@app.get("/api/stats")
def api_stats():
    """Returns database telemetry and count statistics."""
    return get_database_stats()


@app.get("/api/cities")
def api_get_cities():
    """Retrieves all registered cities."""
    return get_cities()


@app.get("/api/geocoding/search")
def api_search_city(q: str = Query(..., min_length=2)):
    """Queries Open-Meteo Geocoding API to resolve coordinates."""
    results = search_city(q)
    return results


@app.post("/api/cities")
def api_add_city(req: AddCityRequest):
    """Registers a new city in the database."""
    city_id = add_city(req.name, req.latitude, req.longitude, req.country)
    return {"success": True, "city_id": city_id, "name": req.name}


@app.get("/api/overview")
def api_overview():
    """Returns multi-city snapshot, latest readings, and AQI rankings."""
    raw_df = get_raw_dataset(record_type="observed")
    if raw_df.empty:
        return {"cities_summary": [], "latest_records": []}

    latest_per_city = raw_df.sort_values("timestamp").groupby("city_id").last().reset_index()
    cities_summary = []
    for _, row in latest_per_city.iterrows():
        us_aqi = row["us_aqi"] if row["us_aqi"] is not None else 0
        tier = "Good"
        color = "#10B981"
        for cat in AQI_CATEGORIES:
            if cat["min"] <= us_aqi <= cat["max"]:
                tier = cat["label"]
                color = cat["color"]
                break

        cities_summary.append({
            "city_id": int(row["city_id"]),
            "city_name": str(row["city_name"]),
            "us_aqi": round(float(us_aqi), 1),
            "tier": tier,
            "color": color,
            "pm2_5": round(float(row.get("pm2_5") or 0), 1),
            "pm10": round(float(row.get("pm10") or 0), 1),
            "no2": round(float(row.get("no2") or 0), 1),
            "so2": round(float(row.get("so2") or 0), 1),
            "co": round(float(row.get("co") or 0), 1),
            "o3": round(float(row.get("o3") or 0), 1),
            "timestamp": str(row["timestamp"])
        })

    # Sort descending by AQI (most polluted first)
    cities_summary.sort(key=lambda x: x["us_aqi"], reverse=True)
    return {"cities_summary": cities_summary}


@app.get("/api/hourly/{city_id}")
def api_hourly(city_id: int, pollutant: str = "pm2_5"):
    """Returns chronological observed vs forecasted measurements for charts."""
    df = get_records(city_id=city_id, as_df=True)
    if df.empty or pollutant not in df.columns:
        return {"observed": [], "forecast": []}

    obs = df[df["record_type"] == "observed"].sort_values("timestamp")
    fc = df[df["record_type"] == "forecast"].sort_values("timestamp")

    return {
        "pollutant": pollutant,
        "observed": [{"time": str(t), "value": round(float(v), 2) if v is not None else None} for t, v in zip(obs["timestamp"], obs[pollutant])],
        "forecast": [{"time": str(t), "value": round(float(v), 2) if v is not None else None} for t, v in zip(fc["timestamp"], fc[pollutant])],
    }


@app.post("/api/ingest/city/{city_id}")
def api_ingest_city(city_id: int):
    """Triggers live API collection for a single city."""
    res = collect_city_data(city_id, past_days=14, forecast_days=3)
    return res


@app.post("/api/ingest/all")
def api_ingest_all():
    """Triggers live API collection for all registered cities."""
    res = collect_all_cities_data(past_days=14, forecast_days=3)
    return {"results": res}


@app.get("/api/preprocessing")
def api_preprocessing():
    """Returns preprocessing step-by-step audit diagnostics and data samples."""
    raw_df = get_raw_dataset(record_type="observed")
    cleaned_df, report = run_preprocessing_pipeline(raw_df, handle_outliers_method="cap")
    
    # Format sample preview rows
    sample_rows = cleaned_df.head(20).to_dict(orient="records")
    for r in sample_rows:
        r["timestamp"] = str(r["timestamp"])

    return {
        "report": report,
        "sample_preview": sample_rows
    }


@app.post("/api/mining/kmeans")
def api_kmeans(req: KMeansRequest):
    """Executes K-Means clustering and returns 2D PCA projection coordinates."""
    cleaned_df, _ = get_cleaned_dataset()
    if len(cleaned_df) < req.k:
        raise HTTPException(status_code=400, detail="Insufficient samples for clustering.")

    elbow_data = compute_elbow_curve(cleaned_df, k_range=range(2, 9))
    results = perform_kmeans_clustering(cleaned_df, n_clusters=req.k)

    save_mining_result("K-Means", {
        "n_clusters": req.k,
        "inertia": results["inertia"],
        "silhouette_score": results["silhouette_score"],
        "cluster_summaries": results["cluster_summaries"]
    })

    # Sample PCA points for scatter plot
    pca_df = results["df_clustered"][["city_name", "timestamp", "cluster", "pca_1", "pca_2", "pm2_5", "pm10", "us_aqi"]].head(300)
    pca_points = []
    for _, row in pca_df.iterrows():
        pca_points.append({
            "city": row["city_name"],
            "time": str(row["timestamp"]),
            "cluster": int(row["cluster"]),
            "x": round(float(row["pca_1"]), 3),
            "y": round(float(row["pca_2"]), 3),
            "pm2_5": round(float(row["pm2_5"]), 1),
            "pm10": round(float(row["pm10"]), 1),
            "us_aqi": round(float(row["us_aqi"]), 1)
        })

    return {
        "k": req.k,
        "inertia": results["inertia"],
        "silhouette_score": results["silhouette_score"],
        "explained_variance": results["explained_variance"],
        "cluster_summaries": results["cluster_summaries"],
        "elbow": elbow_data,
        "pca_points": pca_points
    }


@app.post("/api/mining/decision-tree")
def api_decision_tree(req: DecisionTreeRequest):
    """Trains Decision Tree Classifier without target leakage."""
    cleaned_df, _ = get_cleaned_dataset()
    res = train_decision_tree_classifier(cleaned_df, max_depth=req.max_depth, criterion=req.criterion)

    # Cache for live prediction simulator
    DT_CACHE["model"] = res["model"]
    DT_CACHE["features"] = res["features"]
    DT_CACHE["classes"] = res["classes"]

    save_mining_result("Decision Tree", {
        "accuracy": res["accuracy"],
        "f1_score": res["f1_score"],
        "max_depth": req.max_depth
    })

    return {
        "accuracy": res["accuracy"],
        "precision": res["precision"],
        "recall": res["recall"],
        "f1_score": res["f1_score"],
        "confusion_matrix": res["confusion_matrix"],
        "confusion_matrix_labels": res["confusion_matrix_labels"],
        "feature_importances": res["feature_importances"],
        "tree_text": res["tree_text"],
        "train_size": res["train_size"],
        "test_size": res["test_size"]
    }


@app.post("/api/mining/predict-sample")
def api_predict_sample(req: PredictSampleRequest):
    """Simulates real-time Decision Tree inference from user slider inputs."""
    if DT_CACHE["model"] is None:
        cleaned_df, _ = get_cleaned_dataset()
        res = train_decision_tree_classifier(cleaned_df, max_depth=4)
        DT_CACHE["model"] = res["model"]
        DT_CACHE["features"] = res["features"]
        DT_CACHE["classes"] = res["classes"]

    sample_dict = req.model_dump()
    pred_cat, probs = predict_single_sample(DT_CACHE["model"], DT_CACHE["features"], sample_dict)
    
    # Find color
    color = "#10B981"
    for cat in AQI_CATEGORIES:
        if cat["label"] == pred_cat:
            color = cat["color"]
            break

    return {
        "predicted_category": pred_cat,
        "color": color,
        "probabilities": probs
    }


@app.post("/api/mining/apriori")
def api_apriori(req: AprioriRequest):
    """Discovers inter-pollutant association rules using Apriori."""
    cleaned_df, _ = get_cleaned_dataset()
    res = mine_association_rules(
        cleaned_df,
        min_support=req.min_support,
        min_confidence=req.min_confidence,
        min_lift=req.min_lift
    )

    rules_list = []
    if not res["rules_df"].empty:
        for _, r in res["rules_df"].head(25).iterrows():
            rules_list.append({
                "antecedents": r["antecedents_str"],
                "consequents": r["consequents_str"],
                "support": round(float(r["support"]) * 100, 1),
                "confidence": round(float(r["confidence"]) * 100, 1),
                "lift": round(float(r["lift"]), 2)
            })

    save_mining_result("Apriori Association", {
        "rules_found": len(rules_list),
        "min_support": req.min_support,
        "min_confidence": req.min_confidence
    })

    return {
        "total_rules": res["summary"]["total_rules"],
        "rules": rules_list,
        "explanations": res["rule_explanations"]
    }


@app.post("/api/mining/regression")
def api_regression(req: RegressionRequest):
    """Fits Linear Regression trend model and extrapolates short-term trajectory."""
    df_city = get_records(city_id=req.city_id, record_type="observed", as_df=True)
    if df_city.empty or len(df_city) < 10:
        raise HTTPException(status_code=400, detail="Insufficient records for trend analysis.")

    trend_res = analyze_pollutant_trend(df_city, target_pollutant=req.pollutant, forecast_hours=req.forecast_hours)

    save_mining_result("Linear Regression", {
        "city_id": req.city_id,
        "pollutant": req.pollutant,
        "slope": trend_res["slope_per_hour"],
        "mae": trend_res["mae"],
        "rmse": trend_res["rmse"]
    }, city_id=req.city_id)

    # Format points for charting
    hist_points = []
    for _, r in trend_res["historical_df"].tail(100).iterrows():
        hist_points.append({
            "time": str(r["timestamp"]),
            "actual": round(float(r[req.pollutant]), 2),
            "fitted": round(float(r["predicted"]), 2)
        })

    future_points = []
    for _, r in trend_res["future_df"].iterrows():
        future_points.append({
            "time": str(r["timestamp"]),
            "predicted": round(float(r["predicted_trend"]), 2)
        })

    return {
        "pollutant": req.pollutant,
        "slope_per_hour": trend_res["slope_per_hour"],
        "change_per_day": trend_res["change_per_day"],
        "trend_status": trend_res["trend_status"],
        "trend_desc": trend_res["trend_desc"],
        "mae": trend_res["mae"],
        "rmse": trend_res["rmse"],
        "r2_score": trend_res["r2_score"],
        "history": hist_points,
        "extrapolation": future_points
    }


@app.get("/api/export/raw-csv")
def api_export_raw_csv():
    """Streams the raw database records as a downloadable CSV."""
    df = get_raw_dataset(record_type=None)
    csv_bytes = export_dataframe_to_csv(df)
    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=airinsight_raw_records.csv"}
    )


@app.get("/api/export/cleaned-csv")
def api_export_cleaned_csv():
    """Streams the cleaned and imputed dataset as a downloadable CSV."""
    df, _ = get_cleaned_dataset()
    csv_bytes = export_dataframe_to_csv(df)
    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=airinsight_cleaned_dataset.csv"}
    )


@app.get("/api/report")
def api_generate_report():
    """Generates the full academic experimental laboratory report."""
    db_stats = get_database_stats()
    _, prep_report = get_cleaned_dataset()
    report_text = generate_academic_project_report(db_stats=db_stats, prep_report=prep_report)
    return {"report": report_text}


# Mount Static Frontend
frontend_path = Path(__file__).resolve().parent / "frontend"
frontend_path.mkdir(parents=True, exist_ok=True)
app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")


if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    uvicorn.run("server:app", host=host, port=port)

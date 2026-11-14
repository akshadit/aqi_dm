"""
Reports Generation Module for AirInsight
Generates comprehensive academic data mining summary reports.
"""

from datetime import datetime
from typing import Dict, Any, Optional
import pandas as pd
from database.db import get_database_stats


def generate_academic_project_report(
    db_stats: Dict[str, Any],
    prep_report: Optional[Dict[str, Any]] = None,
    clustering_res: Optional[Dict[str, Any]] = None,
    dt_res: Optional[Dict[str, Any]] = None,
    association_res: Optional[Dict[str, Any]] = None,
    trend_res: Optional[Dict[str, Any]] = None
) -> str:
    """
    Compiles an academic laboratory report summarizing data collection,
    preprocessing steps, and experimental outcomes from all 4 algorithms.
    """
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    report_lines = [
        "=" * 80,
        "AIRINSIGHT: DATA MINING AND AIR QUALITY PREDICTION SYSTEM",
        "ACADEMIC EXPERIMENTAL EXECUTION REPORT",
        f"Generated At: {now_str}",
        "=" * 80,
        "",
        "1. DATA COLLECTION & STORAGE SUMMARY",
        f"  * Total Monitored Cities: {db_stats.get('cities_count', 0)}",
        f"  * Total Stored Records: {db_stats.get('total_records', 0)}",
        f"  * Observed Records: {db_stats.get('observed_records', 0)}",
        f"  * Forecast Records: {db_stats.get('forecast_records', 0)}",
        f"  * Temporal Range: {db_stats.get('earliest_timestamp', 'N/A')} to {db_stats.get('latest_timestamp', 'N/A')}",
        "",
        "2. DATA PREPROCESSING AUDIT"
    ]

    if prep_report:
        report_lines.extend([
            f"  * Initial Records Processed: {prep_report.get('initial_records', 0)}",
            f"  * Duplicate Records Removed: {prep_report.get('duplicates_removed', 0)}",
            f"  * Usable Cleaned Records: {prep_report.get('final_records', 0)}",
            "  * Outliers Detected (IQR Standard 1.5):"
        ])
        for feat, out_info in prep_report.get("outliers_detected", {}).items():
            report_lines.append(f"      - {feat}: {out_info.get('count', 0)} outliers (Capped at [{out_info.get('lower_bound')}, {out_info.get('upper_bound')}])")
    else:
        report_lines.append("  * Preprocessing report not yet computed in current session.")

    report_lines.extend([
        "",
        "3. K-MEANS CLUSTERING RESULTS"
    ])
    if clustering_res:
        report_lines.extend([
            f"  * Optimal Clusters (k): {len(clustering_res.get('cluster_summaries', []))}",
            f"  * Inertia (WCSS): {clustering_res.get('inertia')}",
            f"  * Silhouette Score: {clustering_res.get('silhouette_score')}",
            f"  * PCA Explained Variance: {clustering_res.get('explained_variance')}%",
            "  * Identified Cluster Archetypes:"
        ])
        for summ in clustering_res.get("cluster_summaries", []):
            report_lines.append(f"      - Cluster {summ['cluster']} ({summ['percentage']}%): {summ['archetype']}")
    else:
        report_lines.append("  * K-Means clustering has not been run yet.")

    report_lines.extend([
        "",
        "4. DECISION TREE CLASSIFICATION RESULTS"
    ])
    if dt_res:
        report_lines.extend([
            f"  * Target Variable: EPA AQI Categorical Tier (Leakage-Free)",
            f"  * Classification Accuracy: {dt_res.get('accuracy')}%",
            f"  * Weighted Precision: {dt_res.get('precision')}%",
            f"  * Weighted Recall: {dt_res.get('recall')}%",
            f"  * Weighted F1-Score: {dt_res.get('f1_score')}%",
            f"  * Train/Test Samples: {dt_res.get('train_size')} / {dt_res.get('test_size')}",
            "  * Top Contributing Pollutants (Gini Importance):"
        ])
        for feat, imp in list(dt_res.get("feature_importances", {}).items())[:3]:
            report_lines.append(f"      - {feat}: {imp}")
    else:
        report_lines.append("  * Decision Tree classifier has not been trained yet.")

    report_lines.extend([
        "",
        "5. APRIORI ASSOCIATION RULE MINING"
    ])
    if association_res and not association_res.get("rules_df", pd.DataFrame()).empty:
        summary = association_res.get("summary", {})
        report_lines.extend([
            f"  * Discovered Rules Count: {summary.get('total_rules', 0)}",
            f"  * Min Support Threshold: {summary.get('min_support')}",
            f"  * Min Confidence Threshold: {summary.get('min_confidence')}",
            f"  * Min Lift Filter: {summary.get('min_lift')}",
            "  * Key Discovered Inter-Pollutant Rules:"
        ])
        for exp in association_res.get("rule_explanations", [])[:5]:
            clean_exp = exp.replace("**", "").replace("`", "")
            report_lines.append(f"      - {clean_exp}")
    else:
        report_lines.append("  * Association rule mining has not generated rules yet.")

    report_lines.extend([
        "",
        "6. LINEAR REGRESSION TREND ANALYSIS"
    ])
    if trend_res:
        report_lines.extend([
            f"  * Analyzed Pollutant: {trend_res.get('target_pollutant', 'pm2_5').upper()}",
            f"  * Trajectory Status: {trend_res.get('trend_status')}",
            f"  * Rate of Drift: {trend_res.get('change_per_day')} units/day",
            f"  * Model Fit (R² Score): {trend_res.get('r2_score')}",
            f"  * Mean Absolute Error (MAE): {trend_res.get('mae')}",
            f"  * Root Mean Squared Error (RMSE): {trend_res.get('rmse')}",
            f"  * Scientific Note: {trend_res.get('trend_desc')}"
        ])
    else:
        report_lines.append("  * Trend regression has not been evaluated yet.")

    report_lines.extend([
        "",
        "=" * 80,
        "END OF REPORT - AIRINSIGHT DATA MINING PLATFORM",
        "=" * 80
    ])

    return "\n".join(report_lines)


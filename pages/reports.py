"""
Page 8: Dataset & Reports Module
Enables downloading datasets in CSV format, querying mining execution logs,
and exporting a comprehensive Academic Experimental Project Report.
"""

import streamlit as st
import pandas as pd
import json
from database.db import get_database_stats, get_latest_mining_results, get_records
from data.dataset_manager import get_raw_dataset, get_cleaned_dataset, export_dataframe_to_csv
from visualizations.reports import generate_academic_project_report


def render_reports_page():
    st.markdown("## 📑 Dataset Exports & Academic Laboratory Reports")
    st.markdown(
        "Download primary sensor datasets, query stored algorithm runs from SQLite, and generate "
        "comprehensive project documentation for academic defense and evaluation."
    )

    db_stats = get_database_stats()

    # Overview Stats
    st.markdown("### 🗄️ Database Repository Statistics")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Monitored Cities", db_stats["cities_count"])
    c2.metric("Total Ingested Records", f"{db_stats['total_records']:,}")
    c3.metric("Observed Readings", f"{db_stats['observed_records']:,}")
    c4.metric("Forecast Records", f"{db_stats['forecast_records']:,}")

    st.markdown("---")
    st.markdown("### 📥 Dataset Export Center (CSV)")

    raw_df = get_raw_dataset(record_type=None)
    cleaned_df, prep_report = get_cleaned_dataset()

    dcol1, dcol2 = st.columns(2)
    with dcol1:
        st.markdown("#### Raw Database Records")
        st.caption(f"Includes observed and forecast records ({len(raw_df):,} rows).")
        raw_csv = export_dataframe_to_csv(raw_df)
        st.download_button(
            label="⬇️ Download Raw Records (CSV)",
            data=raw_csv,
            file_name="airinsight_raw_records.csv",
            mime="text/csv",
            use_container_width=True
        )

    with dcol2:
        st.markdown("#### Cleaned Preprocessed Dataset")
        st.caption(f"Normalized, imputed, and IQR-capped observed records ({len(cleaned_df):,} rows).")
        clean_csv = export_dataframe_to_csv(cleaned_df)
        st.download_button(
            label="⬇️ Download Cleaned Dataset (CSV)",
            data=clean_csv,
            file_name="airinsight_cleaned_dataset.csv",
            mime="text/csv",
            use_container_width=True
        )

    st.markdown("---")
    st.markdown("### 📜 Data Mining Execution History")
    mining_logs = get_latest_mining_results(limit=15)
    if mining_logs:
        log_rows = []
        for l in mining_logs:
            res_summary = str(l["result"])
            if len(res_summary) > 75:
                res_summary = res_summary[:75] + "..."
            log_rows.append({
                "Run ID": l["id"],
                "Algorithm": l["algorithm"],
                "City": l.get("city_name") or "Global / Multi-City",
                "Timestamp": l["execution_timestamp"],
                "Result Summary": res_summary
            })
        st.dataframe(pd.DataFrame(log_rows), use_container_width=True, hide_index=True)
    else:
        st.info("No mining executions logged yet. Execute algorithms from the sidebar pages.")

    st.markdown("---")
    st.markdown("### 🎓 Comprehensive Project Analysis Report Generator")
    st.caption("Generates a formal university-grade lab report combining current database telemetry and model outputs.")

    if st.button("📝 Generate Academic Project Report", use_container_width=True):
        full_report_text = generate_academic_project_report(
            db_stats=db_stats,
            prep_report=prep_report,
            clustering_res=st.session_state.get("clustering_res"),
            dt_res=st.session_state.get("dt_results"),
            association_res=st.session_state.get("association_res"),
            trend_res=st.session_state.get("trend_res")
        )
        st.session_state["academic_report_text"] = full_report_text

    if "academic_report_text" in st.session_state:
        st.text_area("Generated Report Preview:", st.session_state["academic_report_text"], height=320)
        st.download_button(
            label="⬇️ Download Project Report (TXT)",
            data=st.session_state["academic_report_text"],
            file_name="airinsight_project_report.txt",
            mime="text/plain",
            use_container_width=True
        )


"""
Page 6: Apriori Association Rule Mining Module
Uncovers inter-pollutant co-occurrence patterns and associative dependencies.
Includes:
- Dynamic support, confidence, and lift thresholds
- Tabular display of mined association rules
- Support vs Confidence vs Lift visual scatter map
- Natural language scientific rule explanations
"""

import streamlit as st
import pandas as pd
from data.dataset_manager import get_cleaned_dataset
from algorithms.association_rules import mine_association_rules
from visualizations.charts import plot_association_rules_scatter
from database.db import save_mining_result


def render_association_page():
    st.markdown("## 🔗 Algorithm 3: Apriori Association Rule Mining")
    st.markdown(
        "Discovers frequent co-occurrence patterns and non-obvious associative dependencies between chemical "
        "pollutants. Continuous measures are categorized into **Low**, **Medium**, and **High** intervals based on WHO standards."
    )

    cleaned_df, _ = get_cleaned_dataset()
    if cleaned_df.empty or len(cleaned_df) < 15:
        st.warning("Insufficient data available for rule mining. Please ingest records first.")
        return

    # Hyperparameter Sliders
    c1, c2, c3, c4 = st.columns([1.2, 1.2, 1.2, 1])
    with c1:
        min_supp = st.slider("Min Support:", min_value=0.05, max_value=0.50, value=0.10, step=0.05)
    with c2:
        min_conf = st.slider("Min Confidence:", min_value=0.30, max_value=0.95, value=0.50, step=0.05)
    with c3:
        min_lift = st.slider("Min Lift Threshold:", min_value=1.0, max_value=4.0, value=1.1, step=0.1)
    with c4:
        st.write("")
        st.write("")
        run_rules_btn = st.button("⛏️ Mine Rules", use_container_width=True)

    # Compute or retrieve from session
    if run_rules_btn or "association_res" not in st.session_state:
        with st.spinner("Discretizing and mining association itemsets with Apriori..."):
            assoc_res = mine_association_rules(
                cleaned_df,
                min_support=min_supp,
                min_confidence=min_conf,
                min_lift=min_lift
            )
            st.session_state["association_res"] = assoc_res
            # Save to database
            rules_count = len(assoc_res["rules_df"])
            save_mining_result("Apriori Association", {
                "rules_found": rules_count,
                "min_support": min_supp,
                "min_confidence": min_conf,
                "min_lift": min_lift
            })

    assoc_res = st.session_state["association_res"]
    rules_df = assoc_res["rules_df"]

    if rules_df.empty:
        st.info("No association rules found matching the chosen Support and Confidence thresholds. Try relaxing the sliders.")
        return

    # Metrics
    st.markdown(f"### 📊 Discovered Rules Summary: **{len(rules_df)} Rules**")
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Discovered Rules", len(rules_df))
    m2.metric("Highest Rule Confidence", f"{rules_df['confidence'].max() * 100:.1f}%")
    m3.metric("Maximum Rule Lift", f"{rules_df['lift'].max():.2f}x")

    # Table of Rules
    st.markdown("#### 📜 Mined Association Rules Table")
    display_rules = rules_df[["antecedents_str", "consequents_str", "support", "confidence", "lift"]].copy()
    display_rules.columns = ["Antecedent (IF)", "Consequent (THEN)", "Support", "Confidence", "Lift"]
    display_rules["Support"] = display_rules["Support"].apply(lambda v: f"{v*100:.1f}%")
    display_rules["Confidence"] = display_rules["Confidence"].apply(lambda v: f"{v*100:.1f}%")
    display_rules["Lift"] = display_rules["Lift"].apply(lambda v: f"{v:.2f}x")
    st.dataframe(display_rules.head(25), use_container_width=True, hide_index=True)

    # Visual Scatter
    st.markdown("---")
    st.markdown("#### 🌌 Rule Distribution Map")
    fig_scatter = plot_association_rules_scatter(rules_df)
    st.plotly_chart(fig_scatter, use_container_width=True)

    # Scientific Narrative Interpretations
    st.markdown("---")
    st.markdown("### 💡 Natural Language Environmental Insights")
    st.caption("Human-interpretable insights automatically derived from high-confidence, high-lift rules:")
    for exp in assoc_res["rule_explanations"]:
        st.markdown(f"- {exp}")


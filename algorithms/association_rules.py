"""
Apriori Association Rule Mining Module for AirInsight
Discretizes continuous pollutant concentrations into categorical tiers (Low, Medium, High),
builds a transaction matrix, discovers frequent itemsets using the Apriori algorithm,
and generates association rules evaluated by Support, Confidence, and Lift.

No hardcoded rules: All outputs are dynamically mined from actual observed data.
"""

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from mlxtend.frequent_patterns import apriori, association_rules
from config import BIN_THRESHOLDS, BIN_LABELS, POLLUTANT_FEATURES


def discretize_pollutants(
    df: pd.DataFrame,
    features: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Transforms continuous pollutant values into categorical labels: Low, Medium, High
    using documented environmental threshold cutoffs.
    """
    if features is None:
        features = [f for f in ["pm2_5", "pm10", "no2", "co", "so2", "o3"] if f in df.columns]

    cat_df = pd.DataFrame(index=df.index)
    for feat in features:
        if feat in df.columns:
            bins = BIN_THRESHOLDS.get(feat, [0, 30, 60, 10000])
            # Ensure bins cover min and max
            clean_series = df[feat].dropna()
            if clean_series.empty:
                continue
            min_val = min(clean_series.min() - 0.1, bins[0])
            max_val = max(clean_series.max() + 0.1, bins[-1])
            custom_bins = [min_val, bins[1], bins[2], max_val]
            
            # Map column name to clean label (e.g., PM2.5)
            col_name = feat.upper().replace("_", ".")
            cat_df[col_name] = pd.cut(
                df[feat],
                bins=custom_bins,
                labels=BIN_LABELS,
                include_lowest=True
            ).astype(str)

    return cat_df


def build_one_hot_transaction_matrix(cat_df: pd.DataFrame) -> pd.DataFrame:
    """
    Encodes categorical features into boolean one-hot transaction matrix for Apriori.
    Items look like: 'PM2.5=High', 'NO2=Medium', etc.
    """
    one_hot_cols = {}
    for col in cat_df.columns:
        for val in BIN_LABELS:
            item_name = f"{col}={val}"
            one_hot_cols[item_name] = (cat_df[col] == val)

    return pd.DataFrame(one_hot_cols, index=cat_df.index)


def mine_association_rules(
    df: pd.DataFrame,
    min_support: float = 0.10,
    min_confidence: float = 0.50,
    min_lift: float = 1.0,
    features: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Executes Apriori Association Rule Mining.
    Computes:
        - Frequent itemsets with support
        - Discovered association rules with Antecedents, Consequents, Support, Confidence, Lift
        - Human-readable interpretations of the top rules
    """
    valid_df = df.copy()
    cat_df = discretize_pollutants(valid_df, features=features)
    if cat_df.empty or len(cat_df) < 10:
        return {
            "rules_df": pd.DataFrame(),
            "frequent_itemsets": pd.DataFrame(),
            "rule_explanations": ["Insufficient data to perform association rule mining."],
            "summary": {"total_rules": 0, "min_support": min_support, "min_confidence": min_confidence}
        }

    # Build boolean one-hot matrix
    transaction_df = build_one_hot_transaction_matrix(cat_df)

    # 1. Mine frequent itemsets
    frequent_itemsets = apriori(
        transaction_df,
        min_support=min_support,
        use_colnames=True,
        max_len=3
    )

    if frequent_itemsets.empty:
        return {
            "rules_df": pd.DataFrame(),
            "frequent_itemsets": pd.DataFrame(),
            "rule_explanations": [f"No frequent itemsets found at min_support = {min_support}."],
            "summary": {"total_rules": 0, "min_support": min_support, "min_confidence": min_confidence}
        }

    # 2. Mine association rules
    rules = association_rules(
        frequent_itemsets,
        metric="confidence",
        min_threshold=min_confidence
    )

    if rules.empty:
        return {
            "rules_df": pd.DataFrame(),
            "frequent_itemsets": frequent_itemsets,
            "rule_explanations": [f"Frequent itemsets exist, but no rules met min_confidence = {min_confidence}."],
            "summary": {"total_rules": 0, "min_support": min_support, "min_confidence": min_confidence}
        }

    # Filter by minimum lift
    rules = rules[rules["lift"] >= min_lift].sort_values(by="lift", ascending=False).reset_index(drop=True)

    # Convert frozensets to readable string representations
    rules["antecedents_str"] = rules["antecedents"].apply(lambda s: ", ".join(list(s)))
    rules["consequents_str"] = rules["consequents"].apply(lambda s: ", ".join(list(s)))

    # Generate human-readable analytical explanations
    explanations = []
    for idx, row in rules.head(8).iterrows():
        ant = row["antecedents_str"]
        con = row["consequents_str"]
        conf_pct = round(row["confidence"] * 100, 1)
        supp_pct = round(row["support"] * 100, 1)
        lift_val = round(row["lift"], 2)

        exp = (
            f"**Rule {idx + 1}:** IF `{ant}` THEN `{con}` "
            f"(Confidence: {conf_pct}%, Support: {supp_pct}%, Lift: {lift_val}x). "
            f"When {ant} occurs, the likelihood of observing {con} is {lift_val} times higher than random chance."
        )
        explanations.append(exp)

    return {
        "rules_df": rules,
        "frequent_itemsets": frequent_itemsets,
        "rule_explanations": explanations,
        "summary": {
            "total_rules": len(rules),
            "min_support": min_support,
            "min_confidence": min_confidence,
            "min_lift": min_lift
        }
    }


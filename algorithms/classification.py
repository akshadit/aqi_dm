"""
Decision Tree Classification Module for AirInsight
Learns to classify air quality observations into standard US EPA AQI health categories:
- Good (0-50)
- Moderate (51-100)
- Unhealthy for Sensitive Groups (101-150)
- Unhealthy (151-200)
- Very Unhealthy (201-300)
- Hazardous (301-500)

CRITICAL: Strictly prevents target leakage by excluding 'us_aqi' and 'european_aqi'
from the input feature matrix X. The model learns pollutant boundary thresholds.
"""

from typing import Dict, Any, List, Tuple, Optional
import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeClassifier, export_text, plot_tree
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report
)
from config import POLLUTANT_FEATURES, AQI_CATEGORIES


def assign_aqi_category(aqi_val: float) -> str:
    """Maps continuous US AQI value into official EPA categorical tier."""
    if pd.isna(aqi_val):
        return "Unknown"
    for cat in AQI_CATEGORIES:
        if cat["min"] <= aqi_val <= cat["max"]:
            return cat["label"]
    return "Hazardous" if aqi_val > 500 else "Good"


def train_decision_tree_classifier(
    df: pd.DataFrame,
    features: List[str] = POLLUTANT_FEATURES,
    test_size: float = 0.2,
    max_depth: int = 5,
    criterion: str = "gini"
) -> Dict[str, Any]:
    """
    Trains a Decision Tree Classifier to predict AQI categories from pollutant levels.
    Evaluates with Accuracy, Precision, Recall, F1-Score, and Confusion Matrix.
    """
    valid_df = df.copy()
    
    # 1. Ensure target category exists without leakage
    if "aqi_category" not in valid_df.columns:
        if "us_aqi" not in valid_df.columns:
            raise ValueError("Dataset lacks 'us_aqi' column needed to derive classification ground truth.")
        valid_df["aqi_category"] = valid_df["us_aqi"].apply(assign_aqi_category)

    # Filter out Unknown / NaN
    valid_df = valid_df[valid_df["aqi_category"] != "Unknown"]
    valid_df = valid_df.dropna(subset=features + ["aqi_category"]).reset_index(drop=True)

    if len(valid_df) < 20:
        raise ValueError(f"Insufficient samples ({len(valid_df)}) for training Decision Tree.")

    # 2. Extract feature matrix X and target y (LEAKAGE PREVENTION)
    X = valid_df[features]
    y = valid_df["aqi_category"]

    # Stratify if all classes have >= 2 instances
    class_counts = y.value_counts()
    can_stratify = (class_counts >= 2).all()
    stratify_param = y if can_stratify else None

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42, stratify=stratify_param
    )

    # 3. Fit Decision Tree Classifier
    dt_clf = DecisionTreeClassifier(
        criterion=criterion,
        max_depth=max_depth,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42
    )
    dt_clf.fit(X_train, y_train)

    # 4. Predictions & Evaluation
    y_pred = dt_clf.predict(X_test)
    labels = sorted(list(set(y)))

    accuracy = float(accuracy_score(y_test, y_pred))
    precision = float(precision_score(y_test, y_pred, average="weighted", zero_division=0))
    recall = float(recall_score(y_test, y_pred, average="weighted", zero_division=0))
    f1 = float(f1_score(y_test, y_pred, average="weighted", zero_division=0))

    cm = confusion_matrix(y_test, y_pred, labels=labels)
    class_rep = classification_report(y_test, y_pred, labels=labels, output_dict=True, zero_division=0)

    # Feature Importance
    feature_importances = {
        feat: round(float(imp), 4)
        for feat, imp in zip(features, dt_clf.feature_importances_)
    }
    # Sort descending
    sorted_importances = dict(sorted(feature_importances.items(), key=lambda item: item[1], reverse=True))

    tree_rules_text = export_text(dt_clf, feature_names=features)

    return {
        "model": dt_clf,
        "features": features,
        "classes": labels,
        "accuracy": round(accuracy * 100, 2),
        "precision": round(precision * 100, 2),
        "recall": round(recall * 100, 2),
        "f1_score": round(f1 * 100, 2),
        "confusion_matrix": cm.tolist(),
        "confusion_matrix_labels": labels,
        "classification_report": class_rep,
        "feature_importances": sorted_importances,
        "tree_text": tree_rules_text,
        "train_size": len(X_train),
        "test_size": len(X_test),
    }


def predict_single_sample(
    model: DecisionTreeClassifier,
    features: List[str],
    sample_values: Dict[str, float]
) -> Tuple[str, Dict[str, float]]:
    """
    Predicts AQI category for a single manual input vector.
    Returns (predicted_category, probability_distribution).
    """
    row_df = pd.DataFrame([[sample_values.get(f, 0.0) for f in features]], columns=features)
    pred_class = model.predict(row_df)[0]
    probs = model.predict_proba(row_df)[0]
    prob_dist = {
        cls_name: round(float(p) * 100, 1)
        for cls_name, p in zip(model.classes_, probs)
    }
    return pred_class, prob_dist

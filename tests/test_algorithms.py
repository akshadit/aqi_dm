"""
Unit Tests for Data Mining Algorithms
Tests K-Means Clustering, Decision Tree Classification,
Apriori Association Rule Mining, and Linear Regression Trend Analysis.
"""

import unittest
import pandas as pd
import numpy as np
from data.dataset_manager import get_cleaned_dataset
from algorithms.clustering import perform_kmeans_clustering, compute_elbow_curve
from algorithms.classification import train_decision_tree_classifier, predict_single_sample
from algorithms.association_rules import mine_association_rules
from algorithms.regression import analyze_pollutant_trend


class TestDataMiningAlgorithms(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Load preprocessed dataset
        cls.df, cls.report = get_cleaned_dataset()

    def test_kmeans_clustering(self):
        """Validates K-Means clustering execution, metrics, and PCA coordinates."""
        res = perform_kmeans_clustering(self.df, n_clusters=3)
        self.assertIn("df_clustered", res)
        self.assertIn("cluster", res["df_clustered"].columns)
        self.assertIn("pca_1", res["df_clustered"].columns)
        self.assertIn("pca_2", res["df_clustered"].columns)
        self.assertGreater(res["inertia"], 0.0)
        self.assertEqual(len(res["cluster_summaries"]), 3)

    def test_decision_tree_classification_no_leakage(self):
        """Validates Decision Tree training and ensures US AQI is withheld from input features."""
        dt_res = train_decision_tree_classifier(self.df, max_depth=4)
        self.assertNotIn("us_aqi", dt_res["features"])
        self.assertNotIn("european_aqi", dt_res["features"])
        self.assertGreater(dt_res["accuracy"], 50.0)
        self.assertGreater(len(dt_res["confusion_matrix"]), 0)

        # Test single sample prediction
        sample = {"pm2_5": 85.0, "pm10": 140.0, "no2": 45.0, "so2": 15.0, "co": 1100.0, "o3": 35.0}
        pred_cat, probs = predict_single_sample(dt_res["model"], dt_res["features"], sample)
        self.assertIsInstance(pred_cat, str)
        self.assertIn(pred_cat, dt_res["classes"])

    def test_apriori_association_rules(self):
        """Validates Apriori rule discovery and metric calculations."""
        assoc_res = mine_association_rules(self.df, min_support=0.08, min_confidence=0.40)
        self.assertIn("rules_df", assoc_res)
        if not assoc_res["rules_df"].empty:
            rules = assoc_res["rules_df"]
            self.assertIn("support", rules.columns)
            self.assertIn("confidence", rules.columns)
            self.assertIn("lift", rules.columns)
            self.assertTrue((rules["confidence"] >= 0.40).all())

    def test_linear_regression_trend(self):
        """Validates Linear Regression trend modeling, slope, MAE, and RMSE."""
        # Test on single city slice
        city_id = self.df["city_id"].iloc[0]
        city_df = self.df[self.df["city_id"] == city_id]
        trend_res = analyze_pollutant_trend(city_df, target_pollutant="pm2_5", forecast_hours=24)

        self.assertIn("slope_per_hour", trend_res)
        self.assertIn("mae", trend_res)
        self.assertIn("rmse", trend_res)
        self.assertGreater(len(trend_res["future_df"]), 0)
        self.assertGreaterEqual(trend_res["mae"], 0.0)


if __name__ == "__main__":
    unittest.main()


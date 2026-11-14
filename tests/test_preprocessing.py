"""
Unit Tests for Data Preprocessing Pipeline
"""

import unittest
import pandas as pd
import numpy as np
from data.preprocessing import detect_outliers_iqr, run_preprocessing_pipeline, get_scaled_features


class TestPreprocessingPipeline(unittest.TestCase):

    def setUp(self):
        # Create synthetic test dataset
        self.test_df = pd.DataFrame({
            "city_id": [1, 1, 1, 1, 1, 1],
            "timestamp": pd.date_range("2026-01-01", periods=6, freq="h"),
            "pm2_5": [20.0, np.nan, 25.0, 30.0, 450.0, 30.0],  # 450 is outlier, index 1 is NaN
            "pm10": [40.0, 50.0, 55.0, 60.0, 70.0, 60.0],
            "no2": [15.0, 18.0, 20.0, 22.0, 25.0, 22.0],
            "so2": [5.0, 6.0, 7.0, 8.0, 9.0, 8.0],
            "co": [500.0, 550.0, 600.0, 650.0, 700.0, 650.0],
            "o3": [20.0, 25.0, 30.0, 35.0, 40.0, 35.0],
            "us_aqi": [68.0, 75.0, 78.0, 88.0, 450.0, 88.0],
            "record_type": ["observed"] * 6
        })

    def test_iqr_outlier_detection(self):
        series = pd.Series([10.0, 12.0, 14.0, 15.0, 16.0, 18.0, 500.0])
        mask, lb, ub, count = detect_outliers_iqr(series)
        self.assertEqual(count, 1)
        self.assertTrue(mask.iloc[-1])

    def test_preprocessing_pipeline_imputation_and_capping(self):
        cleaned, report = run_preprocessing_pipeline(self.test_df, handle_outliers_method="cap")
        # Missing value should be imputed
        self.assertEqual(cleaned["pm2_5"].isna().sum(), 0)
        # Outlier should be capped below 450
        self.assertLess(cleaned["pm2_5"].max(), 400.0)
        self.assertGreaterEqual(report["final_records"], 5)

    def test_feature_scaling(self):
        feats = ["pm10", "no2"]
        scaled, scaler = get_scaled_features(self.test_df, feats)
        self.assertEqual(scaled.shape, (6, 2))
        self.assertAlmostEqual(float(scaled[:, 0].mean()), 0.0, places=5)
        self.assertAlmostEqual(float(scaled[:, 0].std()), 1.0, places=1)


if __name__ == "__main__":
    unittest.main()


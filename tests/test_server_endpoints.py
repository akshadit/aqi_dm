"""
Test FastAPI Endpoints for the Modern Web Stack
"""

import unittest
from starlette.testclient import TestClient
from server import app


class TestServerEndpoints(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_stats_endpoint(self):
        res = self.client.get("/api/stats")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("total_records", data)
        self.assertIn("cities_count", data)

    def test_cities_endpoint(self):
        res = self.client.get("/api/cities")
        self.assertEqual(res.status_code, 200)
        cities = res.json()
        self.assertGreaterEqual(len(cities), 6)

    def test_overview_endpoint(self):
        res = self.client.get("/api/overview")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("cities_summary", data)

    def test_kmeans_endpoint(self):
        res = self.client.post("/api/mining/kmeans", json={"k": 3})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("inertia", data)
        self.assertIn("pca_points", data)

    def test_decision_tree_and_predict_endpoint(self):
        # 1. Train Decision Tree
        res = self.client.post("/api/mining/decision-tree", json={"max_depth": 4, "criterion": "gini"})
        self.assertEqual(res.status_code, 200)
        dt_data = res.json()
        self.assertIn("accuracy", dt_data)
        self.assertIn("confusion_matrix", dt_data)

        # 2. Simulate live prediction
        sample_payload = {
            "pm2_5": 85.0, "pm10": 140.0, "no2": 45.0,
            "so2": 15.0, "co": 1100.0, "o3": 35.0
        }
        res_pred = self.client.post("/api/mining/predict-sample", json=sample_payload)
        self.assertEqual(res_pred.status_code, 200)
        pred_data = res_pred.json()
        self.assertIn("predicted_category", pred_data)
        self.assertIn("probabilities", pred_data)

    def test_frontend_static_serving(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn("<title>AirInsight", res.text)


if __name__ == "__main__":
    unittest.main()


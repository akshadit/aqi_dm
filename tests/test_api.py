"""
Unit Tests for Air Quality & Geocoding API Modules
"""

import unittest
from api.geocoding_api import search_city
from api.air_quality_api import transform_api_response_to_records


class TestAPIIntegration(unittest.TestCase):

    def test_geocoding_default_city_resolution(self):
        """Tests that default cities resolve coordinates immediately."""
        results = search_city("Bengaluru")
        self.assertGreaterEqual(len(results), 1)
        bengaluru = results[0]
        self.assertEqual(bengaluru["name"], "Bengaluru")
        self.assertAlmostEqual(bengaluru["latitude"], 12.9716, places=2)
        self.assertAlmostEqual(bengaluru["longitude"], 77.5946, places=2)

    def test_geocoding_empty_input(self):
        """Tests empty query handling."""
        self.assertEqual(search_city("   "), [])

    def test_api_response_transformation(self):
        """Tests parsing of API payload into relational records."""
        sample_api_response = {
            "hourly": {
                "time": ["2026-01-01T00:00", "2026-01-01T01:00"],
                "pm2_5": [45.2, 50.1],
                "pm10": [85.0, 92.4],
                "carbon_monoxide": [800.0, 850.0],
                "nitrogen_dioxide": [35.0, 40.0],
                "sulphur_dioxide": [12.0, 15.0],
                "ozone": [25.0, 20.0],
                "dust": [15.0, 18.0],
                "european_aqi": [40, 45],
                "us_aqi": [110, 125]
            }
        }
        records = transform_api_response_to_records(sample_api_response, city_id=1)
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["city_id"], 1)
        self.assertEqual(records[0]["pm2_5"], 45.2)
        self.assertIn(records[0]["record_type"], ["observed", "forecast"])


if __name__ == "__main__":
    unittest.main()


import unittest
from unittest.mock import patch, MagicMock
import sys
import io
import bike_miles

class TestBikeMiles(unittest.TestCase):
    @patch('requests.get')
    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('sys.argv', ['bike_miles.py', 'test_token', '2023'])
    def test_main(self, mock_stdout, mock_get):
        # Mock responses
        mock_athlete_resp = MagicMock()
        mock_athlete_resp.json.return_value = {
            "bikes": [
                {"id": "b1", "name": "Road Bike"},
                {"id": "b2", "name": "Mountain Bike"}
            ]
        }

        mock_activities_page1_resp = MagicMock()
        mock_activities_page1_resp.json.return_value = [
            {"gear_id": "b1", "distance": 16093.44}, # 10 miles
            {"gear_id": "b2", "distance": 32186.88}, # 20 miles
            {"gear_id": "b1", "distance": 1609.344}  # 1 mile
        ]

        mock_activities_page2_resp = MagicMock()
        mock_activities_page2_resp.json.return_value = []

        mock_get.side_effect = [
            mock_athlete_resp,
            mock_activities_page1_resp,
            mock_activities_page2_resp
        ]

        bike_miles.main()

        output = mock_stdout.getvalue()

        # Verify output
        self.assertIn("Road Bike     : 11.0", output)
        self.assertIn("Mountain Bike : 20.0", output)
        self.assertIn("Mileage for 2023", output)

if __name__ == '__main__':
    unittest.main()

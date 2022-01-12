from unittest import TestCase
from fastapi.testclient import TestClient
from src.main import app


class TestFastapiSubmitPrediction(TestCase):
    def test_ok(self):
        client = TestClient(app)
        params = {
            'model_id': 'model1',
            'execution_start_at': 1 * 60 * 60,
            'prediction_license': 'CC0-1.0',
            'content': """symbol,position
BTC,0.1
"""
        }
        response = client.post('/submit_prediction', params=params)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['content-type'], 'application/json')
        self.assertEqual(response.json(), {})


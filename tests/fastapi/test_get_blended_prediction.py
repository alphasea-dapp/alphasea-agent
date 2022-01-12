from unittest import TestCase
from fastapi.testclient import TestClient
from src.main import app


class TestFastapiGetBlendedPrediction(TestCase):
    def test_ok(self):
        client = TestClient(app)
        response = client.get('/blended_prediction.csv', params={ 'execution_start_at': 1 })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['content-type'], 'text/csv; charset=utf-8')
        expected = b"""symbol,position
"""
        self.assertEqual(response.content, expected)


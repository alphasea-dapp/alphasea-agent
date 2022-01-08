from unittest import TestCase
from src.prediction_format import normalize_content


class TestPredictionFormatNormalizeContent(TestCase):
    def test_normalize_content(self):
        content = normalize_content(b"""position,symbol
0.2,ETH
0.3,XRP
0.11111111111111111111111111111111111111111111111111111111111111111111111111111,BTC""")

        expected = b"""symbol,position
BTC,0.11111111111111111111111111111111111111111111111111111111111111111111111111111
ETH,0.2
XRP,0.3"""

        self.assertEqual(content, expected)

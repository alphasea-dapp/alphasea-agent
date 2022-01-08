from unittest import TestCase
import pandas as pd
from pandas.util.testing import assert_frame_equal
from src.prediction_format import parse_content


class TestPredictionFormatParseContent(TestCase):
    def test_parse_content(self):
        df = parse_content(b"""symbol,position
ETH,0.2
XRP,0.3
BTC,0.1""")

        expected = pd.DataFrame([
            ['BTC', 0.1],
            ['ETH', 0.2],
            ['XRP', 0.3],
        ], columns=['symbol', 'position']).set_index('symbol')

        assert_frame_equal(df, expected)

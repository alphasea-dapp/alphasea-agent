import pandas as pd
from pandas.testing import assert_frame_equal
from unittest import TestCase
from src.executor.utils import _prediction_to_df
from src.types.exceptions import ValidationError


class TestExecutorPredictionToDf(TestCase):
    def test_ok(self):
        content = b"""symbol,position
BTC,0.1
XRP,0.3
ETH,0.2
"""
        prediction = {
            'content': content,
            'model_id': 'model1',
            'execution_start_at': 1,
        }
        expected = pd.DataFrame(
            [
                ['model1', 1, 'BTC', 0.1],
                ['model1', 1, 'ETH', 0.2],
                ['model1', 1, 'XRP', 0.3],
            ],
            columns=['model_id', 'execution_start_at', 'symbol', 'position'],
        ).set_index(['model_id', 'execution_start_at', 'symbol'])
        assert_frame_equal(_prediction_to_df(prediction), expected)

    def test_invalid_content(self):
        content = 'invalid'
        prediction = {
            'content': content,
            'model_id': 'model1',
            'execution_start_at': 1,
        }
        with self.assertRaisesRegex(ValidationError, 'decode failed'):
            _prediction_to_df(prediction)

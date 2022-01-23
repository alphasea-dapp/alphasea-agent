import pandas as pd
from pandas.testing import assert_frame_equal
from unittest import TestCase
from src.executor.utils import blend_predictions
from src.logger import create_null_logger


class TestExecutorBlendPredictions(TestCase):
    def test_ok(self):
        content1 = b"""symbol,position
BTC,0.1
ETH,0.2"""

        content2 = b"""symbol,position
BTC,0.3
ETH,0.4"""

        df_weight = pd.DataFrame(
            [
                ['model1', 1],
                ['model2', 2],
                ['model_invalid', 1],
                ['model_df_weight_only', 1],
            ],
            columns=['model_id', 'weight'],
        ).set_index(['model_id'])

        df_current = pd.DataFrame(
            [
                ['model1', content1],
                ['model2', content2],
                ['model_invalid', 'invalid'],
                ['model_df_current', 1],
            ],
            columns=['model_id', 'content'],
        ).set_index(['model_id'])

        expected = pd.DataFrame(
            [
                ['BTC', 0.7],
                ['ETH', 1.0],
            ],
            columns=['symbol', 'position'],
        ).set_index(['symbol'])

        assert_frame_equal(blend_predictions(
            df_weight=df_weight,
            df_current=df_current,
            logger=create_null_logger(),
        ), expected)

    def test_df_weight_is_none(self):
        df_weight = None

        df_current = pd.DataFrame(
            [],
            columns=['model_id', 'content'],
        ).set_index(['model_id'])

        expected = pd.DataFrame(
            [],
            columns=['symbol', 'position'],
        ).set_index(['symbol'])

        assert_frame_equal(blend_predictions(
            df_weight=df_weight,
            df_current=df_current,
            logger=create_null_logger(),
        ), expected)


    def test_empty(self):
        df_weight = pd.DataFrame(
            [],
            columns=['model_id', 'weight'],
        ).set_index(['model_id'])

        df_current = pd.DataFrame(
            [],
            columns=['model_id', 'content'],
        ).set_index(['model_id'])

        expected = pd.DataFrame(
            [],
            columns=['symbol', 'position'],
        ).set_index(['symbol'])

        assert_frame_equal(blend_predictions(
            df_weight=df_weight,
            df_current=df_current,
            logger=create_null_logger(),
        ), expected)

from unittest import TestCase
import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal
from src.executor.utils import _pivot_df


class TestExecutorPivotDf(TestCase):
    def test_ok(self):
        df = pd.DataFrame([
            ['model1', 1, 'BTC', 1.0],
            ['model1', 2, 'BTC', 2.0],
            ['model1', 2, 'ETH', 3.0],
            ['model2', 3, 'BTC', 4.0],
        ], columns=['model_id', 'execution_start_at', 'symbol', 'ret']
        ).set_index(['model_id', 'execution_start_at', 'symbol'])

        execution_start_ats = [2, 3]
        df_ret = _pivot_df(df, execution_start_ats, 'ret')

        expected = pd.DataFrame([
            [2, 2.0, 3.0, np.nan],
            [3, np.nan, np.nan, 4.0],
        ], columns=['execution_start_at', 'BTC1', 'ETH1', 'BTC2']).set_index('execution_start_at')

        expected.columns = pd.MultiIndex.from_tuples(
            [
                ('model1', 'BTC'),
                ('model1', 'ETH'),
                ('model2', 'BTC'),
            ],
            names=["model_id", "symbol"]
        )

        assert_frame_equal(df_ret, expected)

    def test_empty(self):
        df = pd.DataFrame([
        ], columns=['model_id', 'execution_start_at', 'symbol', 'ret']
        ).set_index(['model_id', 'execution_start_at', 'symbol'])

        execution_start_ats = [2, 3]
        df_ret = _pivot_df(df, execution_start_ats, 'ret')

        expected = pd.DataFrame([
            [2],
            [3],
        ], columns=['execution_start_at']).set_index('execution_start_at')

        expected.columns = pd.MultiIndex.from_tuples(
            [],
            names=["model_id", "symbol"]
        )

        assert_frame_equal(df_ret, expected)

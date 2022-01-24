from unittest import TestCase
import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal
from src.executor.utils import create_model_selection_params


class TestExecutorCreateModelSelectionParams(TestCase):
    def test_ok(self):
        df = pd.DataFrame([
            ['model1', 1, 'BTC', 1.0],
            ['model1', 2, 'BTC', 2.0],
            ['model1', 2, 'ETH', 3.0],
            ['model2', 3, 'BTC', 4.0],
            ['model2', 3, 'XRP', 4.0],
        ], columns=['model_id', 'execution_start_at', 'symbol', 'position']
        ).set_index(['model_id', 'execution_start_at', 'symbol'])

        df_current = pd.DataFrame([
            ['model1'],
            ['model2'],
        ], columns=['model_id']
        ).set_index(['model_id'])

        df_market = pd.DataFrame([
            [2, 'BTC', 0.1],
            [2, 'ETH', 0.2],
            [3, 'BTC', 0.3],
            [3, 'XRP', 0.3],
        ], columns=['execution_start_at', 'symbol', 'ret']
        ).set_index(['execution_start_at', 'symbol'])

        execution_start_ats = [2, 3]
        symbols = ['BTC', 'ETH']

        params = create_model_selection_params(
            df=df,
            df_current=df_current,
            df_market=df_market,
            execution_start_ats=execution_start_ats,
            symbols=symbols
        )

        expected_ret = pd.DataFrame([
            [2, 0.1, 0.2, 0.0],
            [3, 0.0, 0.0, 0.3],
        ], columns=['execution_start_at', 'BTC1', 'ETH1', 'BTC2']).set_index('execution_start_at')
        expected_ret.columns = pd.MultiIndex.from_tuples(
            [
                ('model1', 'BTC'),
                ('model1', 'ETH'),
                ('model2', 'BTC'),
            ],
            names=["model_id", "symbol"]
        )

        expected_pos = pd.DataFrame([
            [2, 2.0, 3.0, 0.0],
            [3, 0.0, 0.0, 4.0],
        ], columns=['execution_start_at', 'BTC1', 'ETH1', 'BTC2']).set_index('execution_start_at')
        expected_pos.columns = pd.MultiIndex.from_tuples(
            [
                ('model1', 'BTC'),
                ('model1', 'ETH'),
                ('model2', 'BTC'),
            ],
            names=["model_id", "symbol"]
        )

        assert_frame_equal(params.df_ret, expected_ret)
        assert_frame_equal(params.df_position, expected_pos)
        assert_frame_equal(params.df_current, df_current)
        self.assertEqual(params.budget, None)
        self.assertEqual(params.random_state, None)

    def test_empty(self):
        df = pd.DataFrame([
        ], columns=['model_id', 'execution_start_at', 'symbol', 'position']
        ).set_index(['model_id', 'execution_start_at', 'symbol'])

        df_current = pd.DataFrame([
            ['model1'],
            ['model2'],
        ], columns=['model_id']
        ).set_index(['model_id'])

        df_market = pd.DataFrame([
            [2, 'BTC', 0.1],
            [2, 'ETH', 0.2],
            [3, 'BTC', 0.3],
            [3, 'XRP', 0.3],
        ], columns=['execution_start_at', 'symbol', 'ret']
        ).set_index(['execution_start_at', 'symbol'])

        execution_start_ats = [2, 3]
        symbols = ['BTC', 'ETH']

        params = create_model_selection_params(
            df=df,
            df_current=df_current,
            df_market=df_market,
            execution_start_ats=execution_start_ats,
            symbols=symbols
        )

        expected_ret = pd.DataFrame([
            [2],
            [3],
        ], columns=['execution_start_at']).set_index('execution_start_at')
        expected_ret.columns = pd.MultiIndex.from_tuples(
            [],
            names=["model_id", "symbol"]
        )

        expected_pos = pd.DataFrame([
            [2],
            [3],
        ], columns=['execution_start_at']).set_index('execution_start_at')
        expected_pos.columns = pd.MultiIndex.from_tuples(
            [],
            names=["model_id", "symbol"]
        )

        assert_frame_equal(params.df_ret, expected_ret)
        assert_frame_equal(params.df_position, expected_pos)
        assert_frame_equal(params.df_current, df_current)
        self.assertEqual(params.budget, None)
        self.assertEqual(params.random_state, None)

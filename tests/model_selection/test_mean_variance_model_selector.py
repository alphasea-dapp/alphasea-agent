from unittest import TestCase
import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal
from src.model_selection.mean_variance_model_selector import MeanVarianceModelSelector


class TestMeanVarianceModelSelector(TestCase):
    def test_ok(self):
        selector = MeanVarianceModelSelector(
            execution_cost=0.01,
            assets=10,
            budget=1,
            symbol_white_list='BTC,ETH'
        )

        df = pd.DataFrame([
            ['model1', 1, 'BTC', 0.5],
            ['model1', 1, 'ETH', 0.5],
            ['model1', 2, 'BTC', 0.5],
            ['model1', 2, 'ETH', 0.5],
            ['model2', 1, 'BTC', 0.5],
            ['model2', 1, 'ETH', 0.5],
            ['model2', 2, 'BTC', 0.5],
            ['model2', 2, 'ETH', 0.5],
            ['model3', 2, 'XRP', 1.0],
        ], columns=['model_id', 'execution_start_at', 'symbol', 'position']).set_index('model_id')

        df_model = pd.DataFrame([
            ['model1', 1],
            ['model2', 2],
            ['model3', 3],
        ], columns=['model_id', 'price']).set_index('model_id')

        df_weight = selector.select_model(
            df=df,
            df_model=df_model,
            random_state=1,
        )

        expected = pd.DataFrame([
            ['model1', 0.5],
            ['model2', 0.5],
        ], columns=['model_id', 'weight']).set_index('model_id')

        assert_frame_equal(df_weight, expected)

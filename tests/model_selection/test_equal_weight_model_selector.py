from unittest import TestCase
import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal
from src.model_selection.equal_weight_model_selector import EqualWeightModelSelector
import random


class TestEqualWeightModelSelector(TestCase):
    def test_ok(self):
        selector = EqualWeightModelSelector(
            execution_cost=0.01,
            assets=10000,
        )

        df = pd.DataFrame(
            [
                ['model1', 1, 'BTC', 1.0],
                ['model1', 1, 'ETH', 0.0],
                ['model1', 2, 'BTC', 1.0],
                ['model1', 2, 'ETH', 0.0],
                ['model2', 1, 'BTC', 0.0],
                ['model2', 1, 'ETH', 1.0],
                ['model2', 2, 'BTC', 0.0],
                ['model2', 2, 'ETH', 1.0],
            ],
            columns=['model_id', 'execution_start_at', 'symbol', 'position']
        ).set_index(['model_id', 'execution_start_at', 'symbol'])

        df_market = pd.DataFrame(
            [
                [1, 'BTC', 1.1],
                [1, 'ETH', 0.1],
                [2, 'BTC', 1.2],
                [2, 'ETH', 0.2],
            ],
            columns=['execution_start_at', 'symbol', 'ret']
        ).set_index(['execution_start_at', 'symbol'])

        df_current = pd.DataFrame([
            ['model1', 1],
            ['model2', 1],
        ], columns=['model_id', 'price']).set_index('model_id')

        random.seed(1)  # simanneal depends random.random
        df_weight = selector.select_model(
            df=df,
            df_current=df_current,
            df_market=df_market,
            budget=100,
            random_state=1,
        )

        expected = pd.DataFrame([
            ['model1', 1.0],
        ], columns=['model_id', 'weight']).set_index('model_id')

        assert_frame_equal(df_weight, expected)

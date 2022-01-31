from unittest import TestCase
import random
import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal
from src.model_selection.score_model_selector import ScoreModelSelector, default_scorer
from src.executor.utils import create_model_selection_params


def scorer(x):
    return x.mean()


class TestScoreModelSelector(TestCase):
    def test_ok(self):
        selector = ScoreModelSelector(
            execution_cost=0.01,
            scorer=scorer,
            score_threshold=0.0,
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
            ['model1'],
            ['model2'],
        ], columns=['model_id']).set_index('model_id')

        random.seed(1)  # simanneal depends random.random

        params = create_model_selection_params(
            df=df,
            df_current=df_current,
            df_market=df_market,
            execution_start_ats=[1, 2],
            symbols=['BTC', 'ETH'],
        )

        df_weight = selector.select_model(params)

        expected = pd.DataFrame([
            ['model1', 1.0],
        ], columns=['model_id', 'weight']).set_index('model_id')

        assert_frame_equal(df_weight, expected)

    def test_score_threshold(self):
        selector = ScoreModelSelector(
            execution_cost=0.01,
            scorer=scorer,
            score_threshold=1.0,
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
            ['model1'],
            ['model2'],
        ], columns=['model_id']).set_index('model_id')

        random.seed(1)  # simanneal depends random.random

        params = create_model_selection_params(
            df=df,
            df_current=df_current,
            df_market=df_market,
            execution_start_ats=[1, 2],
            symbols=['BTC', 'ETH'],
        )

        df_weight = selector.select_model(params)

        expected = pd.DataFrame([
            ['model1', 0.5],
            ['model2', 0.5],
        ], columns=['model_id', 'weight']).set_index('model_id')

        assert_frame_equal(df_weight, expected)

    def test_owner(self):
        selector = ScoreModelSelector(
            execution_cost=0.01,
            scorer=scorer,
            score_threshold=0.0,
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
            ['model1', 'owner1'],
            ['model2', 'owner2'],
        ], columns=['model_id', 'owner']).set_index('model_id')

        random.seed(1)  # simanneal depends random.random

        params = create_model_selection_params(
            df=df,
            df_current=df_current,
            df_market=df_market,
            execution_start_ats=[1, 2],
            symbols=['BTC', 'ETH'],
        )
        params.owner = 'owner2'

        df_weight = selector.select_model(params)

        expected = pd.DataFrame([
            ['model1', 0.5],
            ['model2', 0.5],
        ], columns=['model_id', 'weight']).set_index('model_id')

        assert_frame_equal(df_weight, expected)

        receivers = selector.select_receivers(params)
        self.assertEqual(list(receivers), ['owner1', 'owner2'])

    def test_empty(self):
        selector = ScoreModelSelector(
            execution_cost=0.01,
            scorer=scorer,
            score_threshold=0.0,
        )

        df = pd.DataFrame(
            [],
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
            ['model1', 'owner1'],
            ['model2', 'owner2'],
        ], columns=['model_id', 'owner']).set_index('model_id')

        random.seed(1)  # simanneal depends random.random

        params = create_model_selection_params(
            df=df,
            df_current=df_current,
            df_market=df_market,
            execution_start_ats=[1, 2],
            symbols=['BTC', 'ETH'],
        )

        df_weight = selector.select_model(params)

        expected = pd.DataFrame(
            [], columns=['model_id', 'weight']).set_index('model_id')
        expected['weight'] = expected['weight'].astype(float)

        assert_frame_equal(df_weight, expected)

        receivers = selector.select_receivers(params)
        self.assertEqual(receivers.shape[0], 0)

    def test_default_scorer_smoke(self):
        default_scorer(np.array([-1, 0, 1]))
        

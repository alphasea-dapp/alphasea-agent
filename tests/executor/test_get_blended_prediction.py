import pandas as pd
from pandas.testing import assert_frame_equal
from unittest.mock import MagicMock
from ..helpers import (
    create_web3,
    create_contract,
    get_future_execution_start_at_timestamp,
    proceed_time,
    get_prediction_time_shift,
    get_purchase_time_shift,
    get_shipping_time_shift,
    get_publication_time_shift,
    get_tournament_id,
    create_store,
    create_event_indexer,
    create_redis_client,
    BaseHardhatTestCase
)
from src.executor.executor import Executor
from src.model_selection.all_model_selector import AllModelSelector

execution_start_at = get_future_execution_start_at_timestamp()
content = b"""position,symbol
0.5,BTC"""
model_id = 'model1'
evaluation_periods = 5


class TestExecutorGetBlendedPrediction(BaseHardhatTestCase):
    def setUp(self):
        super().setUp()

        w3 = create_web3()
        contract = create_contract(w3)
        store = create_store(w3, contract)

        df_market = pd.DataFrame(
            [],
            columns=['execution_start_at', 'symbol', 'ret']
        ).set_index(['execution_start_at', 'symbol'])
        market_data_store = MagicMock()
        market_data_store.fetch_df_market.return_value = df_market

        executor_time = None
        executor = Executor(
            store=store,
            tournament_id=get_tournament_id(),
            time_func=lambda: executor_time,
            evaluation_periods=evaluation_periods,
            model_selector=AllModelSelector(),
            market_data_store=market_data_store,
            symbol_white_list=['BTC'],
            budget_rate=0.1,
            redis_client=create_redis_client(),
        )
        executor._initialize()
        self.executor = executor

        # predict
        proceed_time(w3, execution_start_at + get_prediction_time_shift())
        store.create_models_if_not_exist([dict(
            model_id=model_id,
            tournament_id=get_tournament_id(),
            prediction_license='CC0-1.0',
        )])
        store.create_predictions([dict(
            model_id=model_id,
            execution_start_at=execution_start_at,
            content=content,
            price=1,
        )])

        buffer_time = 4 * 60
        executor_time = execution_start_at + get_purchase_time_shift() + buffer_time
        proceed_time(w3, executor_time)
        executor._step()

    def test_ok(self):
        df = self.executor._get_blended_prediction(
            execution_start_at=execution_start_at
        )

        expected = pd.DataFrame([
            ['BTC', 0.5],
        ], columns=['symbol', 'position']).set_index('symbol')

        assert_frame_equal(df, expected)

    def test_different_execution_start_at(self):
        df = self.executor._get_blended_prediction(
            execution_start_at=execution_start_at + 1
        )

        expected = pd.DataFrame(
            [],
            columns=['symbol', 'position']
        ).set_index('symbol')

        assert_frame_equal(df, expected)

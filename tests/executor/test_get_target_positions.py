import pandas as pd
from pandas.testing import assert_frame_equal
from unittest.mock import MagicMock
from ..helpers import (
    create_web3,
    create_contract,
    get_future_execution_start_at_timestamp,
    proceed_time,
    get_prediction_time_shift,
    get_sending_time_shift,
    get_preparation_time_shift,
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
0.12,BTC"""
model_id = 'model1'
evaluation_periods = 5
day_seconds = 24 * 60 * 60

class TestExecutorGetTargetPositions(BaseHardhatTestCase):
    def setUp(self):
        super().setUp()

        w3 = create_web3()
        contract = create_contract(w3)
        store = create_store(w3, contract)
        self.execution_time = store.fetch_tournament(get_tournament_id())['execution_time']

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
        )])

        buffer_time = 4 * 60
        executor_time = execution_start_at + get_preparation_time_shift() + buffer_time
        proceed_time(w3, executor_time)

    def test_start_entry(self):
        df = self.executor.get_target_positions(
            timestamp=execution_start_at
        )

        expected = pd.DataFrame([
            ['BTC', 0.0],
        ], columns=['symbol', 'position']).set_index('symbol')

        assert_frame_equal(df, expected)

    def test_finish_entry(self):
        df = self.executor.get_target_positions(
            timestamp=execution_start_at + self.execution_time
        )

        expected = pd.DataFrame([
            ['BTC', 0.01],
        ], columns=['symbol', 'position']).set_index('symbol')

        assert_frame_equal(df, expected)

    def test_start_exit(self):
        df = self.executor.get_target_positions(
            timestamp=execution_start_at + day_seconds
        )

        expected = pd.DataFrame([
            ['BTC', 0.01],
        ], columns=['symbol', 'position']).set_index('symbol')

        assert_frame_equal(df, expected)

    def test_finish_exit(self):
        df = self.executor.get_target_positions(
            timestamp=execution_start_at + day_seconds + self.execution_time
        )

        expected = pd.DataFrame([
        ], columns=['symbol', 'position']).set_index('symbol')
        expected['position'] = expected['position'].astype(float)

        assert_frame_equal(df, expected)

    def test_empty(self):
        df = self.executor.get_target_positions(
            timestamp=execution_start_at + 2 * day_seconds
        )

        expected = pd.DataFrame([
        ], columns=['symbol', 'position']).set_index('symbol')
        expected['position'] = expected['position'].astype(float)

        assert_frame_equal(df, expected)

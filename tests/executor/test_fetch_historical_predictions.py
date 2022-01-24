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
from src.executor.utils import fetch_historical_predictions
from src.logger import create_null_logger

content = b"""position,symbol
0.5,BTC"""
invalid_content = b'invalid'
invalid_day = 4
model_id = 'model1'
evaluation_periods = 5
day_seconds = 24 * 60 * 60


class TestExecutorFetchHistoricalPredictions(BaseHardhatTestCase):
    def setUp(self):
        super().setUp()

        w3 = create_web3()
        contract = create_contract(w3)
        store = create_store(w3, contract)
        self.store = store
        self.w3 = w3

        store.create_models_if_not_exist([dict(
            model_id=model_id,
            tournament_id=get_tournament_id(),
            prediction_license='CC0-1.0',
        )])

        execution_start_at = get_future_execution_start_at_timestamp()

        days = evaluation_periods + 2
        for i in range(days):
            execution_start_at += day_seconds

            # predict
            proceed_time(w3, execution_start_at + get_prediction_time_shift())
            store.create_predictions([dict(
                model_id=model_id,
                execution_start_at=execution_start_at,
                content=invalid_content if days - 1 - i == invalid_day else content,
                price=1
            )])

            if i == days - 1:
                break

            # publication
            if i > 0:
                proceed_time(w3, execution_start_at - day_seconds + get_publication_time_shift())
                store.publish_predictions([dict(
                    model_id=model_id,
                    execution_start_at=execution_start_at - day_seconds,
                )])

        self.execution_start_at = execution_start_at

    def test_ok(self):
        execution_start_at = self.execution_start_at

        df = fetch_historical_predictions(
            store=self.store,
            tournament_id=get_tournament_id(),
            execution_start_at=execution_start_at,
            evaluation_periods=evaluation_periods,
            logger=create_null_logger(),
        )

        expected = pd.DataFrame([
            [model_id, execution_start_at - 6 * day_seconds, 'BTC', 0.5],
            [model_id, execution_start_at - 5 * day_seconds, 'BTC', 0.5],
            # day 4 is invalid
            [model_id, execution_start_at - 3 * day_seconds, 'BTC', 0.5],
            [model_id, execution_start_at - 2 * day_seconds, 'BTC', 0.5],
        ], columns=['model_id', 'execution_start_at', 'symbol', 'position']
        ).set_index(['model_id', 'execution_start_at', 'symbol'])

        assert_frame_equal(df, expected)

    def test_empty(self):
        df = fetch_historical_predictions(
            store=self.store,
            tournament_id=get_tournament_id(),
            execution_start_at=self.execution_start_at - evaluation_periods * day_seconds,
            evaluation_periods=evaluation_periods,
            logger=create_null_logger(),
        )

        expected = pd.DataFrame(
            [],
            columns=['model_id', 'execution_start_at', 'symbol', 'position']
        ).set_index(['model_id', 'execution_start_at', 'symbol'])

        assert_frame_equal(df, expected)

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
    get_publication_time_shift,
    get_tournament_id,
    create_store,
    create_event_indexer,
    create_redis_client,
    BaseHardhatTestCase
)
from src.executor.utils import fetch_current_predictions

execution_start_at = get_future_execution_start_at_timestamp()
content = 'abc'.encode()
model_id = 'model1'
model_id_other = 'model2'


class TestExecutorFetchCurrentPredictions(BaseHardhatTestCase):
    def setUp(self):
        super().setUp()

        w3 = create_web3()
        contract = create_contract(w3)
        store = create_store(w3, contract)
        self.store = store
        self.w3 = w3

        w3_other = create_web3(account_index=1)
        contract_other = create_contract(w3_other)
        store_other = create_store(w3_other, contract_other)
        self.store_other = store_other

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

        # other predict
        store_other.create_models_if_not_exist([dict(
            model_id=model_id_other,
            tournament_id=get_tournament_id(),
            prediction_license='CC0-1.0',
        )])
        store_other.create_predictions([dict(
            model_id=model_id_other,
            execution_start_at=execution_start_at,
            content=content,
        )])

    def test_ok(self):
        df_current = fetch_current_predictions(
            store=self.store,
            tournament_id=get_tournament_id(),
            execution_start_at=execution_start_at
        )

        expected = pd.DataFrame([
            [model_id, self.store.default_account_address(), content],
            [model_id_other, self.store_other.default_account_address(), None],
        ], columns=['model_id', 'owner', 'content']).set_index('model_id')

        assert_frame_equal(df_current, expected)

    def test_different_tournament_id(self):
        df_current = fetch_current_predictions(
            store=self.store,
            tournament_id='different',
            execution_start_at=execution_start_at
        )

        expected = pd.DataFrame(
            [],
            columns=['model_id', 'owner', 'content']
        ).set_index('model_id')

        assert_frame_equal(df_current, expected)

    def test_different_execution_start_at(self):
        df_current = fetch_current_predictions(
            store=self.store,
            tournament_id=get_tournament_id(),
            execution_start_at=execution_start_at + 1
        )

        expected = pd.DataFrame(
            [],
            columns=['model_id', 'owner', 'content']
        ).set_index('model_id')

        assert_frame_equal(df_current, expected)

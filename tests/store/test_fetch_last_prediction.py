from unittest import TestCase
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
    get_chain_id,
    create_store,
    BaseHardhatTestCase
)
from src.store.store import Store
from src.store.event_indexer import EventIndexer

execution_start_at = get_future_execution_start_at_timestamp()
execution_start_at2 = execution_start_at + 24 * 60 * 60
content = 'abc'.encode()
model_id = 'model1'


class TestStoreFetchLastPrediction(BaseHardhatTestCase):
    def setUp(self):
        super().setUp()

        w3 = create_web3()
        contract = create_contract(w3)
        store = create_store(w3, contract)
        self.store = store
        self.w3 = w3

        w3_purchaser = create_web3(account_index=1)
        contract_purchaser = create_contract(w3_purchaser)
        store_purchaser = create_store(w3_purchaser, contract_purchaser)
        self.store_purchaser = store_purchaser
        self.w3_purchaser = w3_purchaser

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

        proceed_time(w3, execution_start_at2 + get_prediction_time_shift())
        store.create_predictions([dict(
            model_id=model_id,
            execution_start_at=execution_start_at2,
            content=content,
            price=1,
        )])

    def test_ok(self):
        prediction = self.store.fetch_last_prediction(model_id=model_id, max_execution_start_at=execution_start_at)
        self.assertEqual(prediction, {
            **prediction,
            'model_id': model_id,
            'execution_start_at': execution_start_at,
            'content': content
        })

    def test_different_model_id(self):
        prediction = self.store.fetch_last_prediction(model_id='different', max_execution_start_at=execution_start_at)
        self.assertIsNone(prediction)

    def test_execution_start_at_different_hour(self):
        prediction = self.store.fetch_last_prediction(model_id=model_id,
                                                      max_execution_start_at=execution_start_at + 2 * 60 * 60)
        self.assertIsNone(prediction)

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
    generate_redis_namespace,
    BaseHardhatTestCase
)
from src.web3 import get_account_address

execution_start_at = get_future_execution_start_at_timestamp()
content = 'abc'.encode()
model_id = 'model1'
model_id_other = 'model_other'


class TestStoreFetchPredictionsToPublish(BaseHardhatTestCase):
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
            price=1,
        )])

    def test_ok(self):
        store = self.store

        predictions = store.fetch_predictions_to_publish(
            tournament_id=get_tournament_id(),
            execution_start_at=execution_start_at
        )
        self.assertEqual(predictions, [{
            **predictions[0],
            'model_id': model_id,
            'execution_start_at': execution_start_at,
            'content': content,
        }])

    def test_different_tournament_id(self):
        store = self.store

        predictions = store.fetch_predictions_to_publish(
            tournament_id='different',
            execution_start_at=execution_start_at
        )
        self.assertEqual(predictions, [])

    def test_execution_start_at(self):
        store = self.store

        predictions = store.fetch_predictions_to_publish(
            tournament_id=get_tournament_id(),
            execution_start_at=execution_start_at + 1,
        )
        self.assertEqual(predictions, [])

    def test_already_published(self):
        store = self.store

        proceed_time(self.w3, execution_start_at + get_publication_time_shift())
        store.publish_predictions([dict(
            model_id=model_id,
            execution_start_at=execution_start_at,
        )])

        predictions = store.fetch_predictions_to_publish(
            tournament_id=get_tournament_id(),
            execution_start_at=execution_start_at,
        )
        self.assertEqual(predictions, [])

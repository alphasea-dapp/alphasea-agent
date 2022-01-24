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


class TestStoreFetchPredictions(BaseHardhatTestCase):
    def setUp(self):
        super().setUp()

        redis_namespace = generate_redis_namespace()

        w3 = create_web3()
        contract = create_contract(w3)
        store = create_store(w3, contract, redis_namespace=redis_namespace)
        self.store = store
        self.w3 = w3

        w3_recreate = create_web3()
        contract_recreate = create_contract(w3_recreate)
        self.store_recreate = create_store(w3_recreate, contract_recreate, redis_namespace=redis_namespace)

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

    def test_locally_stored(self):
        store = self.store

        predictions = store.fetch_predictions(
            tournament_id=get_tournament_id(),
            execution_start_at=execution_start_at
        )
        self.assertEqual(predictions, [{
            **predictions[0],
            'model_id': model_id,
            'execution_start_at': execution_start_at,
            'content': content,
        }])

    def test_locally_stored_recreate(self):
        predictions = self.store_recreate.fetch_predictions(
            tournament_id=get_tournament_id(),
            execution_start_at=execution_start_at
        )
        self.assertEqual(predictions, [{
            **predictions[0],
            'model_id': model_id,
            'execution_start_at': execution_start_at,
            'content': content,
        }])

    def test_not_locally_stored(self):
        predictions = self.store_purchaser.fetch_predictions(
            tournament_id=get_tournament_id(),
            execution_start_at=execution_start_at
        )
        self.assertEqual(predictions, [{
            **predictions[0],
            'model_id': model_id,
            'execution_start_at': execution_start_at,
            'content': None,
        }])

    def test_shipped(self):
        store = self.store
        store_purchaser = self.store_purchaser

        proceed_time(self.w3, execution_start_at + get_purchase_time_shift())
        store_purchaser.create_purchases([dict(
            model_id=model_id,
            execution_start_at=execution_start_at,
        )])

        proceed_time(self.w3, execution_start_at + get_shipping_time_shift())
        store.ship_purchases([dict(
            model_id=model_id,
            execution_start_at=execution_start_at,
            purchaser=get_account_address(self.w3_purchaser.eth.default_account),
        )])

        predictions = store_purchaser.fetch_predictions(
            tournament_id=get_tournament_id(),
            execution_start_at=execution_start_at
        )
        self.assertEqual(predictions, [{
            **predictions[0],
            'model_id': model_id,
            'execution_start_at': execution_start_at,
            'content': content
        }])

    def test_published(self):
        store = self.store
        store_purchaser = self.store_purchaser

        proceed_time(self.w3, execution_start_at + get_publication_time_shift())
        store.publish_predictions([dict(
            model_id=model_id,
            execution_start_at=execution_start_at,
        )])

        predictions = store_purchaser.fetch_predictions(
            tournament_id=get_tournament_id(),
            execution_start_at=execution_start_at
        )
        self.assertEqual(predictions, [{
            **predictions[0],
            'model_id': model_id,
            'execution_start_at': execution_start_at,
            'content': content
        }])

    def test_different_tournamend_id(self):
        store = self.store
        predictions = store.fetch_predictions(
            tournament_id='not_found',
            execution_start_at=execution_start_at
        )
        self.assertEqual(predictions, [])

    def test_different_execution_start_at(self):
        store = self.store

        predictions = store.fetch_predictions(
            tournament_id=get_tournament_id(),
            execution_start_at=execution_start_at + 1,
        )
        self.assertEqual(predictions, [])

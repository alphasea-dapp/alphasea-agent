from unittest import TestCase
from unittest.mock import patch
from ..helpers import (
    create_web3,
    create_contract,
    get_future_execution_start_at_timestamp,
    proceed_time,
    get_prediction_time_shift,
    get_sending_time_shift,
    get_publication_time_shift,
    get_tournament_id,
    get_chain_id,
    create_store,
    generate_redis_namespace,
    BaseHardhatTestCase
)
from src.web3 import get_account_address
from src.store.event_indexer import EventIndexer

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

    def test_sent(self):
        store = self.store
        store_purchaser = self.store_purchaser

        proceed_time(self.w3, execution_start_at + get_sending_time_shift())
        store.send_prediction_keys(
            get_tournament_id(),
            execution_start_at,
            [store_purchaser.default_account_address()]
        )

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
        store.publish_prediction_key(
            get_tournament_id(),
            execution_start_at
        )

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

    def test_without_fetch_events(self):
        store = self.store

        # fetch events
        store.fetch_predictions(
            tournament_id=get_tournament_id(),
            execution_start_at=execution_start_at,
        )

        with patch.object(EventIndexer, '_fetch_events') as mocked_fetch_events:
            predictions = store.fetch_predictions(
                tournament_id=get_tournament_id(),
                execution_start_at=execution_start_at,
                without_fetch_events=True
            )
            mocked_fetch_events.assert_not_called()

        self.assertEqual(predictions, [{
            **predictions[0],
            'model_id': model_id,
            'execution_start_at': execution_start_at,
            'content': content,
        }])

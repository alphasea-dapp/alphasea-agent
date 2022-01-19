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
    BaseHardhatTestCase
)
from src.store.store import Store
from src.store.event_indexer import EventIndexer


class TestStoreFetchLastPrediction(BaseHardhatTestCase):
    def test_ok(self):
        w3 = create_web3()
        contract = create_contract(w3)
        store = Store(w3, contract, chain_id=get_chain_id())

        execution_start_at = get_future_execution_start_at_timestamp()
        content = 'abc'.encode()
        model_id = 'model1'

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

        prediction = store.fetch_last_prediction(model_id=model_id, max_execution_start_at=execution_start_at)
        self.assertEqual(prediction, {
            **prediction,
            'model_id': model_id,
            'execution_start_at': execution_start_at,
            'locally_stored': True
        })

        prediction = store.fetch_last_prediction(model_id=model_id, max_execution_start_at=execution_start_at - 1)
        self.assertIsNone(prediction)

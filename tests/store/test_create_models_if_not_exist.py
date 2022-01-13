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
    BaseHardhatTestCase
)
from src.store.store import Store
from src.store.event_indexer import EventIndexer


class TestStoreCreateModelsIfNotExist(BaseHardhatTestCase):
    def test_not_exist(self):
        w3 = create_web3()
        contract = create_contract(w3)
        store = Store(w3, contract)
        event_indexer = EventIndexer(w3, contract)

        store.create_models_if_not_exist([{
            'model_id': 'model1',
            'tournament_id': get_tournament_id(),
            'prediction_license': 'CC0-1.0',
        }])

        model = event_indexer.fetch_models(model_id='model1').iloc[0]
        self.assertEqual(model.to_dict(), {
            **model.to_dict(),
            'model_id': 'model1',
            'tournament_id': get_tournament_id(),
            'prediction_license': 'CC0-1.0',
        })

    def test_exist(self):
        w3 = create_web3()
        contract = create_contract(w3)
        store = Store(w3, contract)
        event_indexer = EventIndexer(w3, contract)

        store.create_models_if_not_exist([{
            'model_id': 'model1',
            'tournament_id': get_tournament_id(),
            'prediction_license': 'CC0-1.0',
        }])
        store.create_models_if_not_exist([{
            'model_id': 'model1',
            'tournament_id': get_tournament_id(),
            'prediction_license': 'CC0-1.0',
        }])

        model = event_indexer.fetch_models(model_id='model1').iloc[0]
        self.assertEqual(model.to_dict(), {
            **model.to_dict(),
            'model_id': 'model1',
            'tournament_id': get_tournament_id(),
            'prediction_license': 'CC0-1.0',
        })

    def test_empty(self):
        w3 = create_web3()
        contract = create_contract(w3)
        store = Store(w3, contract)
        result = store.create_models_if_not_exist([])
        self.assertEqual(result, {})

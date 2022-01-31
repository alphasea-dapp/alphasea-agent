from unittest import TestCase
from ..helpers import (
    create_web3,
    create_contract,
    get_future_execution_start_at_timestamp,
    proceed_time,
    get_prediction_time_shift,
    get_sending_time_shift,
    get_shipping_time_shift,
    get_publication_time_shift,
    get_tournament_id,
    get_chain_id,
    create_store,
    BaseHardhatTestCase
)
from src.store.store import Store
from src.store.event_indexer import EventIndexer


class TestStoreCreatePredictions(BaseHardhatTestCase):
    def test_empty(self):
        w3 = create_web3()
        contract = create_contract(w3)
        store = create_store(w3, contract)
        result = store.create_predictions([])
        self.assertEqual(result, {})

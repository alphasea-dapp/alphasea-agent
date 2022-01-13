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


class TestStorePublishPredictions(BaseHardhatTestCase):
    def test_empty(self):
        w3 = create_web3()
        contract = create_contract(w3)
        store = Store(w3, contract)
        result = store.publish_predictions([])
        self.assertEqual(result, {})

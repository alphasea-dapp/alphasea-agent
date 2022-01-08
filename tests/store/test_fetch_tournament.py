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


class TestStoreFetchTournament(BaseHardhatTestCase):
    def test_fetch_tournament(self):
        w3 = create_web3()
        contract = create_contract(w3)
        store = Store(w3, contract)

        tournament = store.fetch_tournament(get_tournament_id())

        self.assertEqual(tournament, {
            'tournament_id': 'crypto_daily',
            'execution_start_at': 60 * 60,
            'prediction_time': 15 * 60,
            'purchase_time': 15 * 60,
            'shipping_time': 15 * 60,
            'execution_preparation_time': 15 * 60,
            'execution_time': 60 * 60,
            'publication_time': 15 * 60,
            'description': 'https://github.com/alphasea-dapp/alphasea/tree/master/tournaments/crypto_daily.md',
        })

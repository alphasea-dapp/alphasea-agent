from unittest import TestCase
from web3 import Web3
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
from src.store.utils import get_wallet_private_key


class TestStoreLocalPrivateKey(BaseHardhatTestCase):
    def test_ok(self):
        w3 = create_web3()
        contract = create_contract(w3)
        store = Store(w3, contract, wallet_private_key=get_wallet_private_key())

        hash = Web3.sha3(hexstr=Web3.toHex(get_wallet_private_key()))
        address = Web3.toHex(hash[-20:])
        w3.hardhat.set_balance(address, 1 << 200)
        w3.default_account = address

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
            price=1
        )])

        # select purchase
        result = store.fetch_predictions(
            tournament_id=get_tournament_id(),
            execution_start_at=execution_start_at
        )
        self.assertEqual(result, [{
            **result[0],
            'model_id': model_id,
            'price': 1,
            'content': None,
        }])


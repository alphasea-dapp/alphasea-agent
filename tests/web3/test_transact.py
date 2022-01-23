from unittest import TestCase
from unittest.mock import MagicMock
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
from src.web3 import get_account_address, transact

model_id = 'model1'


class TestWeb3Transact(BaseHardhatTestCase):
    def test_ok(self):
        w3 = create_web3()
        contract = create_contract(w3)

        param_list = [
            {
                'modelId': model_id,
                'tournamentId': get_tournament_id(),
                'predictionLicense': 'CC0-1.0'
            }
        ]
        receipt = transact(
            contract.functions.createModels(param_list),
            {
                'from': get_account_address(w3.eth.default_account),
                'chainId': get_chain_id(),
            }
        )

        self.assertEqual(dict(receipt), {
            **dict(receipt),
            'status': 1,
        })

    def test_out_of_gas(self):
        w3 = create_web3()
        contract = create_contract(w3)

        param_list = [
            {
                'modelId': model_id,
                'tournamentId': get_tournament_id(),
                'predictionLicense': 'CC0-1.0'
            }
        ]

        with self.assertRaisesRegex(ValueError, 'Transaction ran out of gas'):
            transact(
                contract.functions.createModels(param_list),
                {
                    'from': get_account_address(w3.eth.default_account),
                    'chainId': get_chain_id(),
                    'gas': 30000,
                },
            )

    def test_gas_buffer_smoke(self):
        w3 = create_web3()
        contract = create_contract(w3)

        param_list = [
            {
                'modelId': model_id,
                'tournamentId': get_tournament_id(),
                'predictionLicense': 'CC0-1.0'
            }
        ]
        receipt = transact(
            contract.functions.createModels(param_list),
            {
                'from': get_account_address(w3.eth.default_account),
                'chainId': get_chain_id(),
            },
            gas_buffer=10000,
        )

        self.assertEqual(dict(receipt), {
            **dict(receipt),
            'status': 1,
        })

    def test_rate_limit_func_smoke(self):
        w3 = create_web3()
        contract = create_contract(w3)

        param_list = [
            {
                'modelId': model_id,
                'tournamentId': get_tournament_id(),
                'predictionLicense': 'CC0-1.0'
            }
        ]
        rate_limit_func = MagicMock()

        receipt = transact(
            contract.functions.createModels(param_list),
            {
                'from': get_account_address(w3.eth.default_account),
                'chainId': get_chain_id(),
            },
            rate_limit_func=rate_limit_func,
        )

        self.assertEqual(dict(receipt), {
            **dict(receipt),
            'status': 1,
        })
        rate_limit_func.assert_called()

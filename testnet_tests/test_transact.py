import os
import random
import string
from unittest import TestCase
from web3.eth import Account
from src.web3 import (
    create_w3,
    get_wallet_private_key,
    get_account_address,
    network_name_to_chain_id,
    transact,
)
from tests.helpers import (
    create_contract, get_tournament_id
)

network_name = 'mumbai'
contract_address = os.getenv('ALPHASEA_CONTRACT_ADDRESS')
chain_id = network_name_to_chain_id(network_name)

class TestWeb3Transact(TestCase):
    def setUp(self):
        self.w3 = create_w3(
            network_name=network_name,
            web3_provider_uri=os.getenv('WEB3_PROVIDER_URI'),
        )
        self.w3.eth.default_account = Account.from_key(get_wallet_private_key())
        self.contract = create_contract(
            self.w3,
            contract_address=contract_address,
        )
        self.model_id = 'test_' + ''.join(random.choices(string.ascii_lowercase, k=16))
        print(get_account_address(self.w3.eth.default_account))

    def test_ok(self):
        param_list = [
            {
                'modelId': self.model_id,
                'tournamentId': get_tournament_id(),
                'predictionLicense': 'CC0-1.0'
            }
        ]
        receipt = transact(
            self.contract.functions.createModels(param_list),
            {
                'from': get_account_address(self.w3.eth.default_account),
                'chainId': chain_id,
            }
        )

        self.assertEqual(dict(receipt), {
            **dict(receipt),
            'status': 1,
        })

    def test_out_of_gas(self):
        param_list = [
            {
                'modelId': self.model_id,
                'tournamentId': get_tournament_id(),
                'predictionLicense': 'CC0-1.0'
            }
        ]

        with self.assertRaisesRegex(Exception, 'transaction failed'):
            transact(
                self.contract.functions.createModels(param_list),
                {
                    'from': get_account_address(self.w3.eth.default_account),
                    'chainId': chain_id,
                    'gas': 30000,
                },
            )

    def test_gas_buffer_smoke(self):
        param_list = [
            {
                'modelId': self.model_id,
                'tournamentId': get_tournament_id(),
                'predictionLicense': 'CC0-1.0'
            }
        ]
        receipt = transact(
            self.contract.functions.createModels(param_list),
            {
                'from': get_account_address(self.w3.eth.default_account),
                'chainId': chain_id,
            },
            gas_buffer=10000,
        )

        self.assertEqual(dict(receipt), {
            **dict(receipt),
            'status': 1,
        })

    def test_max_priority_fee_scale(self):
        param_list = [
            {
                'modelId': self.model_id,
                'tournamentId': get_tournament_id(),
                'predictionLicense': 'CC0-1.0'
            }
        ]
        receipt = transact(
            self.contract.functions.createModels(param_list),
            {
                'from': get_account_address(self.w3.eth.default_account),
                'chainId': chain_id,
            },
            max_priority_fee_scale=1.2345,
        )

        self.assertEqual(dict(receipt), {
            **dict(receipt),
            'status': 1,
        })

    def test_gas_buffer_and_max_priority_fee_scale(self):
        param_list = [
            {
                'modelId': self.model_id,
                'tournamentId': get_tournament_id(),
                'predictionLicense': 'CC0-1.0'
            }
        ]
        receipt = transact(
            self.contract.functions.createModels(param_list),
            {
                'from': get_account_address(self.w3.eth.default_account),
                'chainId': chain_id,
            },
            gas_buffer=10000,
            max_priority_fee_scale=1.2345,
        )

        self.assertEqual(dict(receipt), {
            **dict(receipt),
            'status': 1,
        })


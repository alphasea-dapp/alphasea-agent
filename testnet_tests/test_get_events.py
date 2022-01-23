import os
from unittest import TestCase
from web3.eth import Account
from src.web3 import (
    create_w3,
    get_wallet_private_key,
    network_name_to_chain_id,
    get_events,
)
from tests.helpers import (
    create_contract
)

network_name = 'mumbai'
contract_address = os.getenv('ALPHASEA_CONTRACT_ADDRESS')
chain_id = network_name_to_chain_id(network_name)
start_block_number = int(os.getenv('ALPHASEA_START_BLOCK_NUMBER'))


class TestWeb3GetEvents(TestCase):
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

    def test_ok(self):
        events = get_events(
            contract=self.contract,
            from_block=start_block_number,
            to_block=start_block_number + 1000 - 1,
        )
        self.assertEqual(events[0]['event'], 'TournamentCreated')
        self.assertEqual(events[0]['args'], {
            **events[0]['args'],
            'executionStartAt': 30 * 60
        })

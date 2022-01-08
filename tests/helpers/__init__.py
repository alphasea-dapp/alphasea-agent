import os
from unittest import TestCase
from web3 import Web3
from web3._utils.module import attach_modules
from .hardhat_module import HardhatModule

class BaseHardhatTestCase(TestCase):
    def setUp(self):
        w3 = create_web3()
        self._snapshot_idx = w3.testing.snapshot()

    def tearDown(self):
        w3 = create_web3()
        w3.testing.revert(self._snapshot_idx)


def create_web3():
    external_modules = {
        'hardhat': (HardhatModule,)
    }
    w3 = Web3(Web3.HTTPProvider(os.getenv('WEB3_PROVIDER_URI')))
    attach_modules(w3, external_modules)
    return w3


def create_contract(w3):
    return w3.eth.contract(
        address=os.getenv('ALPHASEA_CONTRACT_ADDRESS'),
        abi=os.getenv('ALPHASEA_CONTRACT_ABI'),
    )


def get_tournament_id():
    return 'crypto_daily'


def proceed_time(w3, timestamp):
    w3.hardhat.set_next_block_timestamp(timestamp)
    w3.hardhat.mine()


def get_future_execution_start_at_timestamp():
    future_midnight = 2000073600
    return future_midnight + 60 * 60


def get_prediction_time_shift():
    return -55 * 60


def get_purchase_time_shift():
    return -40 * 60


def get_shipping_time_shift():
    return -25 * 60


def get_publication_time_shift():
    return 65 * 60

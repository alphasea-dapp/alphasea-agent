import os
from unittest import TestCase
from web3 import Web3
from web3._utils.module import attach_modules
from .hardhat_module import HardhatModule
from web3.eth import Account
from src.web3 import network_name_to_chain_id, get_hardhat_private_key
from redis_namespace import StrictRedis
from src.store.store import Store


class BaseHardhatTestCase(TestCase):
    def setUp(self):
        w3 = create_web3()
        self._snapshot_idx = w3.testing.snapshot()

    def tearDown(self):
        w3 = create_web3()
        w3.testing.revert(self._snapshot_idx)


def create_web3(account_index=0):
    external_modules = {
        'hardhat': (HardhatModule,)
    }
    w3 = Web3(Web3.HTTPProvider(os.getenv('WEB3_PROVIDER_URI')))
    attach_modules(w3, external_modules)
    w3.eth.default_account = Account.from_key(get_hardhat_private_key(account_index))

    return w3


def create_contract(w3):
    return w3.eth.contract(
        address=os.getenv('ALPHASEA_CONTRACT_ADDRESS'),
        abi=os.getenv('ALPHASEA_CONTRACT_ABI'),
    )


_namespace_idx = 1


def create_store(w3, contract, redis_namespace=None):
    global _namespace_idx
    redis_client = StrictRedis.from_url(
        os.getenv('REDIS_URL'),
        namespace='test_store{}:'.format(_namespace_idx) if redis_namespace is None else redis_namespace
    )
    _namespace_idx += 1
    return Store(
        w3, contract,
        chain_id=get_chain_id(),
        redis_client=redis_client
    )


def get_tournament_id():
    return 'crypto_daily_0030'


def proceed_time(w3, timestamp):
    w3.hardhat.set_next_block_timestamp(timestamp)
    w3.hardhat.mine()


def get_future_execution_start_at_timestamp():
    future_midnight = 2000073600
    return future_midnight + 30 * 60


def get_prediction_time_shift():
    return -30 * 60


def get_purchase_time_shift():
    return -22 * 60


def get_shipping_time_shift():
    return -14 * 60


def get_publication_time_shift():
    return 24 * 60 * 60 + 2 * 60 * 60


def get_chain_id():
    return network_name_to_chain_id('hardhat')

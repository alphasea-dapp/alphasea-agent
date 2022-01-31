import os
import random
import string
from unittest import TestCase
from web3 import Web3
from web3._utils.module import attach_modules
from .hardhat_module import HardhatModule
from src.web3 import network_name_to_chain_id
from redis_namespace import StrictRedis
from src.store.store import Store
from src.store.event_indexer import EventIndexer
from src.logger import create_logger


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
    w3.eth.default_account = w3.eth.accounts[account_index]

    return w3


def create_contract(w3, contract_address=None):
    return w3.eth.contract(
        address=os.getenv('ALPHASEA_CONTRACT_ADDRESS') if contract_address is None else contract_address,
        abi=os.getenv('ALPHASEA_CONTRACT_ABI'),
    )


def generate_redis_namespace():
    return 'test_' + ''.join(random.choices(string.ascii_lowercase, k=32))


def create_redis_client(namespace=None):
    if namespace is None:
        namespace = generate_redis_namespace()
    return StrictRedis.from_url(
        os.getenv('REDIS_URL'),
        namespace=namespace,
    )


def create_store(w3, contract, redis_namespace=None, network_name=None,
                 start_block_number=None):
    return Store(
        w3, contract,
        chain_id=get_chain_id(network_name=network_name),
        redis_client=create_redis_client(namespace=redis_namespace),
        logger=get_logger(),
        start_block_number=start_block_number,
    )


def create_event_indexer(w3, contract, start_block_number=None, logger=None,
                         redis_namespace=None, get_logs_limit=None):
    return EventIndexer(
        w3,
        contract,
        redis_client=create_redis_client(namespace=redis_namespace),
        logger=logger,
        start_block_number=start_block_number,
        get_logs_limit=get_logs_limit,
    )


def get_logger():
    return create_logger('debug')


def get_tournament_id():
    return 'crypto_daily'


def proceed_time(w3, timestamp):
    w3.hardhat.set_next_block_timestamp(timestamp)
    w3.hardhat.mine()


def get_future_execution_start_at_timestamp():
    future_midnight = 2000073600
    return future_midnight + 30 * 60


def get_prediction_time_shift():
    return -30 * 60

def get_sending_time_shift():
    return -22 * 60


def get_shipping_time_shift():
    return -14 * 60


def get_publication_time_shift():
    return 24 * 60 * 60 + 2 * 60 * 60


def get_chain_id(network_name=None):
    return network_name_to_chain_id('hardhat' if network_name is None else network_name)

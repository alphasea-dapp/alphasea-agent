from unittest import TestCase
from ..helpers import create_web3, get_future_execution_start_at_timestamp, BaseHardhatTestCase


class TestHardhatModule(BaseHardhatTestCase):
    # def test_reset(self):
    #     w3 = create_web3()
    #     w3.hardhat.reset()

    def test_set_next_block_timestamp(self):
        w3 = create_web3()
        w3.hardhat.set_next_block_timestamp(get_future_execution_start_at_timestamp())

    def test_mine(self):
        w3 = create_web3()
        w3.hardhat.mine()

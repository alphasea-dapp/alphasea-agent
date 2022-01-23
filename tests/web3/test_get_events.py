from unittest import TestCase
from unittest.mock import MagicMock
from ..helpers import (
    create_web3,
    create_contract,
    BaseHardhatTestCase
)
from src.web3 import get_events


class TestWeb3GetEvents(BaseHardhatTestCase):
    def test_ok(self):
        w3 = create_web3()
        contract = create_contract(w3)

        events = get_events(
            contract=contract,
            from_block=1,
            to_block=w3.eth.block_number,
        )
        self.assertEqual(events[0]['event'], 'TournamentCreated')
        self.assertEqual(events[0]['args'], {
            **events[0]['args'],
            'executionStartAt': 30 * 60
        })

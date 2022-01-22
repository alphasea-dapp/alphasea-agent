from ..helpers import (
    create_web3,
    create_contract,
    BaseHardhatTestCase
)
from src.agent import Agent


class TestAgent(BaseHardhatTestCase):
    def test_smoke(self):
        w3 = create_web3()
        contract = create_contract(w3)

        agent = Agent(
            w3=w3,
            contract=contract,
            logger=None
        )

        agent.initialize()
        agent.finalize()

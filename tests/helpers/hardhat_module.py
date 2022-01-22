from web3.module import Module, Method
from web3.types import RPCEndpoint
from web3.method import default_root_munger
from src.web3 import get_account_address

class HardhatModule(Module):

    # def reset(self):
    #     return self._hardhat_reset()

    def set_next_block_timestamp(self, timestamp):
        return self._evm_setNextBlockTimestamp(timestamp)

    def mine(self):
        return self._evm_mine()

    def set_balance(self, address, balance):
        return self._hardhat_setBalance(
            get_account_address(address),
            hex(balance)
        )

    _hardhat_reset = Method(RPCEndpoint("hardhat_reset"))

    _hardhat_setBalance = Method(
        RPCEndpoint("hardhat_setBalance"),
        mungers=[default_root_munger],
    )

    _evm_mine = Method(RPCEndpoint("evm_mine"))

    _evm_setNextBlockTimestamp = Method(
        RPCEndpoint("evm_setNextBlockTimestamp"),
        mungers=[default_root_munger],
    )

from web3.module import Module, Method
from web3.types import RPCEndpoint
from web3.method import default_root_munger


class HardhatModule(Module):

    def reset(self):
        return self._hardhat_reset()

    def set_next_block_timestamp(self, timestamp):
        return self._evm_setNextBlockTimestamp(timestamp)

    def mine(self):
        return self._evm_mine()


    _hardhat_reset = Method(RPCEndpoint("hardhat_reset"))

    _evm_mine = Method(RPCEndpoint("evm_mine"))

    _evm_setNextBlockTimestamp = Method(
        RPCEndpoint("evm_setNextBlockTimestamp"),
        mungers=[default_root_munger],
    )

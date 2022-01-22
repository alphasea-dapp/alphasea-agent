import os
from eth_keyfile import extract_key_from_keyfile
from web3 import Web3
from web3.middleware import geth_poa_middleware


def create_w3(network_name, web3_provider_uri):
    w3 = Web3(Web3.HTTPProvider(web3_provider_uri))

    if network_name in ['mumbai']:
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    return w3


def network_name_to_chain_id(name):
    return {
        'matic': 137,
        'mumbai': 80001,
        'hardhat': 31337,
    }[name]


def network_name_to_currency(name):
    return {
        'matic': 'MATIC',
        'mumbai': 'MATIC',
        'hardhat': 'ETH',
    }[name]


def _get_keyfile_path():
    path = os.path.join(os.path.dirname(__file__), '../../data/keystore')
    return os.path.join(path, sorted(os.listdir(path))[0])


def _get_wallet_password():
    path = os.path.join(os.path.dirname(__file__), '../../default_wallet_password')
    with open(path) as f:
        return f.read().strip()


def get_wallet_private_key():
    return extract_key_from_keyfile(
        _get_keyfile_path(),
        _get_wallet_password().encode()
    )


def get_account_address(account):
    if hasattr(account, 'address'):
        return account.address
    else:
        return account

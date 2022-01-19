import os
from eth_keyfile import extract_key_from_keyfile


def network_name_to_chain_id(name):
    return {
        'matic': 137,
        'mumbai': 80001,
        'hardhat': 31337,
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


def get_hardhat_private_key(account_index=0):
    hardhat_private_keys = [
        '0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80',
        '0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d'
    ]
    return hardhat_private_keys[account_index]

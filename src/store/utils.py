import os
import stringcase
from eth_keyfile import extract_key_from_keyfile


def convert_keys_to_snake_case(x: dict):
    return {stringcase.snakecase(key): x[key] for key in x}


def _get_keyfile_path():
    path = os.path.join(os.path.dirname(__file__), '../../data/keystore')
    return os.path.join(path, sorted(os.listdir(path))[0])


def get_wallet_private_key():
    return extract_key_from_keyfile(
        _get_keyfile_path(),
        os.getenv('ALPHASEA_WALLET_PASSWORD').encode()
    )

import os
import time
from eth_keyfile import extract_key_from_keyfile
from web3 import Web3
from web3.middleware import geth_poa_middleware
from web3.exceptions import (
    MismatchedABI,
)
from web3._utils.events import get_event_data


def create_w3(network_name, web3_provider_uri):
    w3 = Web3(Web3.HTTPProvider(web3_provider_uri))

    if network_name in ['mumbai', 'polygon']:
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    return w3


def network_name_to_chain_id(name):
    return {
        'polygon': 137,
        'mumbai': 80001,
        'hardhat': 31337,
    }[name]


def network_name_to_currency(name):
    return {
        'polygon': 'MATIC',
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


def transact(func, options, rate_limit_func=None, gas_buffer=None):
    w3 = func.web3
    default_account = w3.eth.default_account

    if rate_limit_func is None:
        rate_limit_func = lambda: ...

    rate_limit_func()
    if hasattr(default_account, 'key'):
        # local private key (not work with hardhat https://github.com/nomiclabs/hardhat/issues/1664)
        nonce = w3.eth.get_transaction_count(get_account_address(default_account))
        tx = func.buildTransaction({**options, 'nonce': nonce})
        if gas_buffer is not None:
            tx = func.buildTransaction({
                **options,
                'nonce': nonce,
                'gas': w3.eth.estimate_gas(tx) + gas_buffer,
            })
        signed_tx = w3.eth.account.sign_transaction(tx, private_key=default_account.key)
        w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        tx_hash = signed_tx.hash
    else:
        # remote private key
        tx_hash = func.transact(options)

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    if receipt['status'] == 0:
        raise Exception('transaction failed {}'.format(dict(receipt)))

    # wait for block number
    rate_limit_func()
    while w3.eth.block_number < receipt['blockNumber']:
        time.sleep(1)
        rate_limit_func()

    return receipt


def get_events(contract, from_block, to_block):
    w3 = contract.web3

    logs = w3.eth.get_logs({
        "fromBlock": from_block,
        "toBlock": to_block,
        "address": contract.address,
        "topics": []
    })

    events = []

    for log in logs:
        for contract_event in contract.events:
            abi = contract_event._get_event_abi()

            try:
                ev = get_event_data(w3.codec, abi, log)
                events.append(ev)
            except MismatchedABI:
                ...

    events.sort(key=lambda x: x['blockNumber'])

    return events

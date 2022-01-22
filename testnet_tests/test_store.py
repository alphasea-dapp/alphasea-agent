from unittest import TestCase
import random
import string
import os
from web3.eth import Account
from src.web3 import create_w3, get_wallet_private_key, get_account_address
from src.store.event_indexer import EventIndexer
from tests.helpers import (
    create_contract, create_store, get_tournament_id, get_logger
)

network_name = 'mumbai'
start_block_number = int(os.getenv('ALPHASEA_START_BLOCK_NUMBER'))
contract_address = os.getenv('ALPHASEA_CONTRACT_ADDRESS')


class TestnetTestStoreCreateModelsIfNotExist(TestCase):
    def test_not_exist(self):
        w3 = create_w3(
            network_name=network_name,
            web3_provider_uri=os.getenv('WEB3_PROVIDER_URI'),
        )
        w3.eth.default_account = Account.from_key(get_wallet_private_key())
        print(get_account_address(w3.eth.default_account))

        contract = create_contract(
            w3,
            contract_address=contract_address,
        )
        store = create_store(
            w3, contract,
            network_name=network_name,
            start_block_number=start_block_number,
        )
        event_indexer = EventIndexer(
            w3, contract,
            start_block_number=start_block_number,
            logger=get_logger(),
        )

        model_id = 'test_' + ''.join(random.choices(string.ascii_lowercase, k=16))

        store.create_models_if_not_exist([{
            'model_id': model_id,
            'tournament_id': get_tournament_id(),
            'prediction_license': 'CC0-1.0',
        }])

        model = event_indexer.fetch_models(model_id=model_id).iloc[0]
        self.assertEqual(model.to_dict(), {
            **model.to_dict(),
            'model_id': model_id,
            'tournament_id': get_tournament_id(),
            'prediction_license': 'CC0-1.0',
        })

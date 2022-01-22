from unittest import TestCase
import pandas as pd
from ..helpers import (
    create_web3,
    create_contract,
    get_future_execution_start_at_timestamp,
    proceed_time,
    get_prediction_time_shift,
    get_purchase_time_shift,
    get_shipping_time_shift,
    get_publication_time_shift,
    get_tournament_id,
    get_chain_id,
    create_store,
    BaseHardhatTestCase
)
from src.store.store import Store
from src.web3 import get_account_address


class TestStoreIntegration(BaseHardhatTestCase):
    def test_integration(self):
        w3 = create_web3()
        contract = create_contract(w3)
        store = create_store(w3, contract)

        w3_purchaser = create_web3(account_index=1)
        contract_purhcaser = create_contract(w3_purchaser)
        store_purchaser = create_store(w3_purchaser, contract_purhcaser)

        execution_start_at = get_future_execution_start_at_timestamp()
        content = 'abc'.encode()
        model_id = 'model1'

        # predict
        proceed_time(w3, execution_start_at + get_prediction_time_shift())
        store.create_models_if_not_exist([dict(
            model_id=model_id,
            tournament_id=get_tournament_id(),
            prediction_license='CC0-1.0',
        )])
        store.create_predictions([dict(
            model_id=model_id,
            execution_start_at=execution_start_at,
            content=content,
            price=1
        )])

        # select purchase
        result = store_purchaser.fetch_predictions(
            tournament_id=get_tournament_id(),
            execution_start_at=execution_start_at
        )
        self.assertEqual(result, [{
            **result[0],
            'model_id': model_id,
            'price': 1,
            'content': None,
        }])

        # purchase
        proceed_time(w3, execution_start_at + get_purchase_time_shift())
        store_purchaser.create_purchases([dict(
            model_id=model_id,
            execution_start_at=execution_start_at,
        )])

        # select ship
        result = store.fetch_purchases_to_ship(
            tournament_id=get_tournament_id(),
            execution_start_at=execution_start_at
        )
        self.assertEqual(result, [{
            **result[0],
            'model_id': model_id,
            'execution_start_at': execution_start_at,
            'purchaser': w3_purchaser.eth.accounts[1],
        }])

        # shipping
        proceed_time(w3, execution_start_at + get_shipping_time_shift())
        store.ship_purchases([dict(
            model_id=model_id,
            execution_start_at=execution_start_at,
            purchaser=get_account_address(w3_purchaser.eth.default_account),
        )])

        # check shipped purchase
        result = store_purchaser.fetch_predictions(
            tournament_id=get_tournament_id(),
            execution_start_at=execution_start_at
        )
        result = [x for x in result if ~pd.isna(x['encrypted_content_key'])]
        self.assertEqual(result, [{
            **result[0],
            'model_id': model_id,
            'execution_start_at': execution_start_at,
            'content': content,
        }])

        # publication
        result = store.fetch_predictions_to_publish(
            tournament_id=get_tournament_id(),
            execution_start_at=execution_start_at,
        )
        self.assertEqual(result, [{
            **result[0],
            'model_id': model_id,
            'execution_start_at': execution_start_at,
        }])

        proceed_time(w3, execution_start_at + get_publication_time_shift())
        store.publish_predictions([dict(
            model_id=model_id,
            execution_start_at=execution_start_at,
        )])

        # check published prediction
        result = store.fetch_predictions(
            tournament_id=get_tournament_id(),
            execution_start_at=execution_start_at
        )
        self.assertEqual(result, [{
            **result[0],
            'model_id': model_id,
            'price': 1,
            'content': content,
        }])

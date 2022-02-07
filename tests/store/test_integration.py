from unittest import TestCase
import pandas as pd
from ..helpers import (
    create_web3,
    create_contract,
    get_future_execution_start_at_timestamp,
    proceed_time,
    get_prediction_time_shift,
    get_sending_time_shift,
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
        )])

        # select send
        result = store_purchaser.fetch_predictions(
            tournament_id=get_tournament_id(),
            execution_start_at=execution_start_at
        )
        self.assertEqual(result, [{
            **result[0],
            'model_id': model_id,
            'content': None,
        }])

        # send
        proceed_time(w3, execution_start_at + get_sending_time_shift())
        store.send_prediction_keys(
            get_tournament_id(),
            execution_start_at,
            [store_purchaser.default_account_address()],
        )

        # check if shipped
        result = store_purchaser.fetch_predictions(
            tournament_id=get_tournament_id(),
            execution_start_at=execution_start_at
        )
        self.assertEqual(result, [{
            **result[0],
            'model_id': model_id,
            'execution_start_at': execution_start_at,
            'content': content,
        }])

        # publication
        proceed_time(w3, execution_start_at + get_publication_time_shift())
        store.publish_prediction_key(
            get_tournament_id(),
            execution_start_at,
        )

        # check published prediction
        result = store.fetch_predictions(
            tournament_id=get_tournament_id(),
            execution_start_at=execution_start_at
        )
        self.assertEqual(result, [{
            **result[0],
            'model_id': model_id,
            'content': content,
        }])

from unittest import TestCase
import numpy as np
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
    BaseHardhatTestCase
)
from src.store.store import Store
from src.store.event_indexer import EventIndexer
from src.predictor.predictor import Predictor
from src.types.exceptions import ValidationError


class TestPredictorStep(BaseHardhatTestCase):
    def test_ok(self):
        w3 = create_web3()
        contract = create_contract(w3)
        store = Store(w3, contract, chain_id=get_chain_id())
        event_indexer = EventIndexer(w3, contract)
        predictor_time = None
        predictor = Predictor(
            store=store,
            tournament_id=get_tournament_id(),
            price_min=100,
            time_func=lambda: predictor_time,
        )

        model_id = 'model1'
        execution_start_at = get_future_execution_start_at_timestamp()
        content = b"""position,symbol
0.1,BTC"""
        buffer_time = 1 * 60

        predictor.submit_prediction(
            model_id=model_id,
            execution_start_at=execution_start_at,
            prediction_license='CC0-1.0',
            content=content
        )

        # predict
        predictor_time = execution_start_at + get_prediction_time_shift() + buffer_time
        proceed_time(w3, predictor_time)
        predictor._step()

        predictions = event_indexer.fetch_predictions()
        self.assertEqual(predictions.iloc[0].to_dict(), {
            **predictions.iloc[0].to_dict(),
            'model_id': 'model1',
            'execution_start_at': execution_start_at,
        })
        self.assertTrue(pd.isna(predictions.iloc[0]['content_key']))

        # purchase
        w3_purchaser = create_web3(account_index=1)
        contract_purhcaser = create_contract(w3_purchaser)
        store_purchaser = Store(w3_purchaser, contract_purhcaser, chain_id=get_chain_id())

        proceed_time(w3, execution_start_at + get_purchase_time_shift())
        store_purchaser.create_purchases([dict(
            model_id=model_id,
            execution_start_at=execution_start_at,
        )])
        purchases = event_indexer.fetch_purchases()
        self.assertTrue(pd.isna(purchases.iloc[0]['encrypted_content_key']))

        # shipping
        predictor_time = execution_start_at + get_shipping_time_shift() + buffer_time
        proceed_time(w3, predictor_time)
        predictor._step()

        purchases = event_indexer.fetch_purchases()
        self.assertFalse(pd.isna(purchases.iloc[0]['encrypted_content_key']))

        # publication
        predictor_time = execution_start_at + get_publication_time_shift() + buffer_time
        proceed_time(w3, predictor_time)
        predictor._step()

        predictions = event_indexer.fetch_predictions()
        self.assertFalse(pd.isna(predictions.iloc[0]['content_key']))

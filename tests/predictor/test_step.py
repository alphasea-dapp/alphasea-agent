from unittest import TestCase
import numpy as np
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
    create_event_indexer,
    BaseHardhatTestCase
)
from src.predictor.predictor import Predictor


class TestPredictorStep(BaseHardhatTestCase):
    def test_ok(self):
        w3 = create_web3()
        contract = create_contract(w3)
        store = create_store(w3, contract)
        event_indexer = create_event_indexer(w3, contract)
        predictor_time = None
        predictor = Predictor(
            store=store,
            tournament_id=get_tournament_id(),
            time_func=lambda: predictor_time,
        )

        model_id = 'model1'
        execution_start_at = get_future_execution_start_at_timestamp()
        content = b"""position,symbol
0.1,BTC"""
        buffer_time = 6 * 60

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
        self.assertEqual(event_indexer.fetch_prediction_key_publications().shape[0], 0)

        # publication
        predictor_time = execution_start_at + get_publication_time_shift() + buffer_time
        proceed_time(w3, predictor_time)
        predictor._step()

        self.assertEqual(event_indexer.fetch_prediction_key_publications().shape[0], 1)

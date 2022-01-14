from unittest import TestCase
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
    BaseHardhatTestCase
)
from src.store.store import Store
from src.store.event_indexer import EventIndexer
from src.predictor.predictor import Predictor
from src.types.exceptions import ValidationError


class TestPredictorSubmitPrediction(BaseHardhatTestCase):
    def test_ok(self):
        w3 = create_web3()
        contract = create_contract(w3)
        store = Store(w3, contract)
        predictor = Predictor(
            store=store,
            tournament_id=get_tournament_id(),
        )

        model_id = 'model1'
        execution_start_at = get_future_execution_start_at_timestamp()
        content = b"""position,symbol
0.2,ETH
0.3,XRP
0.1,BTC"""

        normalized_content = b"""symbol,position
BTC,0.1
ETH,0.2
XRP,0.3"""

        predictor.submit_prediction(
            model_id=model_id,
            execution_start_at=execution_start_at,
            prediction_license='CC0-1.0',
            content=content
        )

        self.assertEqual(predictor._predictions[model_id][execution_start_at], {
            'prediction_license': 'CC0-1.0',
            'content': normalized_content
        })

    def test_validation_error(self):
        w3 = create_web3()
        contract = create_contract(w3)
        store = Store(w3, contract)
        predictor = Predictor(
            store=store,
            tournament_id=get_tournament_id(),
        )

        model_id = 'model1'
        execution_start_at = get_future_execution_start_at_timestamp()
        content = b'abc'

        with self.assertRaises(ValidationError):
            predictor.submit_prediction(
                model_id=model_id,
                execution_start_at=execution_start_at,
                prediction_license='CC0-1.0',
                content=content
            )

    def test_license_error(self):
        w3 = create_web3()
        contract = create_contract(w3)
        store = Store(w3, contract)
        predictor = Predictor(
            store=store,
            tournament_id=get_tournament_id(),
        )

        model_id = 'model1'
        execution_start_at = get_future_execution_start_at_timestamp()
        content = b"""position,symbol
0.1,BTC"""

        with self.assertRaisesRegex(Exception, 'prediction_license must be CC0-1.0'):
            predictor.submit_prediction(
                model_id=model_id,
                execution_start_at=execution_start_at,
                prediction_license='MIT',
                content=content
            )

    def test_execution_start_at_error(self):
        w3 = create_web3()
        contract = create_contract(w3)
        store = Store(w3, contract)
        predictor = Predictor(
            store=store,
            tournament_id=get_tournament_id(),
        )

        model_id = 'model1'
        content = b"""position,symbol
0.1,BTC"""

        with self.assertRaisesRegex(Exception, 'invalid execution_start_at'):
            predictor.submit_prediction(
                model_id=model_id,
                execution_start_at=1,
                prediction_license='CC0-1.0',
                content=content
            )

    def test_model_id_error(self):
        w3 = create_web3()
        contract = create_contract(w3)
        store = Store(w3, contract)
        predictor = Predictor(
            store=store,
            tournament_id=get_tournament_id(),
        )

        model_id = 'a'
        execution_start_at = get_future_execution_start_at_timestamp()
        content = b"""position,symbol
0.1,BTC"""

        with self.assertRaisesRegex(Exception, 'invalid model_id'):
            predictor.submit_prediction(
                model_id=model_id,
                execution_start_at=execution_start_at,
                prediction_license='CC0-1.0',
                content=content
            )

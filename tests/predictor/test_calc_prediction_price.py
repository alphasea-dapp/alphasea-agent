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
    get_chain_id,
    BaseHardhatTestCase
)
from src.store.store import Store
from src.store.event_indexer import EventIndexer
from src.predictor.predictor import Predictor
from src.types.exceptions import ValidationError

class TestPredictorCalcPredictionPrice(BaseHardhatTestCase):
    def test_no_prediction(self):
        w3 = create_web3()
        contract = create_contract(w3)
        store = Store(w3, contract, chain_id=get_chain_id())
        predictor = Predictor(
            store=store,
            price_min=100,
            price_increase_rate=0.1,
            price_decrease_rate=0.2,
        )

        model_id = 'model1'
        execution_start_at = get_future_execution_start_at_timestamp()
        day_seconds = 24 * 60 * 60

        # no prediction
        price = predictor._calc_prediction_price(model_id=model_id, execution_start_at=execution_start_at)
        self.assertEqual(price, 100)

    def test_not_purchased_prediction(self):
        w3 = create_web3()
        contract = create_contract(w3)
        store = Store(w3, contract, chain_id=get_chain_id())
        predictor = Predictor(
            store=store,
            price_min=100,
            price_increase_rate=0.1,
            price_decrease_rate=0.2,
        )

        model_id = 'model1'
        execution_start_at = get_future_execution_start_at_timestamp()
        day_seconds = 24 * 60 * 60
        content = b"""position,symbol
0.1,BTC"""

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
            price=1000,
        )])
        price = predictor._calc_prediction_price(model_id=model_id, execution_start_at=execution_start_at + day_seconds)
        self.assertEqual(price, 800)

    def test_not_purchased_prediction_min_price(self):
        w3 = create_web3()
        contract = create_contract(w3)
        store = Store(w3, contract, chain_id=get_chain_id())
        predictor = Predictor(
            store=store,
            price_min=100,
            price_increase_rate=0.1,
            price_decrease_rate=0.2,
        )

        model_id = 'model1'
        execution_start_at = get_future_execution_start_at_timestamp()
        day_seconds = 24 * 60 * 60
        content = b"""position,symbol
0.1,BTC"""

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
            price=100,
        )])
        price = predictor._calc_prediction_price(model_id=model_id, execution_start_at=execution_start_at + day_seconds)
        self.assertEqual(price, 100)

    def test_purchased_prediction(self):
        w3 = create_web3()
        contract = create_contract(w3)
        store = Store(w3, contract, chain_id=get_chain_id())

        w3_purchaser = create_web3(account_index=1)
        contract_purhcaser = create_contract(w3_purchaser)
        store_purchaser = Store(w3_purchaser, contract_purhcaser, chain_id=get_chain_id())

        predictor = Predictor(
            store=store,
            price_min=100,
            price_increase_rate=0.1,
            price_decrease_rate=0.2,
        )

        model_id = 'model1'
        execution_start_at = get_future_execution_start_at_timestamp()
        day_seconds = 24 * 60 * 60
        content = b"""position,symbol
0.1,BTC"""

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
            price=1000,
        )])

        proceed_time(w3, execution_start_at + get_purchase_time_shift())
        store_purchaser.create_purchases([dict(
            model_id=model_id,
            execution_start_at=execution_start_at,
        )])

        price = predictor._calc_prediction_price(model_id=model_id, execution_start_at=execution_start_at + day_seconds)
        self.assertEqual(price, 1100)



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


class TestStoreCreatePurchases(BaseHardhatTestCase):
    def test_two(self):
        w3 = create_web3()
        contract = create_contract(w3)
        store = Store(w3, contract)

        w3_purchaser = create_web3(account_index=1)
        contract_purhcaser = create_contract(w3_purchaser)
        store_purchaser = Store(w3_purchaser, contract_purhcaser)
        event_indexer_purchaser = EventIndexer(w3_purchaser, contract_purhcaser)

        execution_start_at = get_future_execution_start_at_timestamp()
        content = 'abc'.encode()
        model_id = 'model1'
        model_id2 = 'model2'

        # predict
        proceed_time(w3, execution_start_at + get_prediction_time_shift())
        store.create_models_if_not_exist([dict(
            model_id=model_id,
            tournament_id=get_tournament_id(),
            prediction_license='CC0-1.0',
        ), dict(
            model_id=model_id2,
            tournament_id=get_tournament_id(),
            prediction_license='CC0-1.0',
        )])
        store.create_predictions([dict(
            model_id=model_id,
            execution_start_at=execution_start_at,
            content=content,
            price=1 << 200 # test precision
        ), dict(
            model_id=model_id2,
            execution_start_at=execution_start_at,
            content=content,
            price=1 # test precision
        )])

        proceed_time(w3, execution_start_at + get_purchase_time_shift())
        w3_purchaser.hardhat.set_balance(w3_purchaser.eth.default_account, 1 << 210)
        result = store_purchaser.create_purchases([{
            'model_id': model_id,
            'execution_start_at': execution_start_at,
        }, {
            'model_id': model_id2,
            'execution_start_at': execution_start_at,
        }])
        self.assertEqual(result['sum_price'], (1 << 200) + 1)

        purchases = event_indexer_purchaser.fetch_purchases()
        self.assertEqual(purchases.iloc[0].to_dict(), {
            **purchases.iloc[0].to_dict(),
            'model_id': model_id,
        })
        self.assertEqual(purchases.iloc[1].to_dict(), {
            **purchases.iloc[1].to_dict(),
            'model_id': model_id2,
        })




from web3 import Web3
import threading
from collections import defaultdict
import pandas as pd
from nacl.public import PublicKey, PrivateKey, SealedBox
from nacl.secret import SecretBox
import nacl.utils
from .event_indexer import EventIndexer

# thread safe
# 暗号化などを隠蔽する
# 自分の予測は購入できないので、シミュレーションする
# インターフェースはsnakecase

class Store:
    def __init__(self, w3, contract):
        self._w3 = w3
        self._contract = contract
        self._lock = threading.Lock()
        self._private_key = PrivateKey.generate()
        self._predictions = defaultdict(dict)
        self._event_indexer = EventIndexer(w3, contract)

    # read

    def fetch_tournament(self, tournament_id: str):
        with self._lock:
            return self._event_indexer.fetch_tournaments(tournament_id=tournament_id).iloc[0].to_dict()

    # def fetch_last_prediction(self, model_id: str, max_execution_start_at: int):
    #     with self._lock:
    #         predictions = self._event_indexer.fetch_predictions(model_id=model_id)
    #         predictions = predictions[predictions['execution_start_at'] <= max_execution_start_at]
    #         if predictions.shape[0] == 0:
    #             return None
    #         prediction = predictions.iloc[-1]
    #
    #         purchases = self._event_indexer.fetch_purchases(
    #             model_id=prediction['model_id'],
    #             execution_start_at=prediction['execution_start_at'],
    #         )
    #
    #         return {
    #             **prediction.to_dict(),
    #             'purchase_count': purchases.shape[0],
    #         }

    def fetch_predictions(self, tournament_id: str, execution_start_at: int):
        with self._lock:
            models = self._event_indexer.fetch_models(tournament_id=tournament_id)
            predictions = self._event_indexer.fetch_predictions(
                execution_start_at=execution_start_at
            )
            predictions = predictions.loc[predictions['model_id'].isin(models['model_id'].unique())]

            results = []
            for idx, prediction in predictions.iterrows():
                if pd.isna(prediction['content_key']):
                    content = None
                else:
                    box = SecretBox(prediction['content_key'])
                    content = box.decrypt(prediction['encrypted_content'])

                results.append({
                    **prediction.to_dict(),
                    'content': content,
                })

            return results

    def fetch_predictions_to_publish(self, tournament_id: str, execution_start_at: int):
        with self._lock:
            models = self._event_indexer.fetch_models(
                tournament_id=tournament_id,
                owner=self._w3.eth.default_account
            )
            predictions = self._event_indexer.fetch_predictions(
                execution_start_at=execution_start_at
            )
            predictions = predictions.loc[predictions['model_id'].isin(models['model_id'].unique())]
            predictions = predictions.loc[predictions['content_key'].isna()]

            results = []
            for idx, prediction in predictions.iterrows():
                results.append(prediction.to_dict())

            return results

    def fetch_purchases_to_ship(self, tournament_id: str, execution_start_at: int):
        with self._lock:
            my_models = self._event_indexer.fetch_models(
                tournament_id=tournament_id, owner=self._w3.eth.default_account)
            purchases = self._event_indexer.fetch_purchases(execution_start_at=execution_start_at)
            purchases = purchases.loc[purchases['model_id'].isin(my_models['model_id'].unique())]
            purchases = purchases.loc[purchases['encrypted_content_key'].isna()]

            results = []
            for idx, purchase in purchases.iterrows():
                results.append(purchase.to_dict())
            return results

    def fetch_shipped_purchases(self, tournament_id: str, execution_start_at: int):
        with self._lock:
            models = self._event_indexer.fetch_models(tournament_id=tournament_id)
            purchases = self._event_indexer.fetch_purchases(
                execution_start_at=execution_start_at,
                purchaser=self._w3.eth.default_account,
            )
            purchases = purchases.loc[purchases['model_id'].isin(models['model_id'].unique())]
            purchases = purchases.loc[~purchases['encrypted_content_key'].isna()]

            predictions = self._event_indexer.fetch_predictions(
                execution_start_at=execution_start_at
            )
            purchases = purchases.merge(
                predictions[['model_id', 'execution_start_at', 'encrypted_content']],
                on=['model_id', 'execution_start_at'], how='left'
            )

            results = []
            for idx, purchase in purchases.iterrows():
                unseal_box = SealedBox(self._private_key)
                content_key = unseal_box.decrypt(purchase['encrypted_content_key'])

                box = SecretBox(content_key)
                content = box.decrypt(purchase['encrypted_content'])

                results.append({
                    **purchase.to_dict(),
                    'prediction_content': content,
                })
            return results

    # write

    def create_models_if_not_exist(self, params_list):
        with self._lock:
            params_list2 = []
            for params in params_list:
                model_id = params['model_id']
                tournament_id = params['tournament_id']
                prediction_license = params['prediction_license']

                models = self._event_indexer.fetch_models(model_id=model_id)
                if models.shape[0] > 0:
                    continue

                params_list2.append({
                    'modelId': model_id,
                    'tournamentId': tournament_id,
                    'predictionLicense': prediction_license
                })

            tx_hash = self._contract.functions.createModels(params_list2).transact()
            receipt = self._w3.eth.wait_for_transaction_receipt(tx_hash)
            return { 'receipt': dict(receipt) }

    def create_predictions(self, params_list):
        with self._lock:
            params_list2 = []
            for params in params_list:
                model_id = params['model_id']
                execution_start_at = params['execution_start_at']
                content = params['content']
                price = params['price']

                content_key_generator = nacl.utils.random(32)
                content_key = Web3.solidityKeccak(
                    ['bytes', 'string'],
                    [content_key_generator, model_id]
                )
                box = SecretBox(content_key)
                encrypted_content = box.encrypt(content)

                self._predictions[model_id][execution_start_at] = {
                    'content_key_generator': content_key_generator,
                    'content_key': content_key,
                }

                params_list2.append({
                    'modelId': model_id,
                    'executionStartAt': execution_start_at,
                    'encryptedContent': encrypted_content,
                    'price': price,
                })

            tx_hash = self._contract.functions.createPredictions(params_list2).transact()
            receipt = self._w3.eth.wait_for_transaction_receipt(tx_hash)
            return { 'receipt': dict(receipt) }

    def create_purchases(self, params_list):
        with self._lock:
            params_list2 = []
            sum_price = None
            for params in params_list:
                model_id = params['model_id']
                execution_start_at = params['execution_start_at']

                prediction = self._event_indexer.fetch_predictions(
                    model_id=model_id,
                    execution_start_at=execution_start_at,
                ).iloc[0]
                price = prediction['price']
                if sum_price is None:
                    sum_price = price
                else:
                    sum_price += price

                params_list2.append({
                    'modelId': model_id,
                    'executionStartAt': execution_start_at,
                    'publicKey': bytes(self._private_key.public_key),
                })

            tx_hash = self._contract.functions.createPurchases(
                params_list2
            ).transact({ 'value': sum_price })
            receipt = self._w3.eth.wait_for_transaction_receipt(tx_hash)
            return { 'receipt': dict(receipt), 'sum_price': sum_price }

    def ship_purchases(self, params_list):
        with self._lock:
            params_list2 = []
            for params in params_list:
                model_id = params['model_id']
                execution_start_at = params['execution_start_at']
                purchaser = params['purchaser']

                purchase = self._event_indexer.fetch_purchases(
                    model_id=model_id,
                    execution_start_at=execution_start_at,
                    purchaser=purchaser,
                ).iloc[0]

                content_key = self._predictions[model_id][execution_start_at]['content_key']

                sealed_box = SealedBox(PublicKey(purchase['public_key']))
                encrypted_content_key = sealed_box.encrypt(content_key)

                params_list2.append({
                    'modelId': model_id,
                    'executionStartAt': execution_start_at,
                    'purchaser': purchaser,
                    'encryptedContentKey': encrypted_content_key,
                })

            tx_hash = self._contract.functions.shipPurchases(params_list2).transact()
            receipt = self._w3.eth.wait_for_transaction_receipt(tx_hash)
            return { 'receipt': dict(receipt) }

    def publish_predictions(self, params_list):
        with self._lock:
            params_list2 = []
            for params in params_list:
                content_key_generator = self._predictions[params['model_id']][params['execution_start_at']]['content_key_generator']
                params_list2.append({
                    'modelId': params['model_id'],
                    'executionStartAt': params['execution_start_at'],
                    'contentKeyGenerator': content_key_generator,
                })

            tx_hash = self._contract.functions.publishPredictions(params_list2).transact()
            receipt = self._w3.eth.wait_for_transaction_receipt(tx_hash)
            return { 'receipt': dict(receipt) }

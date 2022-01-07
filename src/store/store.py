
from web3 import Web3
import threading
from collections import defaultdict
from nacl.public import PublicKey, PrivateKey, SealedBox
from nacl.secret import SecretBox
import nacl.utils
from .event_indexer import EventIndexer

# thread safe
# 暗号化などを隠蔽する
# 自分の予測は購入できないので、シミュレーションする

class Store:
    def __init__(self, w3, contract):
        self._w3 = w3
        self._contract = contract
        self._lock = threading.Lock()
        self._private_key = PrivateKey.generate()
        self._predictions = defaultdict(dict)
        self._event_indexer = EventIndexer(w3, contract)

    # read

    def fetch_predictions(self, tournament_id: str, execution_start_at: int):
        with self._lock:
            models = self._event_indexer.fetch_models(tournament_id=tournament_id)
            predictions = self._event_indexer.fetch_predictions(
                execution_start_at=execution_start_at
            )
            if models.shape[0] == 0:
                return []
            if predictions.shape[0] == 0:
                return []
            predictions = predictions.loc[predictions['modelId'].isin(models['modelId'].unique())]

            results = []
            for idx, prediction in predictions.iterrows():
                if 'contentKey' in predictions.columns and prediction['contentKey'] is not None:
                    box = SecretBox(prediction['contentKey'])
                    content = box.decrypt(prediction['encryptedContent'])
                else:
                    content = None

                results.append({
                    'model_id': prediction['modelId'],
                    'price': int(prediction['price']),
                    'content': content,
                })

            return results

    def fetch_purchases_to_ship(self, tournament_id: str, execution_start_at: int):
        with self._lock:
            my_models = self._event_indexer.fetch_models(
                tournament_id=tournament_id, owner=self._w3.eth.default_account)
            if my_models.shape[0] == 0:
                return []
            purchases = self._event_indexer.fetch_purchases(execution_start_at=execution_start_at)
            if purchases.shape[0] == 0:
                return []
            purchases = purchases.loc[purchases['modelId'].isin(my_models['modelId'].unique())]
            if 'encryptedContentKey' in purchases.columns:
                purchases = purchases.loc[purchases['encryptedContentKey'].isna()]

            results = []
            for idx, purchase in purchases.iterrows():
                results.append({
                    'model_id': purchase['modelId'],
                    'execution_start_at': purchase['executionStartAt'],
                    'purchaser': purchase['purchaser'],
                })
            return results

    def fetch_shipped_purchases(self, tournament_id: str, execution_start_at: int):
        with self._lock:
            models = self._event_indexer.fetch_models(tournament_id=tournament_id)
            purchases = self._event_indexer.fetch_purchases(
                execution_start_at=execution_start_at,
                purchaser=self._w3.eth.default_account,
            )
            if purchases.shape[0] == 0:
                return []
            purchases = purchases.loc[purchases['modelId'].isin(models['modelId'].unique())]
            if 'encryptedContentKey' not in purchases.columns:
                return []
            purchases = purchases.loc[~purchases['encryptedContentKey'].isna()]

            predictions = self._event_indexer.fetch_predictions(
                execution_start_at=execution_start_at
            )
            purchases = purchases.merge(
                predictions[['modelId', 'executionStartAt', 'encryptedContent']],
                on=['modelId', 'executionStartAt'], how='left'
            )

            results = []
            for idx, purchase in purchases.iterrows():
                unseal_box = SealedBox(self._private_key)
                content_key = unseal_box.decrypt(purchase['encryptedContentKey'])

                box = SecretBox(content_key)
                content = box.decrypt(purchase['encryptedContent'])

                results.append({
                    'model_id': purchase['modelId'],
                    'execution_start_at': purchase['executionStartAt'],
                    'purchaser': purchase['purchaser'],
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
                price = int(prediction['price'])
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
            return { 'receipt': dict(receipt) }

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

                sealed_box = SealedBox(PublicKey(purchase['publicKey']))
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

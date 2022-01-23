from web3 import Web3
import threading
import pandas as pd
from nacl.public import PublicKey, PrivateKey, SealedBox
from nacl.secret import SecretBox
import nacl.utils
import pickle
import time
from .event_indexer import EventIndexer
from ..logger import create_null_logger
from ..web3 import get_account_address, transact

# thread safe
# 暗号化などを隠蔽する
# 自分の予測は購入できないので、シミュレーションする
# インターフェースはsnakecase
# インターフェースのcontentはcontentのままで
# 復号化に失敗したcontentはNone

# 未実装 (不正を行うインセンティブが無いので)
# 現在の公開鍵で購入したものは公開鍵で復号
# それ以外はpublishされた共有鍵で復号
# (publishされたものとshipされたものが違う場合に対応するため)


def _prediction_info_key(model_id, execution_start_at):
    return 'prediction_info:{}:{}'.format(model_id, execution_start_at)


class Store:
    def __init__(self, w3, contract, chain_id, logger=None,
                 rate_limiter=None, start_block_number=None,
                 redis_client=None):
        self._w3 = w3
        self._contract = contract
        self._lock = threading.Lock()
        self._event_indexer = EventIndexer(
            w3, contract,
            logger=logger,
            rate_limiter=rate_limiter,
            start_block_number=start_block_number,
            redis_client=redis_client,
        )
        self._logger = create_null_logger() if logger is None else logger
        self._rate_limiter = rate_limiter
        self._redis_client = redis_client
        self._chain_id = chain_id

        private_key_key = 'private_key'
        private_key = self._redis_client.get(private_key_key)
        if private_key is None:
            self._private_key = PrivateKey.generate()
            self._redis_client.set(private_key_key, bytes(self._private_key))
        else:
            self._private_key = PrivateKey(private_key)

    # redis

    def _get_prediction_info(self, model_id, execution_start_at):
        key = _prediction_info_key(model_id, execution_start_at)
        value = self._redis_client.get(key)
        if value is None:
            return None
        return pickle.loads(value)

    def _set_prediction_info(self, model_id, execution_start_at, info):
        key = _prediction_info_key(model_id, execution_start_at)
        self._redis_client.set(key, pickle.dumps(info))
        self._redis_client.expireat(key, execution_start_at + 2 * 24 * 60 * 60)

    # read

    def get_balance(self):
        with self._lock:
            self._rate_limit()
            return self._w3.eth.get_balance(self._default_account_address())

    def fetch_tournament(self, tournament_id: str):
        with self._lock:
            return self._event_indexer.fetch_tournaments(tournament_id=tournament_id).iloc[0].to_dict()

    def fetch_last_prediction(self, model_id: str, max_execution_start_at: int):
        with self._lock:
            predictions = self._event_indexer.fetch_predictions(model_id=model_id)
            predictions = predictions[predictions['execution_start_at'] <= max_execution_start_at]
            predictions = predictions[predictions['execution_start_at'] % (24 * 60 * 60) == max_execution_start_at % (24 * 60 * 60)]
            if predictions.shape[0] == 0:
                return None
            return self._predictions_to_dict_list(predictions)[0]

    def fetch_predictions(self, tournament_id: str, execution_start_at: int):
        with self._lock:
            models = self._event_indexer.fetch_models(tournament_id=tournament_id)
            predictions = self._event_indexer.fetch_predictions(
                execution_start_at=execution_start_at
            )
            predictions = predictions.loc[predictions['model_id'].isin(models['model_id'].unique())]
            return self._predictions_to_dict_list(predictions)

    def fetch_predictions_to_publish(self, tournament_id: str, execution_start_at: int):
        with self._lock:
            models = self._event_indexer.fetch_models(
                tournament_id=tournament_id,
                owner=self._default_account_address(),
            )
            predictions = self._event_indexer.fetch_predictions(
                execution_start_at=execution_start_at
            )
            predictions = predictions.loc[predictions['model_id'].isin(models['model_id'].unique())]
            predictions = predictions.loc[predictions['content_key'].isna()]
            return self._predictions_to_dict_list(predictions)

    def fetch_purchases_to_ship(self, tournament_id: str, execution_start_at: int):
        with self._lock:
            my_models = self._event_indexer.fetch_models(
                tournament_id=tournament_id, owner=self._default_account_address())
            purchases = self._event_indexer.fetch_purchases(execution_start_at=execution_start_at)
            purchases = purchases.loc[purchases['model_id'].isin(my_models['model_id'].unique())]
            purchases = purchases.loc[purchases['encrypted_content_key'].isna()]

            results = []
            for idx, purchase in purchases.iterrows():
                results.append(purchase.to_dict())
            return results

    # write

    def create_models_if_not_exist(self, params_list):
        self._logger.debug('Store.create_models_if_not_exist called {}'.format(params_list))

        with self._lock:
            params_list2 = []
            for params in params_list:
                model_id = params['model_id']
                tournament_id = params['tournament_id']
                prediction_license = params['prediction_license']

                models = self._event_indexer.fetch_models(model_id=model_id)
                if models.shape[0] > 0:
                    self._logger.debug('Store.create_models_if_not_exist model({}) already exists. skipped'.format(model_id))
                    continue

                params_list2.append({
                    'modelId': model_id,
                    'tournamentId': tournament_id,
                    'predictionLicense': prediction_license
                })

            if len(params_list2) == 0:
                self._logger.debug('Store.create_models_if_not_exist no new models. skipped')
                return {}

            receipt = self._transact(
                self._contract.functions.createModels(params_list2),
                self._default_tx_options()
            )
            self._logger.debug('Store.create_models_if_not_exist done {} receipt {}'.format(params_list2, dict(receipt)))
            return {'receipt': dict(receipt)}

    def create_predictions(self, params_list):
        self._logger.debug('Store.create_predictions called {}'.format(params_list))

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

                self._set_prediction_info(
                    model_id=model_id,
                    execution_start_at=execution_start_at,
                    info={
                        'content_key_generator': content_key_generator,
                        'content_key': content_key,
                    }
                )

                params_list2.append({
                    'modelId': model_id,
                    'executionStartAt': execution_start_at,
                    'encryptedContent': encrypted_content,
                    'price': price,
                })

            if len(params_list2) == 0:
                return {}

            receipt = self._transact(
                self._contract.functions.createPredictions(params_list2),
                self._default_tx_options()
            )
            self._logger.debug('Store.create_predictions done {} receipt {}'.format(params_list2, dict(receipt)))
            return {'receipt': dict(receipt)}

    def create_purchases(self, params_list):
        self._logger.debug('Store.create_purchases called {}'.format(params_list))

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

            if len(params_list2) == 0:
                return {}

            receipt = self._transact(
                self._contract.functions.createPurchases(params_list2),
                {
                    **self._default_tx_options(),
                    'value': sum_price,
                }
            )
            self._logger.debug('Store.create_purchases done {} receipt {} sum_price {}'.format(params_list2, dict(receipt), sum_price))
            return {'receipt': dict(receipt), 'sum_price': sum_price}

    def ship_purchases(self, params_list):
        self._logger.debug('Store.ship_purchases called {}'.format(params_list))

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

                prediction_info = self._get_prediction_info(
                    model_id=model_id,
                    execution_start_at=execution_start_at
                )
                content_key = prediction_info['content_key']

                sealed_box = SealedBox(PublicKey(purchase['public_key']))
                encrypted_content_key = sealed_box.encrypt(content_key)

                params_list2.append({
                    'modelId': model_id,
                    'executionStartAt': execution_start_at,
                    'purchaser': purchaser,
                    'encryptedContentKey': encrypted_content_key,
                })

            if len(params_list2) == 0:
                return {}

            receipt = self._transact(
                self._contract.functions.shipPurchases(params_list2),
                self._default_tx_options()
            )
            self._logger.debug('Store.ship_purchases done {} receipt {}'.format(params_list2, dict(receipt)))
            return {'receipt': dict(receipt)}

    def publish_predictions(self, params_list):
        self._logger.debug('Store.publish_predictions called {}'.format(params_list))

        with self._lock:
            params_list2 = []
            for params in params_list:
                prediction_info = self._get_prediction_info(
                    model_id=params['model_id'],
                    execution_start_at=params['execution_start_at']
                )
                content_key_generator = prediction_info['content_key_generator']
                params_list2.append({
                    'modelId': params['model_id'],
                    'executionStartAt': params['execution_start_at'],
                    'contentKeyGenerator': content_key_generator,
                })

            if len(params_list2) == 0:
                return {}

            receipt = self._transact(
                self._contract.functions.publishPredictions(params_list2),
                self._default_tx_options()
            )
            self._logger.debug('Store.publish_predictions done {} receipt {}'.format(params_list2, dict(receipt)))
            return {'receipt': dict(receipt)}

    def _predictions_to_dict_list(self, predictions):
        predictions = predictions.copy()

        # 自分の予測はplaintextをくっつける
        predictions['locally_stored'] = False
        for idx in predictions.index:
            model_id = predictions.loc[idx, 'model_id']
            execution_start_at = predictions.loc[idx, 'execution_start_at']
            prediction_info = self._get_prediction_info(
                model_id=model_id,
                execution_start_at=execution_start_at
            )
            if prediction_info is not None:
                content_key = prediction_info['content_key']
                predictions.loc[idx, 'content_key'] = content_key
                predictions.loc[idx, 'locally_stored'] = True

        # ship済みであればplaintextをくっつける
        my_purchases = self._event_indexer.fetch_purchases(
            purchaser=self._default_account_address(),
            public_key=bytes(self._private_key.public_key),
        )
        my_purchases = my_purchases.loc[~my_purchases['encrypted_content_key'].isna()]
        predictions = predictions.merge(
            my_purchases[['model_id', 'execution_start_at', 'encrypted_content_key']],
            on=['model_id', 'execution_start_at'],
            how='left'
        )

        # 購入数を追加
        purchases = self._event_indexer.fetch_purchases()
        purchase_count = purchases.groupby(['model_id', 'execution_start_at'])['purchaser'].count()
        predictions = predictions.join(
            purchase_count.rename('purchase_count'),
            on=['model_id', 'execution_start_at'],
            how='left'
        )
        predictions['purchase_count'] = predictions['purchase_count'].fillna(0)

        results = []
        for _, prediction in predictions.iterrows():
            content = None
            if pd.isna(prediction['content_key']) and not pd.isna(prediction['encrypted_content_key']):
                unseal_box = SealedBox(self._private_key)
                prediction['content_key'] = unseal_box.decrypt(prediction['encrypted_content_key'])

            if not pd.isna(prediction['content_key']):
                box = SecretBox(prediction['content_key'])
                content = box.decrypt(prediction['encrypted_content'])

            results.append({
                **prediction.to_dict(),
                'content': content,
            })

        return results

    def _default_account_address(self):
        return get_account_address(self._w3.eth.default_account)

    def _default_tx_options(self):
        return {
            'from': self._default_account_address(),
            'chainId': self._chain_id,
        }

    def _rate_limit(self):
        if self._rate_limiter is not None:
            self._rate_limiter.rate_limit(tags=['default'])

    def _transact(self, func, options):
        return transact(
            func=func,
            options=options,
            rate_limit_func=self._rate_limit,
            gas_buffer=20000,
        )

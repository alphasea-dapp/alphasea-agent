from web3 import Web3
import threading
import pandas as pd
from nacl.public import PublicKey, PrivateKey, SealedBox
from nacl.secret import SecretBox
import nacl.utils
from nacl.exceptions import CryptoError
import pickle
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

class Store:
    def __init__(self, w3, contract, chain_id, logger=None,
                 rate_limiter=None, start_block_number=None,
                 redis_client=None, max_priority_fee_scale=None):
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
        self._max_priority_fee_scale = max_priority_fee_scale

        private_key_key = 'private_key'
        private_key = self._redis_client.get(private_key_key)
        if private_key is None:
            self._private_key = PrivateKey.generate()
            self._redis_client.set(private_key_key, bytes(self._private_key))
        else:
            self._private_key = PrivateKey(private_key)

        self._change_public_key()

    # redis

    def _prediction_key_info(self, tournament_id, execution_start_at, create=False):
        key = _prediction_key_info_key(tournament_id, execution_start_at)
        value = self._redis_client.get(key)

        if value is not None:
            return pickle.loads(value)

        if not create:
            return None

        content_key_generator = nacl.utils.random(32)
        info = {
            'content_key_generator': content_key_generator,
            'content_key': Web3.solidityKeccak(
                ['bytes', 'address'],
                [content_key_generator, self.default_account_address()]
            )
        }
        self._redis_client.set(key, pickle.dumps(info))
        self._redis_client.expireat(key, execution_start_at + 2 * 24 * 60 * 60)
        return info

    # read

    def get_balance(self):
        with self._lock:
            self._rate_limit()
            return self._w3.eth.get_balance(self.default_account_address())

    def fetch_tournament(self, tournament_id: str):
        with self._lock:
            return self._event_indexer.fetch_tournaments(tournament_id=tournament_id).iloc[0].to_dict()

    def fetch_predictions(self, tournament_id: str, execution_start_at: int, without_fetch_events: bool = False):
        with self._lock:
            models = self._event_indexer.fetch_models(
                tournament_id=tournament_id,
                without_fetch_events=without_fetch_events,
            )
            predictions = self._event_indexer.fetch_predictions(
                execution_start_at=execution_start_at,
                without_fetch_events=True,
            )
            predictions = predictions.loc[predictions['model_id'].isin(models['model_id'].unique())]
            return self._predictions_to_dict_list(predictions)

    # write

    def _change_public_key(self):
        current_public_key = bytes(self._private_key.public_key)

        public_keys = self._event_indexer.fetch_public_keys(owner=self.default_account_address())
        if public_keys.shape[0] > 0 and public_keys.iloc[0]['public_key'] == current_public_key:
            self._logger.debug('public_key not changed')
            return {}

        receipt = self._transact(
            self._contract.functions.changePublicKey(current_public_key),
            self._default_tx_options()
        )
        self._logger.debug(
            'Store.change_public_key done receipt {}'.format(dict(receipt)))
        return {'receipt': dict(receipt)}

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
                    self._logger.debug(
                        'Store.create_models_if_not_exist model({}) already exists. skipped'.format(model_id))
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
            self._logger.debug(
                'Store.create_models_if_not_exist done {} receipt {}'.format(params_list2, dict(receipt)))
            return {'receipt': dict(receipt)}

    def create_predictions(self, params_list):
        self._logger.debug('Store.create_predictions called {}'.format(params_list))

        with self._lock:
            params_list2 = []
            for params in params_list:
                model_id = params['model_id']
                execution_start_at = params['execution_start_at']
                content = params['content']

                models = self._event_indexer.fetch_models(model_id=model_id)
                tournament_id = models.iloc[0]['tournament_id']

                info = self._prediction_key_info(
                    tournament_id=tournament_id,
                    execution_start_at=execution_start_at,
                    create=True,
                )
                box = SecretBox(info['content_key'])
                encrypted_content = box.encrypt(content)

                params_list2.append({
                    'modelId': model_id,
                    'executionStartAt': execution_start_at,
                    'encryptedContent': encrypted_content,
                })

            if len(params_list2) == 0:
                return {}

            receipt = self._transact(
                self._contract.functions.createPredictions(params_list2),
                self._default_tx_options()
            )
            self._logger.debug('Store.create_predictions done {} receipt {}'.format(params_list2, dict(receipt)))
            return {'receipt': dict(receipt)}

    def send_prediction_keys(self, tournament_id, execution_start_at, receivers):
        self._logger.debug('Store.send_prediction_keys called {} {} {}'.format(tournament_id, execution_start_at, receivers))

        with self._lock:
            publications = self._event_indexer.fetch_prediction_key_publications(
                owner=self.default_account_address(),
                tournament_id=tournament_id,
                execution_start_at=execution_start_at
            )
            if publications.shape[0] > 0:
                self._logger.debug('send_prediction_keys skipped because already published')
                return {}

            prediction_info = self._prediction_key_info(
                tournament_id=tournament_id,
                execution_start_at=execution_start_at,
            )
            if prediction_info is None:
                self._logger.debug('send_prediction_keys skipped because prediction_info is None')
                return {}

            content_key = prediction_info['content_key']

            params_list2 = []
            for receiver in receivers:
                if receiver == self.default_account_address():
                    self._logger.debug('send_prediction_keys skipped because receiver is me')
                    continue

                public_keys = self._event_indexer.fetch_public_keys(
                    owner=receiver
                )
                if public_keys.shape[0] == 0:
                    self._logger.debug('send_prediction_keys skipped because public key empty')
                    continue

                sealed_box = SealedBox(PublicKey(public_keys.iloc[0]['public_key']))
                encrypted_content_key = sealed_box.encrypt(content_key)

                params_list2.append({
                    'receiver': receiver,
                    'encryptedContentKey': encrypted_content_key,
                })

            if len(params_list2) == 0:
                return {}

            receipt = self._transact(
                self._contract.functions.sendPredictionKeys(
                    tournament_id,
                    execution_start_at,
                    params_list2,
                ),
                self._default_tx_options()
            )
            self._logger.debug('Store.send_prediction_keys done {} receipt {}'.format(params_list2, dict(receipt)))
            return {'receipt': dict(receipt)}

    def publish_prediction_key(self, tournament_id: str, execution_start_at: int):
        self._logger.debug('Store.publish_prediction_key called {} {}'.format(tournament_id, execution_start_at))

        with self._lock:
            publications = self._event_indexer.fetch_prediction_key_publications(
                owner=self.default_account_address(),
                tournament_id=tournament_id,
                execution_start_at=execution_start_at,
            )
            if publications.shape[0] > 0:
                self._logger.debug('Store.publish_prediction_key skipped because already published.')
                return {}

            prediction_info = self._prediction_key_info(
                tournament_id=tournament_id,
                execution_start_at=execution_start_at,
            )
            if prediction_info is None:
                self._logger.debug('publish_prediction_key skipped because prediction_info is None')
                return {}

            models = self._event_indexer.fetch_models(
                owner=self.default_account_address(),
                tournament_id=tournament_id,
            )
            predictions = self._event_indexer.fetch_predictions(
                execution_start_at=execution_start_at,
            )
            if predictions[predictions['model_id'].isin(models['model_id'])].shape[0] == 0:
                self._logger.debug('publish_prediction_key skipped because no predictions')
                return {}

            receipt = self._transact(
                self._contract.functions.publishPredictionKey(
                    tournament_id,
                    execution_start_at,
                    prediction_info['content_key_generator']
                ),
                self._default_tx_options()
            )
            self._logger.debug('Store.publish_predictions done {} receipt {}'.format(prediction_info['content_key_generator'], dict(receipt)))
            return {'receipt': dict(receipt)}

    def _predictions_to_dict_list(self, predictions):
        predictions = predictions.copy()

        # modelをjoin
        models = self._event_indexer.fetch_models(
            without_fetch_events=True,
        )
        predictions = predictions.merge(
            models[['model_id', 'owner', 'tournament_id']],
            on=['model_id'],
            how='left'
        )

        # published prediction
        publications = self._event_indexer.fetch_prediction_key_publications(
            without_fetch_events=True,
        )
        predictions = predictions.merge(
            publications[['owner', 'tournament_id', 'execution_start_at', 'content_key']],
            on=['owner', 'tournament_id', 'execution_start_at'],
            how='left'
        )

        # 自分の予測はcontent_keyをくっつける
        for idx in predictions.loc[predictions['owner'] == self.default_account_address()].index:
            tournament_id = predictions.loc[idx, 'tournament_id']
            execution_start_at = predictions.loc[idx, 'execution_start_at']

            prediction_key_info = self._prediction_key_info(
                tournament_id=tournament_id,
                execution_start_at=execution_start_at
            )
            if prediction_key_info is None:
                continue

            content_key = prediction_key_info['content_key']
            predictions.loc[idx, 'content_key'] = content_key

        # sendされたものはcontent_keyをjoin
        sendings = self._event_indexer.fetch_prediction_key_sendings(
            receiver=self.default_account_address(),
            without_fetch_events=True,
        )
        predictions = predictions.merge(
            sendings[['owner', 'tournament_id', 'execution_start_at', 'encrypted_content_key']],
            on=['owner', 'tournament_id', 'execution_start_at'],
            how='left'
        )

        results = []
        for _, prediction in predictions.iterrows():
            content = None
            if pd.isna(prediction['content_key']) and not pd.isna(prediction['encrypted_content_key']):
                unseal_box = SealedBox(self._private_key)
                try:
                    prediction['content_key'] = unseal_box.decrypt(prediction['encrypted_content_key'])
                except CryptoError as e:
                    self._logger.warn('failed to decrypt encrypted_content_key. ignored {}'.format(e))

            if not pd.isna(prediction['content_key']):
                box = SecretBox(prediction['content_key'])
                try:
                    content = box.decrypt(prediction['encrypted_content'])
                except CryptoError as e:
                    self._logger.warn('failed to decrypt encrypted_content. ignored {}'.format(e))

            results.append({
                **prediction.to_dict(),
                'content': content,
            })

        return results

    def default_account_address(self):
        return get_account_address(self._w3.eth.default_account)

    def _default_tx_options(self):
        return {
            'from': self.default_account_address(),
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
            max_priority_fee_scale=self._max_priority_fee_scale
        )


def _prediction_key_info_key(tournament_id, execution_start_at):
    return 'prediction_key_info:{}:{}'.format(tournament_id, execution_start_at)

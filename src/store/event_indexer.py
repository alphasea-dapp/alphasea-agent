import pandas as pd
from .utils import convert_keys_to_snake_case
from ..logger import create_null_logger


# thegraphのようなことをする
# インターフェースはsnakecase

class EventIndexer:
    def __init__(self, w3, contract, logger=None, start_block_number=None, rate_limiter=None):
        self._w3 = w3
        self._contract = contract
        self._logger = create_null_logger() if logger is None else logger
        self._rate_limiter = rate_limiter

        self._event_names = [
            'TournamentCreated',
            'ModelCreated',
            'PredictionCreated',
            'PredictionPublished',
            'PurchaseCreated',
            'PurchaseShipped',
        ]

        self._last_block_number = 0 if start_block_number is None else start_block_number - 1
        self._get_logs_limit = 1000

        # pandasの仕様
        # ここで追加したカラムはappendで整数を追加したときにobjectになる
        # 追加しないとfloatになる

        self._tournaments = pd.DataFrame(columns=[
            'tournament_id',
            'description',
            'execution_preparation_time',
            'execution_start_at',
            'execution_time',
            'prediction_time',
            'publication_time',
            'purchase_time',
            'shipping_time'
        ])
        self._models = pd.DataFrame(columns=['model_id', 'tournament_id', 'owner'])
        self._predictions = pd.DataFrame(
            columns=['model_id', 'execution_start_at', 'price', 'content_key', 'encrypted_content'])
        self._purchases = pd.DataFrame(
            columns=['model_id', 'execution_start_at', 'purchaser', 'encrypted_content_key', 'public_key'])

    def fetch_tournaments(self, tournament_id: str = None):
        self._fetch_events()

        return _filter_df(self._tournaments, [
            ('tournament_id', tournament_id)
        ])

    def fetch_models(self, model_id: str = None, tournament_id: str = None, owner: str = None):
        self._fetch_events()

        return _filter_df(self._models, [
            ('model_id', model_id),
            ('tournament_id', tournament_id),
            ('owner', owner),
        ])

    def fetch_predictions(self, model_id: str = None, execution_start_at: int = None):
        self._fetch_events()

        return _filter_df(self._predictions, [
            ('model_id', model_id),
            ('execution_start_at', execution_start_at),
        ])

    def fetch_purchases(self, model_id: str = None, execution_start_at: int = None,
                        purchaser: str = None, public_key: bytes = None):
        self._fetch_events()

        return _filter_df(self._purchases, [
            ('model_id', model_id),
            ('execution_start_at', execution_start_at),
            ('purchaser', purchaser),
            ('public_key', public_key),
        ])

    def _fetch_events(self):
        while True:
            events = []

            to_block = min(self._last_block_number + self._get_logs_limit, self._w3.eth.block_number)
            if to_block <= self._last_block_number:
                return

            for event_name in self._event_names:
                if self._rate_limiter is not None:
                    self._rate_limiter.rate_limit(tags=['default'])
                events += getattr(self._contract.events, event_name).getLogs(
                    fromBlock=self._last_block_number + 1,
                    # fromBlock=1,
                    toBlock=to_block,
                )

            self._last_block_number = to_block
            self._logger.debug('EventIndexer._fetch_events to_block {}'.format(to_block))

            # print(events)

            events.sort(key=lambda x: x['blockNumber'])

            for event in events:
                self._process_event(event)

    def _process_event(self, event):
        event_name = event['event']
        args = convert_keys_to_snake_case(event['args'])

        if event_name == 'TournamentCreated':
            self._tournaments = self._tournaments.append(
                args,
                ignore_index=True,
            )
        elif event_name == 'ModelCreated':
            self._models = self._models.append(
                args,
                ignore_index=True,
            )
        elif event_name == 'PredictionCreated':
            self._predictions = self._predictions.append(
                args,
                ignore_index=True,
            )
        elif event_name == 'PredictionPublished':
            idx = self._predictions['model_id'] == args['model_id']
            idx &= self._predictions['execution_start_at'] == args['execution_start_at']
            self._predictions.loc[idx, 'content_key'] = args['content_key']
        elif event_name == 'PurchaseCreated':
            self._purchases = self._purchases.append(
                args,
                ignore_index=True,
            )
        elif event_name == 'PurchaseShipped':
            idx = self._purchases['model_id'] == args['model_id']
            idx &= self._purchases['execution_start_at'] == args['execution_start_at']
            idx &= self._purchases['purchaser'] == args['purchaser']
            self._purchases.loc[idx, 'encrypted_content_key'] = args['encrypted_content_key']


def _filter_df(df, conditions):
    for name, value in conditions:
        if value is not None:
            df = df.loc[df[name] == value]
    return df.copy()

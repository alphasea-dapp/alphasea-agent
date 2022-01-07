
from collections import defaultdict
import pandas as pd

# thegraphのようなことをする

class EventIndexer:
    def __init__(self, w3, contract):
        self._w3 = w3
        self._contract = contract

        self._event_names = [
            'ModelCreated',
            'PredictionCreated',
            'PredictionPublished',
            'PurchaseCreated',
            'PurchaseShipped',
        ]

        self._events = defaultdict(list)
        self._last_blocks = defaultdict(int)

        self._models = pd.DataFrame()
        self._predictions = pd.DataFrame()
        self._purchases = pd.DataFrame()

    def fetch_models(self, model_id: str=None, tournament_id: str=None, owner: str=None):
        self._fetch_events()

        if self._models.shape[0] == 0:
            return self._models

        idx = self._models['modelId'] == self._models['modelId']
        if model_id is not None:
            idx &= self._models['modelId'] == model_id
        if tournament_id is not None:
            idx &= self._models['tournamentId'] == tournament_id
        if owner is not None:
            idx &= self._models['owner'] == owner
        return self._models.loc[idx]

    def fetch_predictions(self, model_id: str=None, execution_start_at: int=None):
        self._fetch_events()

        if self._predictions.shape[0] == 0:
            return self._predictions

        idx = self._predictions['modelId'] == self._predictions['modelId']
        if model_id is not None:
            idx &= self._predictions['modelId'] == model_id
        if execution_start_at is not None:
            idx &= self._predictions['executionStartAt'] == execution_start_at
        return self._predictions.loc[idx]

    def fetch_purchases(self, model_id: str=None, execution_start_at: int=None, purchaser: str=None):
        self._fetch_events()

        if self._purchases.shape[0] == 0:
            return self._purchases

        idx = self._purchases['modelId'] == self._purchases['modelId']
        if model_id is not None:
            idx &= self._purchases['modelId'] == model_id
        if execution_start_at is not None:
            idx &= self._purchases['executionStartAt'] == execution_start_at
        if purchaser is not None:
            idx &= self._purchases['purchaser'] == purchaser
        return self._purchases.loc[idx]


    def _fetch_events(self):
        events = []

        for event_name in self._event_names:
            to_block = self._w3.eth.block_number
            if to_block <= self._last_blocks[event_name]:
                continue

            # print(event_name, self._last_blocks[event_name])

            events += getattr(self._contract.events, event_name).getLogs(
                fromBlock=self._last_blocks[event_name] + 1,
                # fromBlock=1,
                toBlock=to_block,
                argument_filters={
                    'executionStartAt': 1,
                },
            )

            self._last_blocks[event_name] = to_block

        # print(events)

        events.sort(key=lambda x: x['blockNumber'])

        for event in events:
            self._process_event(event)

    def _process_event(self, event):
        event_name = event['event']
        args = event['args']

        if event_name == 'ModelCreated':
            self._models = self._models.append(
                {
                    'modelId': args['modelId'],
                    'tournamentId': args['tournamentId'],
                    'owner': args['owner'],
                },
                ignore_index=True,
            )
        elif event_name == 'PredictionCreated':
            self._predictions = self._predictions.append(
                {
                    'modelId': args['modelId'],
                    'executionStartAt': args['executionStartAt'],
                    'price': str(args['price']),
                    'encryptedContent': args['encryptedContent'],
                },
                ignore_index=True,
            )
        elif event_name == 'PredictionPublished':
            idx = self._predictions['modelId'] == args['modelId']
            idx &= self._predictions['executionStartAt'] == args['executionStartAt']
            self._predictions.loc[idx, 'contentKey'] = args['contentKey']
        elif event_name == 'PurchaseCreated':
            self._purchases = self._purchases.append(
                {
                    'modelId': args['modelId'],
                    'executionStartAt': args['executionStartAt'],
                    'purchaser': args['purchaser'],
                    'publicKey': args['publicKey'],
                },
                ignore_index=True,
            )
        elif event_name == 'PurchaseShipped':
            idx = self._purchases['modelId'] == args['modelId']
            idx &= self._purchases['executionStartAt'] == args['executionStartAt']
            idx &= self._purchases['purchaser'] == args['purchaser']
            self._purchases.loc[idx, 'encryptedContentKey'] = args['encryptedContentKey']

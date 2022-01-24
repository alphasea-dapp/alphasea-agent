import time
import threading
import traceback
import pickle
import numpy as np
from ..logger import create_null_logger
from .utils import (
    fetch_historical_predictions,
    fetch_current_predictions,
    df_weight_to_purchase_params_list,
    blend_predictions,
    floor_to_execution_start_at,
    calc_target_positions,
    create_model_selection_params
)

day_seconds = 24 * 60 * 60


class Executor:
    def __init__(self, store=None, tournament_id=None, time_func=None, evaluation_periods=None,
                 model_selector=None, market_data_store=None, budget_rate=None,
                 symbol_white_list=None, logger=None, redis_client=None):
        self._store = store
        self._tournament = store.fetch_tournament(tournament_id)
        self._tournament_id = tournament_id
        self._time_func = time.time if time_func is None else time_func
        self._interval_sec = 15
        self._logger = create_null_logger() if logger is None else logger
        self._redis_client = redis_client

        self._evaluation_periods = evaluation_periods
        self._model_selector = model_selector
        self._market_data_store = market_data_store
        self._symbol_white_list = symbol_white_list.copy()
        self._budget_rate = budget_rate
        self._thread = None
        self._thread_terminated = False
        self._initialized = False

    # redis

    def _get_purchase_info(self, execution_start_at):
        key = _purchase_info_key(execution_start_at)
        value = self._redis_client.get(key)
        if value is None:
            return None
        return pickle.loads(value)

    def _set_purchase_info(self, execution_start_at, info):
        key = _purchase_info_key(execution_start_at)
        self._redis_client.set(key, pickle.dumps(info))
        self._redis_client.expireat(key, execution_start_at + 2 * 24 * 60 * 60)

    def start_thread(self):
        self._thread = threading.Thread(target=self._run)
        self._thread.start()

    def terminate_thread(self):
        self._thread_terminated = True
        self._thread.join()

    # called from other thread
    def get_target_positions(self, timestamp: int):
        execution_start_at, t = floor_to_execution_start_at(timestamp, self._tournament)
        execution_time = self._tournament['execution_time']

        df_blended_list = []
        round_count = day_seconds // execution_time
        for i in range(round_count + 1):
            df_blended_list.append(self._get_blended_prediction(
                execution_start_at=execution_start_at - execution_time * i,
                without_fetch_events=i > 0,
            ))
        df_blended_list = list(reversed(df_blended_list))

        return calc_target_positions(
            t,
            df_blended_list,
        )

    def _get_blended_prediction(self, execution_start_at: int, without_fetch_events=False):
        purchase_info = self._get_purchase_info(execution_start_at)
        if purchase_info is None:
            df_weight = None
        else:
            df_weight = purchase_info['df_weight']

        df_current = fetch_current_predictions(
            store=self._store,
            tournament_id=self._tournament_id,
            execution_start_at=execution_start_at,
            without_fetch_events=without_fetch_events,
        )

        return blend_predictions(
            df_current=df_current,
            df_weight=df_weight,
        )

    def _run(self):
        while not self._thread_terminated:
            try:
                if not self._initialized:
                    self._initialize()
                    self._initialized = True
                self._step()
            except Exception as e:
                self._logger.error(e)
                self._logger.error(traceback.format_exc())
            time.sleep(self._interval_sec)

    def _step_purchase(self, execution_start_at):
        purchase_info = self._get_purchase_info(execution_start_at)
        if purchase_info is not None:
            return

        execution_start_ats = np.sort(
            execution_start_at
            - day_seconds * np.arange(2, 2 + self._evaluation_periods)
        )

        df = fetch_historical_predictions(
            store=self._store,
            tournament_id=self._tournament_id,
            execution_start_ats=execution_start_ats,
            logger=self._logger,
        )

        df_current = fetch_current_predictions(
            store=self._store,
            tournament_id=self._tournament_id,
            execution_start_at=execution_start_at,
        )

        df_market = self._market_data_store.fetch_df_market(
            symbols=self._symbol_white_list,
        )

        params = create_model_selection_params(
            df=df,
            df_current=df_current,
            df_market=df_market,
            execution_start_ats=execution_start_ats,
            symbols=self._symbol_white_list
        )
        params.budget = self._budget_rate * self._store.get_balance()

        # モデル選択
        df_weight = self._model_selector.select_model(params)
        df_weight = df_weight.loc[df_weight['weight'] > 0]
        self._logger.debug('df_weight {}'.format(df_weight))

        # 購入
        create_purchase_params_list = df_weight_to_purchase_params_list(
            df_current=df_current,
            df_weight=df_weight,
            execution_start_at=execution_start_at
        )
        self._store.create_purchases(create_purchase_params_list)

        self._set_purchase_info(execution_start_at, {
            'df_weight': df_weight
        })

    def _step(self):
        now = int(self._time_func())

        t = self._tournament

        purchase_time_buffer = int(t['purchase_time'] * 0.2)
        purchase_start_at = (t['execution_start_at'] - t['execution_preparation_time'] -
                             t['shipping_time'] - t['purchase_time'] + purchase_time_buffer)

        interval = t['execution_time']

        if (now - purchase_start_at) % interval < t['purchase_time'] - purchase_time_buffer:
            execution_start_at = ((now - purchase_start_at) // interval) * interval + t['execution_start_at']
            self._step_purchase(execution_start_at)

    def _initialize(self):
        self._market_data_store.fetch_df_market(
            symbols=self._symbol_white_list,
        )


def _purchase_info_key(execution_start_at):
    return 'purchase_info:{}'.format(execution_start_at)

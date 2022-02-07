import time
import threading
import traceback
import numpy as np
from ..logger import create_null_logger
from .utils import (
    fetch_historical_predictions,
    fetch_current_predictions,
    blend_predictions,
    floor_to_execution_start_at,
    calc_target_positions,
    create_model_selection_params
)

day_seconds = 24 * 60 * 60


class Executor:
    def __init__(self, store=None, tournament_id=None, time_func=None, evaluation_periods=None,
                 model_selector=None, market_data_store=None,
                 symbol_white_list=None, logger=None, redis_client=None):
        self._store = store
        self._tournament = store.fetch_tournament(tournament_id)
        self._tournament_id = tournament_id
        self._time_func = time.time if time_func is None else time_func
        self._interval_sec = 15
        self._logger = create_null_logger() if logger is None else logger
        self._redis_client = redis_client
        self._prediction_sent = set()
        self._calc_weight_cache = {}

        self._evaluation_periods = evaluation_periods
        self._model_selector = model_selector
        self._market_data_store = market_data_store
        self._symbol_white_list = symbol_white_list.copy()
        self._thread = None
        self._thread_terminated = False
        self._initialized = False

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
        df_weight = self._calc_weight(execution_start_at)

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

    def _create_model_selection_params(self, execution_start_at, model_ids=None):
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

        if model_ids is not None:
            df = df.loc[df.index.get_level_values('model_id').isin(model_ids)]
            df_current = df_current.loc[df_current.index.get_level_values('model_id').isin(model_ids)]

        params = create_model_selection_params(
            df=df,
            df_current=df_current,
            df_market=df_market,
            execution_start_ats=execution_start_ats,
            symbols=self._symbol_white_list
        )

        return params

    def _step_send(self, execution_start_at):
        if execution_start_at in self._prediction_sent:
            return

        params = self._create_model_selection_params(
            execution_start_at=execution_start_at,
        )
        params.owner = self._store.default_account_address()
        receivers = self._model_selector.select_receivers(params)

        self._prediction_sent.add(execution_start_at)

        self._store.send_prediction_keys(
            tournament_id=self._tournament_id,
            execution_start_at=execution_start_at,
            receivers=receivers
        )

    def _calc_weight(self, execution_start_at):
        if execution_start_at in self._calc_weight_cache:
            return self._calc_weight_cache[execution_start_at]

        t = self._tournament

        preparation_time_buffer = int(t['execution_preparation_time'] * 0.2)
        preparation_start_at = (execution_start_at
                                - t['execution_preparation_time']
                                + preparation_time_buffer)

        if self._time_func() < preparation_start_at:
            return None

        df_current = fetch_current_predictions(
            store=self._store,
            tournament_id=self._tournament_id,
            execution_start_at=execution_start_at,
        )
        df_current = df_current.loc[~df_current['content'].isna()]

        params = self._create_model_selection_params(
            execution_start_at=execution_start_at,
            model_ids=df_current.index,
        )
        params.owner = self._store.default_account_address()

        df_weight = self._model_selector.select_model(params)
        df_weight = df_weight.loc[df_weight['weight'] > 0]
        self._logger.debug('df_weight {}'.format(df_weight))

        self._calc_weight_cache[execution_start_at] = df_weight

        return df_weight

    def _step(self):
        now = int(self._time_func())

        t = self._tournament

        sending_time_buffer = int(t['sending_time'] * 0.2)
        sending_start_at = (t['execution_start_at'] - t['execution_preparation_time'] -
                             t['sending_time'] + sending_time_buffer)

        interval = t['execution_time']

        if (now - sending_start_at) % interval < t['sending_time'] - sending_time_buffer:
            execution_start_at = ((now - sending_start_at) // interval) * interval + t['execution_start_at']
            self._step_send(execution_start_at)

    def _initialize(self):
        self._market_data_store.fetch_df_market(
            symbols=self._symbol_white_list,
        )


def _purchase_info_key(execution_start_at):
    return 'purchase_info:{}'.format(execution_start_at)

import time
from collections import defaultdict
import threading
import traceback
from ..prediction_format import validate_content, normalize_content
from .model_id import validate_model_id
from ..logger import create_null_logger

day_seconds = 24 * 60 * 60


class Predictor:
    def __init__(self, store=None, tournament_id=None, time_func=None,
                 price_min=None, price_increase_rate=None, price_decrease_rate=None,
                 logger=None):
        self._store = store
        self._predictions = defaultdict(defaultdict)
        self._tournament_id = tournament_id
        self._tournament = None
        self._time_func = time.time if time_func is None else time_func
        self._lock = threading.Lock()
        self._interval_sec = 15
        self._logger = create_null_logger() if logger is None else logger

        self._price_min = price_min
        self._price_increase_rate = price_increase_rate
        self._price_decrease_rate = price_decrease_rate
        self._thread = None
        self._thread_terminated = False

    def start_thread(self):
        self._thread = threading.Thread(target=self._run)
        self._thread.start()

    def terminate_thread(self):
        self._thread_terminated = True
        self._thread.join()

    def submit_prediction(self, model_id: str, execution_start_at: int,
                          prediction_license: str, content: bytes):

        if prediction_license != 'CC0-1.0':
            raise Exception('prediction_license must be CC0-1.0')

        if execution_start_at % day_seconds != self._get_tournament()['execution_start_at']:
            raise Exception('invalid execution_start_at {} {}'.format(execution_start_at,
                                                                      self._get_tournament()['execution_start_at']))

        validate_model_id(model_id)

        validate_content(content)
        content = normalize_content(content)

        prediction = {
            'content': content,
            'prediction_license': prediction_license,
        }
        with self._lock:
            self._predictions[model_id][execution_start_at] = prediction

    def _run(self):
        while not self._thread_terminated:
            try:
                self._step()
            except Exception as e:
                self._logger.error(e)
                self._logger.error(traceback.format_exc())
            time.sleep(self._interval_sec)

    def _step_prediction(self):
        with self._lock:
            predictions = self._predictions
            self._predictions = defaultdict(defaultdict)

        create_model_params_list = []
        create_prediction_params_list = []

        for model_id in predictions:
            for execution_start_at in predictions[model_id]:
                prediction = predictions[model_id][execution_start_at]

                create_model_params_list.append({
                    'tournament_id': self._tournament_id,
                    'model_id': model_id,
                    'prediction_license': prediction['prediction_license'],
                })

                price = self._calc_prediction_price(
                    model_id=model_id,
                    execution_start_at=execution_start_at,
                )
                create_prediction_params_list.append({
                    'model_id': model_id,
                    'execution_start_at': execution_start_at,
                    'content': prediction['content'],
                    'price': price,
                })

        self._store.create_models_if_not_exist(create_model_params_list)
        self._store.create_predictions(create_prediction_params_list)

    def _step_shipping(self, execution_start_at):
        purchases = self._store.fetch_purchases_to_ship(
            tournament_id=self._tournament_id,
            execution_start_at=execution_start_at
        )
        ship_purchase_params_list = []
        for purchase in purchases:
            ship_purchase_params_list.append({
                'model_id': purchase['model_id'],
                'execution_start_at': purchase['execution_start_at'],
                'purchaser': purchase['purchaser']
            })
        self._store.ship_purchases(ship_purchase_params_list)

    def _step_publication(self, execution_start_at):
        predictions = self._store.fetch_predictions_to_publish(
            tournament_id=self._tournament_id,
            execution_start_at=execution_start_at
        )
        publish_prediction_params_list = []
        for prediction in predictions:
            publish_prediction_params_list.append({
                'model_id': prediction['model_id'],
                'execution_start_at': prediction['execution_start_at'],
            })
        self._store.publish_predictions(publish_prediction_params_list)

    def _get_tournament(self):
        if self._tournament is None:
            self._tournament = self._store.fetch_tournament(self._tournament_id)
        return self._tournament

    def _step(self):
        now = int(self._time_func())

        t = self._get_tournament()

        prediction_time_buffer = int(t['prediction_time'] * 0.2)
        prediction_start_at = (t['execution_start_at'] - t['execution_preparation_time'] -
                               t['shipping_time'] - t['purchase_time'] - t['prediction_time'] + prediction_time_buffer)

        shipping_time_buffer = int(t['shipping_time'] * 0.2)
        shipping_start_at = (t['execution_start_at'] - t['execution_preparation_time'] -
                             t['shipping_time'] + shipping_time_buffer)

        publication_time_buffer = int(t['publication_time'] * 0.2)
        publication_start_at = t['execution_start_at'] + t['execution_time'] + day_seconds + publication_time_buffer

        if (now - prediction_start_at) % day_seconds < t['prediction_time'] - prediction_time_buffer:
            self._step_prediction()
        elif (now - shipping_start_at) % day_seconds < t['shipping_time'] - shipping_time_buffer:
            execution_start_at = ((now - shipping_start_at) // day_seconds) * day_seconds + t['execution_start_at']
            self._step_shipping(execution_start_at)
        elif (now - publication_start_at) % day_seconds < t['publication_time'] - publication_time_buffer:
            execution_start_at = ((now - publication_start_at) // day_seconds) * day_seconds + t['execution_start_at']
            self._step_publication(execution_start_at)

    def _calc_prediction_price(self, model_id: str, execution_start_at: int):
        prediction = self._store.fetch_last_prediction(
            model_id=model_id,
            max_execution_start_at=execution_start_at - 1
        )
        if prediction is None:
            return self._price_min
        else:
            if prediction['purchase_count'] > 0:
                return int(prediction['price'] * (1 + self._price_increase_rate))
            else:
                return max(self._price_min, int(prediction['price'] * (1 - self._price_decrease_rate)))

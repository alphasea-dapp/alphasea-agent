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
                 logger=None):
        self._store = store
        self._predictions = defaultdict(defaultdict)
        self._tournament_id = tournament_id
        self._tournament = store.fetch_tournament(tournament_id)
        self._time_func = time.time if time_func is None else time_func
        self._lock = threading.Lock()
        self._interval_sec = 15
        self._logger = create_null_logger() if logger is None else logger

        self._thread = None
        self._thread_terminated = False

    def start_thread(self):
        self._thread = threading.Thread(target=self._run)
        self._thread.start()

    def terminate_thread(self):
        self._thread_terminated = True
        self._thread.join()

    # called from other thread
    def submit_prediction(self, model_id: str, execution_start_at: int,
                          prediction_license: str, content: bytes):

        if prediction_license != 'CC0-1.0':
            raise Exception('prediction_license must be CC0-1.0')

        t = self._tournament
        if execution_start_at % t['execution_time'] != t['execution_start_at']:
            raise Exception('invalid execution_start_at {} {}'.format(
                execution_start_at, t['execution_start_at']))

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

                create_prediction_params_list.append({
                    'model_id': model_id,
                    'execution_start_at': execution_start_at,
                    'content': prediction['content'],
                })

        self._store.create_models_if_not_exist(create_model_params_list)
        self._store.create_predictions(create_prediction_params_list)

    def _step_publication(self, execution_start_at):
        self._store.publish_prediction_key(
            tournament_id=self._tournament_id,
            execution_start_at=execution_start_at
        )

    def _step(self):
        now = int(self._time_func())

        t = self._tournament

        prediction_time_buffer = int(t['prediction_time'] * 0.2)
        prediction_start_at = (t['execution_start_at'] - t['execution_preparation_time'] -
                               t['sending_time'] - t['prediction_time'] + prediction_time_buffer)

        publication_time_buffer = int(t['publication_time'] * 0.2)
        publication_start_at = t['execution_start_at'] + t['execution_time'] + day_seconds + publication_time_buffer

        interval = t['execution_time']

        if (now - prediction_start_at) % interval < t['prediction_time'] - prediction_time_buffer:
            self._step_prediction()
        elif (now - publication_start_at) % interval < t['publication_time'] - publication_time_buffer:
            execution_start_at = ((now - publication_start_at) // interval) * interval + t['execution_start_at']
            self._step_publication(execution_start_at)

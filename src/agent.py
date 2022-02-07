import os
import time
from types import SimpleNamespace
from ccxt_rate_limiter.rate_limiter_group import RateLimiterGroup
from redis_namespace import StrictRedis
from web3 import Web3
from .web3 import (
    network_name_to_chain_id,
)
from .store.store import Store
from .executor.executor import Executor
from .predictor.predictor import Predictor
from .market_data_store.data_fetcher_builder import DataFetcherBuilder
from .market_data_store.market_data_store import MarketDataStore
from .model_selection.score_model_selector import ScoreModelSelector
from .model_selection.all_model_selector import AllModelSelector
from .logger import create_null_logger
from .model_selection.statistics import max_sprt_t_test_log_prob_ratio


class Agent:
    def __init__(self, w3=None, contract=None, logger=None):
        if logger is None:
            logger = create_null_logger()

        executor_evaluation_periods = int(os.getenv('ALPHASEA_EXECUTOR_EVALUATION_PERIODS'))
        executor_symbol_white_list = os.getenv('ALPHASEA_EXECUTOR_SYMBOL_WHITE_LIST').split(',')
        executor_execution_cost = float(os.getenv('ALPHASEA_EXECUTOR_EXECUTION_COST'))
        network_name = os.getenv('ALPHASEA_NETWORK')
        chain_id = network_name_to_chain_id(network_name)
        start_block_number = int(os.getenv('ALPHASEA_START_BLOCK_NUMBER', '1'))
        max_priority_fee_scale = float(os.getenv('ALPHASEA_MAX_PRIORITY_FEE_SCALE', '1'))
        tournament_id = 'crypto_daily'

        logger.debug('executor_evaluation_periods {}'.format(executor_evaluation_periods))
        logger.debug('executor_symbol_white_list {}'.format(executor_symbol_white_list))
        logger.debug('executor_execution_cost {}'.format(executor_execution_cost))
        logger.debug('network_name {}'.format(network_name))
        logger.debug('chain_id {}'.format(chain_id))
        logger.debug('start_block_number {}'.format(start_block_number))
        logger.debug('max_priority_fee_scale {}'.format(max_priority_fee_scale))
        logger.debug('tournament_id {}'.format(tournament_id))

        rate_limiter = RateLimiterGroup(
            limits=[
                {
                    'tag': 'default',
                    'period_sec': 1,
                    'count': 1,
                }
            ]
        )

        store = Store(
            w3=w3,
            contract=contract,
            chain_id=chain_id,
            logger=logger,
            rate_limiter=rate_limiter,
            start_block_number=start_block_number,
            redis_client=StrictRedis.from_url(
                os.getenv('REDIS_URL'),
                namespace='store:{}:'.format(contract.address)
            ),
            max_priority_fee_scale=max_priority_fee_scale,
        )

        data_fetcher_builder = DataFetcherBuilder()
        tournament = store.fetch_tournament(tournament_id)
        market_data_store = MarketDataStore(
            data_fetcher_builder=data_fetcher_builder,
            start_time=time.time() - 24 * 60 * 60 * executor_evaluation_periods * 2,
            logger=logger,
            execution_lag_sec=(
                    tournament['prediction_time']
                    + tournament['sending_time']
                    + tournament['execution_preparation_time']
            ),
            execution_time_sec=tournament['execution_time'],
        )

        model_selector_name = os.getenv('ALPHASEA_EXECUTOR_MODEL_SELECTOR')
        logger.debug('model_selector_name {}'.format(model_selector_name))
        if model_selector_name == 'score':
            model_selector = ScoreModelSelector(
                execution_cost=executor_execution_cost,
                score_threshold=float(os.getenv('ALPHASEA_EXECUTOR_SCORE_THRESHOLD')),
                logger=logger,
            )
        elif model_selector_name == 'all_model':
            model_selector = AllModelSelector()
        else:
            raise Exception('unknown model selector {}'.format(model_selector_name))

        tournaments = {}

        executor = Executor(
            store=store,
            tournament_id=tournament_id,
            evaluation_periods=executor_evaluation_periods,
            model_selector=model_selector,
            market_data_store=market_data_store,
            symbol_white_list=executor_symbol_white_list,
            logger=logger,
            redis_client=StrictRedis.from_url(
                os.getenv('REDIS_URL'),
                namespace='executor:{}:'.format(contract.address)
            ),
        )

        predictor = Predictor(
            store=store,
            tournament_id=tournament_id,
            logger=logger,
        )

        tournaments[tournament_id] = SimpleNamespace(
            executor=executor,
            predictor=predictor,
        )

        self.tournaments = tournaments

    def initialize(self):
        tournaments = self.tournaments
        for tournament_id in tournaments:
            tournaments[tournament_id].executor.start_thread()
            tournaments[tournament_id].predictor.start_thread()

    def finalize(self):
        tournaments = self.tournaments
        for tournament_id in tournaments:
            tournaments[tournament_id].executor.terminate_thread()
            tournaments[tournament_id].predictor.terminate_thread()

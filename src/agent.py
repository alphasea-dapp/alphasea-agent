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
from .model_selection.equal_weight_model_selector import EqualWeightModelSelector


class Agent:

    def __init__(self, w3=None, contract=None, logger=None):

        executor_evaluation_periods = int(os.getenv('ALPHASEA_EXECUTOR_EVALUATION_PERIODS'))
        executor_symbol_white_list = os.getenv('ALPHASEA_EXECUTOR_SYMBOL_WHITE_LIST').split(',')
        executor_budget_rate = float(os.getenv('ALPHASEA_EXECUTOR_BUDGET_RATE'))
        network_name = os.getenv('ALPHASEA_NETWORK')
        chain_id = network_name_to_chain_id(network_name)
        start_block_number = int(os.getenv('ALPHASEA_START_BLOCK_NUMBER', '1'))

        data_fetcher_builder = DataFetcherBuilder()
        market_data_store = MarketDataStore(
            data_fetcher_builder=data_fetcher_builder,
            start_time=time.time() - 24 * 60 * 60 * executor_evaluation_periods * 2,
            logger=logger,
        )

        rate_limiter = RateLimiterGroup(
            limits=[
                {
                    'tag': 'default',
                    'period_sec': 1,
                    'count': 1,
                }
            ]
        )

        redis_client = StrictRedis.from_url(
            os.getenv('REDIS_URL'),
            namespace='store:'
        )

        store = Store(
            w3=w3,
            contract=contract,
            chain_id=chain_id,
            logger=logger,
            rate_limiter=rate_limiter,
            start_block_number=start_block_number,
            redis_client=redis_client,
        )

        model_selector = EqualWeightModelSelector(
            execution_cost=float(os.getenv('ALPHASEA_EXECUTOR_EXECUTION_COST')),
            assets=Web3.toWei(os.getenv('ALPHASEA_EXECUTOR_ASSETS'), 'ether'),
        )

        tournaments = {}

        for i in range(0, 24, 2):
            tournament_id = 'crypto_daily_{:02}30'.format(i)

            executor = Executor(
                store=store,
                tournament_id=tournament_id,
                evaluation_periods=executor_evaluation_periods,
                model_selector=model_selector,
                market_data_store=market_data_store,
                symbol_white_list=executor_symbol_white_list,
                budget_rate=executor_budget_rate,
                logger=logger,
            )

            predictor = Predictor(
                store=store,
                tournament_id=tournament_id,
                price_min=Web3.toWei(os.getenv('ALPHASEA_PREDICTOR_PRICE_MIN'), 'ether'),
                price_increase_rate=float(os.getenv('ALPHASEA_PREDICTOR_PRICE_INCREASE_RATE')),
                price_decrease_rate=float(os.getenv('ALPHASEA_PREDICTOR_PRICE_DECREASE_RATE')),
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

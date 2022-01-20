from fastapi import FastAPI, Response, Body

from io import StringIO
import os
import time
from ccxt_rate_limiter.rate_limiter_group import RateLimiterGroup
from redis_namespace import StrictRedis
from web3 import Web3
from web3.auto import w3
from web3.eth import Account
from .web3 import (
    get_wallet_private_key,
    network_name_to_chain_id,
    network_name_to_currency,
    get_hardhat_private_key,
)
from .store.store import Store
from .executor.executor import Executor
from .predictor.predictor import Predictor
from .market_data_store.data_fetcher_builder import DataFetcherBuilder
from .market_data_store.market_data_store import MarketDataStore
from .model_selection.equal_weight_model_selector import EqualWeightModelSelector
from .logger import create_logger, set_log_level_web3, customize_uvicorn_log

default_tournament_id = os.getenv('ALPHASEA_DEFAULT_TOURNAMENT_ID')
executor_evaluation_periods = int(os.getenv('ALPHASEA_EXECUTOR_EVALUATION_PERIODS'))
executor_symbol_white_list = os.getenv('ALPHASEA_EXECUTOR_SYMBOL_WHITE_LIST').split(',')
executor_budget_rate = float(os.getenv('ALPHASEA_EXECUTOR_BUDGET_RATE'))
log_level = os.getenv('ALPHASEA_LOG_LEVEL')
log_level_web3 = os.getenv('ALPHASEA_LOG_LEVEL_WEB3')
network_name = os.getenv('ALPHASEA_NETWORK')
chain_id = network_name_to_chain_id(network_name)
start_block_number = int(os.getenv('ALPHASEA_START_BLOCK_NUMBER', '1'))

logger = create_logger(log_level)
customize_uvicorn_log(log_level)
set_log_level_web3(log_level_web3)

data_fetcher_builder = DataFetcherBuilder()
market_data_store = MarketDataStore(
    data_fetcher_builder=data_fetcher_builder,
    start_time=time.time() - 24 * 60 * 60 * executor_evaluation_periods * 2,
    logger=logger,
)

if network_name == 'hardhat':
    w3.eth.default_account = Account.from_key(get_hardhat_private_key())
else:
    w3.eth.default_account = Account.from_key(get_wallet_private_key())

if chain_id != w3.eth.chain_id:
    raise Exception('specified chain_id({}) is different from remote chain_id({})'.format(
        chain_id, w3.eth.chain_id
    ))

logger.info('chain_id {}'.format(w3.eth.chain_id))
logger.info('account address {}'.format(w3.eth.default_account.address))
logger.info('account balance {} {}'.format(
    Web3.fromWei(w3.eth.get_balance(w3.eth.default_account.address), 'ether'),
    network_name_to_currency(network_name)
))

contract = w3.eth.contract(
    address=os.getenv('ALPHASEA_CONTRACT_ADDRESS'),
    abi=os.getenv('ALPHASEA_CONTRACT_ABI'),
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

executor = Executor(
    store=store,
    tournament_id=default_tournament_id,
    evaluation_periods=executor_evaluation_periods,
    model_selector=model_selector,
    market_data_store=market_data_store,
    symbol_white_list=executor_symbol_white_list,
    budget_rate=executor_budget_rate,
    logger=logger,
)

predictor = Predictor(
    store=store,
    tournament_id=default_tournament_id,
    price_min=Web3.toWei(os.getenv('ALPHASEA_PREDICTOR_PRICE_MIN'), 'ether'),
    price_increase_rate=float(os.getenv('ALPHASEA_PREDICTOR_PRICE_INCREASE_RATE')),
    price_decrease_rate=float(os.getenv('ALPHASEA_PREDICTOR_PRICE_DECREASE_RATE')),
    logger=logger,
)

app = FastAPI()


@app.on_event("startup")
def startup_event():
    executor.start_thread()
    predictor.start_thread()


@app.on_event("shutdown")
def shutdown_event():
    executor.terminate_thread()
    predictor.terminate_thread()


@app.post("/submit_prediction")
def post_submit_prediction(model_id: str = Body(...), execution_start_at: int = Body(...),
                           prediction_license: str = Body(...), content: str = Body(...)):
    predictor.submit_prediction(
        model_id=model_id,
        execution_start_at=int(execution_start_at),
        prediction_license=prediction_license,
        content=content.encode(),
    )
    return {}


@app.get("/blended_prediction.csv")
def get_blended_prediction_csv(execution_start_at: int):
    df = executor.get_blended_prediction(
        execution_start_at=int(execution_start_at),
    )
    output = StringIO()
    df.to_csv(output)
    return Response(content=output.getvalue(), media_type="text/csv")

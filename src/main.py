from fastapi import FastAPI, Response, Body

from io import StringIO
import os
import time
from web3.auto import w3
from .store.store import Store
from .executor.executor import Executor
from .predictor.predictor import Predictor
from .market_data_store.data_fetcher_builder import DataFetcherBuilder
from .market_data_store.market_data_store import MarketDataStore
from .model_selection.equal_weight_model_selector import EqualWeightModelSelector


def _eth_to_wei(x):
    return int(x * 1e18)


default_tournament_id = os.getenv('ALPHASEA_DEFAULT_TOURNAMENT_ID')
executor_evaluation_periods = int(os.getenv('ALPHASEA_EXECUTOR_EVALUATION_PERIODS'))
executor_symbol_white_list = os.getenv('ALPHASEA_EXECUTOR_SYMBOL_WHITE_LIST').split(',')
executor_budget = _eth_to_wei(float(os.getenv('ALPHASEA_EXECUTOR_BUDGET_ETH')))

data_fetcher_builder = DataFetcherBuilder()
market_data_store = MarketDataStore(
    data_fetcher_builder=data_fetcher_builder,
    start_time=time.time() - 24 * 60 * 60 * executor_evaluation_periods * 2
)

contract = w3.eth.contract(
    address=os.getenv('ALPHASEA_CONTRACT_ADDRESS'),
    abi=os.getenv('ALPHASEA_CONTRACT_ABI'),
)
store = Store(
    w3=w3,
    contract=contract,
)

model_selector = EqualWeightModelSelector(
    execution_cost=float(os.getenv('ALPHASEA_EXECUTOR_EXECUTION_COST')),
    assets=_eth_to_wei(float(os.getenv('ALPHASEA_EXECUTOR_ASSETS_ETH'))),
    budget=executor_budget,
)

executor = Executor(
    store=store,
    tournament_id=default_tournament_id,
    evaluation_periods=executor_evaluation_periods,
    model_selector=model_selector,
    market_data_store=market_data_store,
    symbol_white_list=executor_symbol_white_list,
)

predictor = Predictor(
    store=store,
    tournament_id=default_tournament_id,
    price_min=_eth_to_wei(float(os.getenv('ALPHASEA_PREDICTOR_PRICE_MIN_ETH'))),
    price_increase_rate=float(os.getenv('ALPHASEA_PREDICTOR_PRICE_INCREASE_RATE')),
    price_decrease_rate=float(os.getenv('ALPHASEA_PREDICTOR_PRICE_DECREASE_RATE')),
)

app = FastAPI()


@app.on_event("startup")
def startup_event():
    if executor_budget > 0:
        executor.start_thread()
    predictor.start_thread()


@app.on_event("shutdown")
def shutdown_event():
    if executor_budget > 0:
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
def get_blended_position_csv(execution_start_at: int):
    df = executor.get_blended_position(
        execution_start_at=int(execution_start_at),
    )
    output = StringIO()
    df.to_csv(output)
    return Response(content=output.getvalue(), media_type="text/csv")

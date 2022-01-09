from fastapi import FastAPI

import os
from web3.auto import w3
from src.store.store import Store
from src.executor.executor import Executor
from src.predictor.predictor import Predictor

default_tournament_id = 'crypto_daily'

contract = w3.eth.contract(
    address=os.getenv('ALPHASEA_CONTRACT_ADDRESS'),
    abi=os.getenv('ALPHASEA_CONTRACT_ABI'),
)

store = Store(w3=w3, contract=contract)
executor = Executor(store=store, tournament_id=default_tournament_id)
predictor = Predictor(store=store, tournament_id=default_tournament_id)

app = FastAPI()


@app.post("/submit_prediction")
def post_submit_prediction(tournament_id: str, model_id: str, execution_start_at: int,
                           prediction_license: str, content: str):

    return predictor.submit_prediction(
        tournament_id=tournament_id,
        model_id=model_id,
        execution_start_at=execution_start_at,
        prediction_license=prediction_license,
        content=content,
    )


@app.get("/blended_prediction")
def get_blended_prediction(tournament_id: str, execution_start_at: int):
    return executor.get_blended_prediction(
        tournament_id=tournament_id,
        execution_start_at=execution_start_at,
    )

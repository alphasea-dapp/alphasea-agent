from fastapi import FastAPI, Response, Body

from io import StringIO
import os
from web3 import Web3
from web3.eth import Account
from .web3 import (
    get_wallet_private_key,
    network_name_to_chain_id,
    network_name_to_currency,
    create_w3,
    get_account_address,
)
from .logger import create_logger, set_log_level_web3, customize_uvicorn_log
from .agent import Agent

log_level = os.getenv('ALPHASEA_LOG_LEVEL')
log_level_web3 = os.getenv('ALPHASEA_LOG_LEVEL_WEB3')
network_name = os.getenv('ALPHASEA_NETWORK')
chain_id = network_name_to_chain_id(network_name)

logger = create_logger(log_level)
customize_uvicorn_log(log_level)
set_log_level_web3(log_level_web3)

w3 = create_w3(
    network_name=network_name,
    web3_provider_uri=os.getenv('WEB3_PROVIDER_URI'),
)

if network_name == 'hardhat':
    w3.eth.default_account = w3.eth.accounts[0]
else:
    w3.eth.default_account = Account.from_key(get_wallet_private_key())

if chain_id != w3.eth.chain_id:
    raise Exception('specified chain_id({}) is different from remote chain_id({})'.format(
        chain_id, w3.eth.chain_id
    ))

logger.info('chain_id {}'.format(w3.eth.chain_id))
logger.info('account address {}'.format(get_account_address(w3.eth.default_account)))
logger.info('account balance {} {}'.format(
    Web3.fromWei(w3.eth.get_balance(get_account_address(w3.eth.default_account)), 'ether'),
    network_name_to_currency(network_name)
))

contract = w3.eth.contract(
    address=os.getenv('ALPHASEA_CONTRACT_ADDRESS'),
    abi=os.getenv('ALPHASEA_CONTRACT_ABI'),
)

agent = Agent(
    w3=w3,
    contract=contract,
    logger=logger
)

app = FastAPI()


@app.on_event("startup")
def startup_event():
    agent.initialize()


@app.on_event("shutdown")
def shutdown_event():
    agent.finalize()


@app.post("/submit_prediction")
def post_submit_prediction(model_id: str = Body(...),
                           tournament_id: str = Body(...),
                           execution_start_at: int = Body(...),
                           prediction_license: str = Body(...), content: str = Body(...)):
    agent.tournaments[tournament_id].predictor.submit_prediction(
        model_id=model_id,
        execution_start_at=int(execution_start_at),
        prediction_license=prediction_license,
        content=content.encode(),
    )
    return {}


@app.get("/blended_prediction.csv")
def get_blended_prediction_csv(tournament_id: str, execution_start_at: int):
    df = agent.tournaments[tournament_id].executor.get_blended_prediction(
        execution_start_at=int(execution_start_at),
    )
    output = StringIO()
    df.to_csv(output)
    return Response(content=output.getvalue(), media_type="text/csv")

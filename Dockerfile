FROM python:3.6.15

RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir \
    ccxt==1.57.43 \
    "git+https://github.com/richmanbtc/ccxt_rate_limiter.git@v0.0.4#egg=ccxt_rate_limiter" \
    coverage==6.2 \
    "git+https://github.com/richmanbtc/crypto_data_fetcher.git@v0.0.17#egg=crypto_data_fetcher" \
    cvxpy==1.1.10 \
    fastapi==0.70.1 \
    flake8==4.0.1 \
    numpy==1.19.5 \
    pandas==1.1.5 \
    PyNaCl==1.4.0 \
    scikit-learn==0.24 \
    simanneal==0.5.0 \
    stringcase==1.2.0 \
    uvicorn[standard]==0.16.0 \
    web3==5.25.0

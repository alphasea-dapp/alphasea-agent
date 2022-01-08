



## API docs

http://localhost:8070/docs
http://localhost:8070/redoc

## Development

### abi

docker-compose-dev.yml内の以下を設定する必要がある。
ALPHASEA_CONTRACT_ADDRESS
ALPHASEA_CONTRACT_ABI

ALPHASEA_CONTRACT_ABIはalphaseaリポジトリでnpm run print_abiで取得した文字列を設定すれば良い。

### test

hardhat nodeに依存するので、
alphaseaリポジトリでnpx hardhat nodeを立ち上げてから実行。

```bash
docker-compose -f docker-compose-dev.yml run --rm agent bash scripts/test.sh
```

### lint

```bash
docker-compose -f docker-compose-dev.yml run --rm agent flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
docker-compose -f docker-compose-dev.yml run --rm agent flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
```

### CI

github actionsでtestとlintを行っている。

設定: .github/workflows/python-app.yml

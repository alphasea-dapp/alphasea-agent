

## Development

### abi

docker-compose-dev.yml内の以下を設定する必要がある。
ALPHASEA_CONTRACT_ADDRESS
ALPHASEA_CONTRACT_ABI

ALPHASEA_CONTRACT_ABIはalphaseaリポジトリでnpm run print_abiで取得した文字列を設定すれば良い。

### test

hardhat nodeに依存するので、
alphaseaリポジトリでnpx hardhat nodeを立ち上げてから実行。

docker-compose -f docker-compose-dev.yml run --rm agent python -m unittest

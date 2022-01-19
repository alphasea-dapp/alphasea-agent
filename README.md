## alphasea-agent

alphasea-agentは、
AlphaSeaスマートコントラクトを、
シンプルなインターフェースで扱えるようにするための、
HTTPサーバーです。

## 機能

HTTP APIインターフェース

- 予測提出
- メタモデルの予測値取得

エージェントの動き

- 提出された予測をethスマートコントラクトに投稿
- 購入された予測をethスマートコントラクト経由で購入者に届ける
- モデル選択アルゴリズムで購入する予測を選び購入する

## agentの動かし方

### 秘密鍵を用意

agentの稼働にはETHウォレットが必要です。

agentで使う用のETHウォレットの秘密鍵を生成します。
パスワードはdefault_wallet_password内に記載されたalphasea_passwordのままでも、
変えても良いと思います。

[アカウント操作について](https://geth.ethereum.org/docs/interface/managing-your-accounts)

```bash
docker run --rm -v "$(pwd)/default_wallet_password:/default_wallet_password:ro" -v "$(pwd)/data/keystore:/root/.ethereum/keystore" ethereum/client-go account new --password /default_wallet_password
```

上記を実行すると、data/keystoreに秘密鍵が保存されます。
以下で確認できます。
data/keystoreの秘密鍵を消したり漏らしたりすると資産を失います。

```bash
docker run --rm -v "$(pwd)/data/keystore:/root/.ethereum/keystore:ro" ethereum/client-go account list
```

送金などは以下のコンソールでできます。起動時にパスワードでアカウントをアンロックしています。

```bash
docker run --rm -v "$(pwd)/default_wallet_password:/default_wallet_password:ro" -v "$(pwd)/data/keystore:/root/.ethereum/keystore:ro" -it ethereum/client-go console --password /default_wallet_password --unlock 0
```

### ウォレットにETHを入れる

alphasea-agentは動作にETHが必要です(gas代や予測購入費用)。
testnetの場合はfaucetサイトで入れてください。
mainnetの場合は送金で入れてください。
アドレスは前項の手順で見れると思います。

### agentとgethを起動

mainnet (未実装)

```bash
docker-compose up -d
```

testnet (ropsten)

```bash
docker-compose -f docker-compose-ropsten.yml up -d
```

## agentの使い方

以下の2つを参考にしてください。

### alphasea-example-model (未実装)

Numeraiのexample modelに相当するものです。
毎日、agentに対して予測を提出します。

[alphasea-example-model](https://github.com/alphasea-dapp/alphasea-example-model)

### alphasea-trade-bot (未実装)

Numeraiのfund運用に相当するものです。
毎日、agentからメタモデル予測結果を取得し、リバランスします。
いくつかのCEXのPerpetual futureに対応しています。

[alphasea-trade-bot](https://github.com/alphasea-dapp/alphasea-trade-bot)

## Settings

environment variables (defined in docker-compose.yml)

|name|description|
|:-:|:-:|
|WEB3_PROVIDER_URI|eth rpc endpoint|
|ALPHASEA_CONTRACT_ADDRESS|alphasea eth contract address|
|ALPHASEA_CONTRACT_ABI|alphasea eth contract ABI|
|ALPHASEA_DEFAULT_TOURNAMENT_ID| 'crypto_daily' で固定 |
|ALPHASEA_PREDICTOR_PRICE_INCREASE_RATE| 前回の予測が一つ以上購入された場合に値上げする割合。0.1で10%値上げ |
|ALPHASEA_PREDICTOR_PRICE_DECREASE_RATE| 前回の予測が一個も購入されなかった場合に値下げする割合。0.1で10%値下げ |
|ALPHASEA_PREDICTOR_PRICE_MIN_ETH|価格の最小値(単位ETH)|
|ALPHASEA_EXECUTOR_SYMBOL_WHITE_LIST|モデル選択で使う銘柄ホワイトリスト|
|ALPHASEA_EXECUTOR_EXECUTION_COST|モデル選択で使う取引コスト|
|ALPHASEA_EXECUTOR_ASSETS_ETH|モデル選択で使う運用資産額(単位ETH)|
|ALPHASEA_EXECUTOR_BUDGET_RATE|予測購入予算(ウォレットETH残高に対する割合)。これをゼロにすると購入が発生しない|
|ALPHASEA_EXECUTOR_EVALUATION_PERIODS|モデル選択で使う過去成績の数|

## API docs

以下でエージェントを立ち上げ

```bash
docker-compose -f docker-compose-dev.yml up -d
```

以下を開く

- [http://localhost:8070/docs](http://localhost:8070/docs)
- [http://localhost:8070/redoc](http://localhost:8070/docs)

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
docker-compose -f docker-compose-dev.yml run --rm dev_agent bash scripts/test.sh
```

### lint

```bash
docker-compose -f docker-compose-dev.yml run --rm dev_agent flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
docker-compose -f docker-compose-dev.yml run --rm dev_agent flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
```

### CI

github actionsでtestとlintを行っている。

設定: .github/workflows/python-app.yml

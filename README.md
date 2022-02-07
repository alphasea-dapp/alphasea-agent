## alphasea-agent

alphasea-agentは、AlphaSeaスマートコントラクトを、
シンプルなインターフェースで扱えるようにするためのHTTPサーバーです。

[alphasea-example-model](https://github.com/alphasea-dapp/alphasea-example-model) と
[alphasea-trade-bot](https://github.com/alphasea-dapp/alphasea-trade-bot) を動かすために必要です。

[AlphaSeaの仕組み](https://alphasea.io/how-it-works/) も参考にしてください。

## 機能

HTTP APIインターフェース (デフォルトポート: 8070)

- 予測提出
- メタモデルのポジション取得

エージェントの動き

- 提出された予測をスマートコントラクトに投稿
- メタモデルが共有すると判断した予測をスマートコントラクト経由で共有
- メタモデルのポジションを計算する

## 準備

agentを動かすには、dockerとdocker-composeが必要です。
インストールしてください。

## agentのインストール

alphasea-agentをクローンします。

```bash
git clone https://github.com/alphasea-dapp/alphasea-agent
```

以降の作業はクローンしたディレクトリ内で行います。

## agentの動かし方

### 秘密鍵を用意

agentの稼働にはPolygon(MATIC)ウォレットが必要です。

alphasea-agentのディレクトリで、
以下のコマンドを実行し、agentで使うPolygonウォレットの秘密鍵を生成します。
ウォレット暗号化のパスフレーズはdefault_wallet_password内に記載されたものが使われます。
デフォルトのalphasea_passwordのままでも変えても良いと思います。

```bash
docker run --rm -v "$(pwd)/default_wallet_password:/default_wallet_password:ro" -v "$(pwd)/data/keystore:/root/.ethereum/keystore" ethereum/client-go account new --password /default_wallet_password
```

上記を実行すると、data/keystoreに秘密鍵が保存されます。
以下のコマンドで確認できます。
data/keystoreの秘密鍵を消したり漏らしたりすると資産を失うので注意してください。

```bash
docker run --rm -v "$(pwd)/data/keystore:/root/.ethereum/keystore:ro" ethereum/client-go account list
```

参考: [アカウント操作について ethereum.org](https://geth.ethereum.org/docs/interface/managing-your-accounts)

### ウォレットにMATICを入れる

alphasea-agentは動作にMATICが必要です(gas代用)。
MATICはPolygonの基本の通貨で、
ethereumのETHに相当します。
取引所からの送金などで入れると良いと思います。
送金先アドレスは前項の手順で確認できます。

### agentを起動

以下のコマンドを実行し、agentを起動します。

```bash
docker-compose up -d
```

起動すると8070ポートでHTTPリクエストを受け付けるようになります。
試しに以下のコマンドでメタモデルポジションを取得してみます。
動作確認なので、curlコマンドが無い場合は、この手順は飛ばしても良いです。

```bash
curl 'http://localhost:8070/target_positions.csv?timestamp=1640962800&tournament_id=crypto_daily'
```

以下のような出力が表示されれば成功です。
これは指定したtimestamp時点でのメタモデルポジションを表します。
この時点では、予測が共有されていないので、中身は空です。

```bash
symbol,position
```

以下のコマンドで、agentのログを確認できます。

```bash
docker-compose logs -f polygon_agent
```

以上で、agentのセットアップは完了です。

## agentの使い方

### Predictorを行う場合

Predictorを行う場合は、
[alphasea-example-model](https://github.com/alphasea-dapp/alphasea-example-model) を動かす必要があります。
これは、Numeraiのexample modelに相当するものです。
毎ラウンド、agentに対して予測を提出します。
動かし方はリンク先を見てください。

### Executorを行う場合

Executorを行う場合は、
[alphasea-trade-bot](https://github.com/alphasea-dapp/alphasea-trade-bot) を動かす必要があります。
これは、定期的にagentからメタモデルポジションを取得し、
仮想通貨取引所の無期限先物(Perpetual)のポジションを自動でリバランスするボットです。
動かし方はリンク先を見てください。

## Settings

environment variables (defined in docker-compose.yml)

|name|description|
|:-:|:-:|
|WEB3_PROVIDER_URI|polygon rpc endpoint|
|ALPHASEA_CONTRACT_ADDRESS|alphasea polygon contract address|
|ALPHASEA_CONTRACT_ABI|alphasea polygon contract ABI|
|ALPHASEA_EXECUTOR_SYMBOL_WHITE_LIST|モデル選択で使う銘柄ホワイトリスト|
|ALPHASEA_EXECUTOR_EXECUTION_COST|モデル選択で使う取引コスト|
|ALPHASEA_EXECUTOR_EVALUATION_PERIODS|モデル選択で使う過去成績の数|
|ALPHASEA_EXECUTOR_SCORE_THRESHOLD|予測を共有する基準|
|ALPHASEA_MAX_PRIORITY_FEE_SCALE|maxPriorityFeePerGasを設定した値倍にする。トランザクション遅延対策|

## Development

### API docs

以下でエージェントを立ち上げ

```bash
docker-compose -f docker-compose-dev.yml up -d
```

以下を開く

- [http://localhost:8070/docs](http://localhost:8070/docs)
- [http://localhost:8070/redoc](http://localhost:8070/docs)

### abi

docker-compose-dev.yml内の以下を設定する必要がある。
ALPHASEA_CONTRACT_ADDRESS
ALPHASEA_CONTRACT_ABI

ALPHASEA_CONTRACT_ABIはalphaseaリポジトリでnpm run print_abiで取得した文字列を設定すれば良い。

### testnet

testnet (mumbai)

```bash
docker-compose -f docker-compose-mumbai.yml up -d
```

### test

hardhat nodeに依存するので、
alphaseaリポジトリでnpx hardhat nodeを立ち上げてから実行。

```bash
docker-compose -f docker-compose-dev.yml run --rm dev_agent bash scripts/test.sh
```

mumbai testnetを使ったテスト。
mumbai用のMATICの入ったウォレットが必要。

```bash
docker-compose -f docker-compose-mumbai.yml run --rm mumbai_agent python -m unittest discover -s testnet_tests
```

### lint

```bash
docker-compose -f docker-compose-dev.yml run --rm dev_agent flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
docker-compose -f docker-compose-dev.yml run --rm dev_agent flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
```

### CI

github actionsでtestとlintを行っている。

設定: .github/workflows/python-app.yml

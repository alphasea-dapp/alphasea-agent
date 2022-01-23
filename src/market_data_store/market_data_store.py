from collections import defaultdict
import threading
import pandas as pd
from ..logger import create_null_logger


class MarketDataStore:
    def __init__(self, data_fetcher_builder=None, logger=None, start_time=None,
                 execution_lag_sec=None, execution_time_sec=None):
        self.fetcher_builder = data_fetcher_builder
        self.dfs = {}
        self.locks = defaultdict(threading.Lock)
        self.locks_lock = threading.Lock()
        self.logger = create_null_logger() if logger is None else logger
        self.start_time = start_time
        self._execution_lag_sec = execution_lag_sec
        self._execution_time_sec = execution_time_sec

    def fetch_df_market(self, symbols=None):
        dfs = []
        for symbol in symbols:
            df = self._get_df_ohlcv(
                exchange='ftx',
                market=symbol + '-PERP',
                interval=300,
                price_type='index',
                force_fetch=True
            )

            df = df.reset_index()
            shift = pd.to_timedelta(self._execution_lag_sec, unit='S')
            df['execution_start_at'] = (df['timestamp'] - shift).dt.floor(
                '{}S'.format(self._execution_time_sec)) + shift
            df['execution_start_at'] = df['execution_start_at'].astype(int) // (10 ** 9)
            df = pd.concat([
                df.groupby(['execution_start_at'])['cl'].mean().rename('twap'),
            ], axis=1)
            df['ret'] = df['twap'].shift(-24 // (self._execution_time_sec // (60 * 60))) / df['twap'] - 1
            df = df.drop(columns='twap')
            df = df.dropna()

            df = df.reset_index()
            df['symbol'] = symbol
            df = df.set_index(['execution_start_at', 'symbol'])
            dfs.append(df)

        df = pd.concat(dfs)
        df = df.sort_index()
        return df

    def _get_df_ohlcv(self, exchange=None, market=None, interval=None, price_type=None, force_fetch=False):
        self.logger.info('get_df_ohlcv {} {} {} {}'.format(exchange, market, interval, price_type))

        key = 'ohlcv,exchange={},market={},interval={},price_type={}'.format(exchange, market, interval, price_type)
        fetcher = self.fetcher_builder.create_fetcher(exchange=exchange, logger=self.logger)

        with self._get_lock(key):
            df = self.dfs.get(key)

            if force_fetch or df is None:
                df = fetcher.fetch_ohlcv(
                    df=df,
                    start_time=self.start_time,
                    interval_sec=interval,
                    market=market,
                    price_type=price_type
                )

                self.dfs[key] = df

            if df is not None:
                df = df.copy()

        return df

    def _get_lock(self, key):
        with self.locks_lock:
            return self.locks[key]

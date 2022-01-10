from unittest import TestCase
import pandas as pd
from pandas.testing import assert_frame_equal
from src.market_data_store.data_fetcher_builder import DataFetcherBuilder
from src.market_data_store.market_data_store import MarketDataStore


class TestMarketDataStore(TestCase):
    def test_ok(self):
        start_time = pd.to_datetime('2022-01-01 00:00:00')

        market_data_store = MarketDataStore(
            data_fetcher_builder=DataFetcherBuilder(),
            start_time=start_time
        )
        df = market_data_store.fetch_df_market(
            symbols=['BTC', 'ETH']
        )

        print(df)

        expected = pd.DataFrame(
            [
                [int(start_time.timestamp()), 'BTC', 0.024451540423388263],
                [int(start_time.timestamp()), 'ETH', 0.0164282793151036],
            ],
            columns=['execution_start_at', 'symbol', 'ret'],
        ).set_index(['execution_start_at', 'symbol'])

        print(expected)

        df = df.loc[df.index.get_level_values('execution_start_at') == start_time.timestamp()]
        assert_frame_equal(df, expected)

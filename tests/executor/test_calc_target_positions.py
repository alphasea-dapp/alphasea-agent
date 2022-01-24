import pandas as pd
from pandas.testing import assert_frame_equal
from unittest import TestCase
from src.executor.utils import calc_target_positions

df_blended_list1 = [
    pd.DataFrame([
        ['ETH', 0.2],
        ['BTC', 0.1],
    ], columns=['symbol', 'position']).set_index(['symbol']),
    pd.DataFrame([
        ['ETH', 0.4],
        ['BTC', 0.2],
    ], columns=['symbol', 'position']).set_index(['symbol']),
    pd.DataFrame([
        ['XRP', 0.1],
        ['BTC', 0.3],
    ], columns=['symbol', 'position']).set_index(['symbol'])
]


class TestExecutorCalcTargetPositions(TestCase):
    def test_zero(self):
        result = calc_target_positions(
            0.0,
            df_blended_list=df_blended_list1
        )
        expected = pd.DataFrame([
            ['BTC', 0.15],
            ['ETH', 0.3],
            ['XRP', 0.0],
        ], columns=['symbol', 'position']).set_index(['symbol'])
        assert_frame_equal(result, expected)

    def test_half(self):
        result = calc_target_positions(
            0.5,
            df_blended_list=df_blended_list1
        )
        expected = pd.DataFrame([
            ['BTC', 0.2],
            ['ETH', 0.25],
            ['XRP', 0.025],
        ], columns=['symbol', 'position']).set_index(['symbol'])
        assert_frame_equal(result, expected)

    def test_one(self):
        result = calc_target_positions(
            1.0,
            df_blended_list=df_blended_list1
        )
        expected = pd.DataFrame([
            ['BTC', 0.25],
            ['ETH', 0.2],
            ['XRP', 0.05],
        ], columns=['symbol', 'position']).set_index(['symbol'])
        assert_frame_equal(result, expected)

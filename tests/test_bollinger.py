"""indicators/bollinger.py 단위 테스트"""
from __future__ import annotations

import pandas as pd
import pytest

from indicators.bollinger import add_bollinger, get_bb_signal
from tests.conftest import make_ohlcv


class TestAddBollinger:
    def test_adds_band_columns(self, sample_df):
        result = add_bollinger(sample_df)
        assert "BB_upper" in result.columns
        assert "BB_lower" in result.columns
        assert "BB_mid" in result.columns

    def test_upper_greater_than_lower(self, sample_df):
        result = add_bollinger(sample_df)
        valid = result.dropna()
        assert (valid["BB_upper"] > valid["BB_lower"]).all()

    def test_mid_equals_rolling_mean(self, sample_df):
        result = add_bollinger(sample_df, period=20)
        expected = sample_df["Close"].rolling(20).mean()
        pd.testing.assert_series_equal(result["BB_mid"], expected, check_names=False)

    def test_does_not_mutate_original(self, sample_df):
        cols = list(sample_df.columns)
        add_bollinger(sample_df)
        assert list(sample_df.columns) == cols


class TestGetBbSignal:
    def test_returns_zeros_without_band_columns(self, sample_df):
        result = get_bb_signal(sample_df)
        assert (result == 0).all()

    def test_buy_when_close_at_lower_band(self):
        dates = pd.date_range("2024-01-01", periods=3, freq="B")
        df = pd.DataFrame(
            {
                "Close":    [100.0, 80.0, 110.0],
                "BB_upper": [120.0, 120.0, 120.0],
                "BB_lower": [ 90.0,  90.0,  90.0],
            },
            index=dates,
        )
        signal = get_bb_signal(df)
        assert signal.iloc[0] == 0   # 밴드 내부 → HOLD
        assert signal.iloc[1] == 1   # 하단 터치 → BUY
        assert signal.iloc[2] == 0   # 밴드 내부 → HOLD

    def test_sell_when_close_at_upper_band(self):
        dates = pd.date_range("2024-01-01", periods=2, freq="B")
        df = pd.DataFrame(
            {
                "Close":    [120.0, 130.0],
                "BB_upper": [120.0, 120.0],
                "BB_lower": [ 80.0,  80.0],
            },
            index=dates,
        )
        signal = get_bb_signal(df)
        assert signal.iloc[0] == -1  # 상단 터치 → SELL
        assert signal.iloc[1] == -1

    def test_only_valid_signal_values(self, sample_df):
        df = add_bollinger(sample_df)
        signal = get_bb_signal(df)
        assert set(signal.unique()).issubset({-1, 0, 1})

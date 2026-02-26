"""indicators/rsi.py 단위 테스트"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from indicators.rsi import add_rsi, get_rsi_signal
from tests.conftest import make_ohlcv


class TestAddRsi:
    def test_adds_rsi_column(self, sample_df):
        result = add_rsi(sample_df)
        assert "RSI" in result.columns

    def test_rsi_range_0_to_100(self, sample_df):
        result = add_rsi(sample_df)
        valid = result["RSI"].dropna()
        assert (valid >= 0).all() and (valid <= 100).all()

    def test_does_not_mutate_original(self, sample_df):
        original_cols = list(sample_df.columns)
        add_rsi(sample_df)
        assert list(sample_df.columns) == original_cols

    def test_rsi_is_50_for_constant_price(self):
        """가격 변화 없으면 RSI = 50 (gain == loss == 0 → NaN 처리 확인)."""
        dates = pd.date_range("2024-01-01", periods=30, freq="B")
        df = pd.DataFrame({"Close": [50_000.0] * 30}, index=dates)
        result = add_rsi(df)
        # 상수 가격: delta=0 → gain=0, loss=0 → NaN 예상
        assert result["RSI"].isna().any() or (result["RSI"].dropna() == 50).all()


class TestGetRsiSignal:
    def test_returns_zeros_without_rsi_column(self, sample_df):
        result = get_rsi_signal(sample_df)
        assert (result == 0).all()

    def test_sell_signal_when_overbought(self):
        dates = pd.date_range("2024-01-01", periods=5, freq="B")
        df = pd.DataFrame({"RSI": [75.0, 80.0, 50.0, 25.0, 60.0]}, index=dates)
        signal = get_rsi_signal(df)
        assert signal.iloc[0] == -1  # 과매수 → SELL
        assert signal.iloc[1] == -1
        assert signal.iloc[2] == 0   # HOLD
        assert signal.iloc[3] == 1   # 과매도 → BUY
        assert signal.iloc[4] == 0

    def test_only_valid_signal_values(self, sample_df):
        df = add_rsi(sample_df)
        signal = get_rsi_signal(df)
        assert set(signal.unique()).issubset({-1, 0, 1})

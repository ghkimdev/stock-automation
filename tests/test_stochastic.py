"""indicators/stochastic.py 단위 테스트"""
from __future__ import annotations

import pandas as pd
import pytest
from indicators.stochastic import add_stochastic, get_stoch_signal
from tests.conftest import make_ohlcv


class TestAddStochastic:
    def test_adds_stoch_columns(self, sample_df):
        result = add_stochastic(sample_df)
        assert "Stoch_K" in result.columns
        assert "Stoch_D" in result.columns

    def test_stoch_k_range_0_to_100(self, sample_df):
        result = add_stochastic(sample_df)
        valid = result["Stoch_K"].dropna()
        assert (valid >= 0).all() and (valid <= 100).all()

    def test_does_not_mutate_original(self, sample_df):
        cols = list(sample_df.columns)
        add_stochastic(sample_df)
        assert list(sample_df.columns) == cols


class TestGetStochSignal:
    def test_returns_zeros_without_stoch_columns(self, sample_df):
        result = get_stoch_signal(sample_df)
        assert (result == 0).all()

    def test_only_valid_values(self, sample_df):
        df = add_stochastic(sample_df)
        signal = get_stoch_signal(df)
        assert set(signal.unique()).issubset({-1, 0, 1})

    def test_buy_signal_in_oversold_crossover(self):
        """과매도 영역에서 %K가 %D 상향 돌파 → BUY (크로스는 인덱스 2에서 발생)."""
        dates = pd.date_range("2024-01-01", periods=4, freq="B")
        # idx0: K<D, idx1: K<D, idx2: K>D (크로스 발생), idx3: K>D
        df = pd.DataFrame(
            {"Stoch_K": [10.0, 12.0, 14.0, 16.0],
             "Stoch_D": [15.0, 14.0, 13.0, 12.0]},
            index=dates,
        )
        signal = get_stoch_signal(df)
        assert signal.iloc[2] == 1  # idx2: prev_K(12)<prev_D(14), curr_K(14)>=curr_D(13)

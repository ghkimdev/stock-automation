"""indicators/macd.py 단위 테스트"""
from __future__ import annotations

import pandas as pd
import pytest

from indicators.macd import add_macd, detect_macd_cross
from tests.conftest import make_ohlcv


class TestAddMacd:
    def test_adds_macd_columns(self, sample_df):
        result = add_macd(sample_df)
        assert "MACD" in result.columns
        assert "MACD_signal" in result.columns

    def test_macd_is_ema_diff(self, sample_df):
        result = add_macd(sample_df, fast=12, slow=26)
        ema12 = sample_df["Close"].ewm(span=12, adjust=False).mean()
        ema26 = sample_df["Close"].ewm(span=26, adjust=False).mean()
        expected = ema12 - ema26
        pd.testing.assert_series_equal(result["MACD"], expected, check_names=False)

    def test_does_not_mutate_original(self, sample_df):
        cols = list(sample_df.columns)
        add_macd(sample_df)
        assert list(sample_df.columns) == cols


class TestDetectMacdCross:
    def test_returns_zeros_without_macd_columns(self, sample_df):
        result = detect_macd_cross(sample_df)
        assert (result == 0).all()

    def test_only_valid_values(self, sample_df):
        df = add_macd(sample_df)
        cross = detect_macd_cross(df)
        assert set(cross.unique()).issubset({-1, 0, 1})

    def test_golden_cross_on_known_data(self):
        """MACD가 시그널선을 상향 돌파하는 케이스를 직접 구성."""
        dates = pd.date_range("2024-01-01", periods=4, freq="B")
        # prev: MACD < signal, curr: MACD >= signal
        df = pd.DataFrame(
            {"MACD": [-1.0, -0.5, 0.1, 0.5], "MACD_signal": [0.0, 0.0, 0.0, 0.0]},
            index=dates,
        )
        cross = detect_macd_cross(df)
        assert cross.iloc[2] == 1  # 인덱스2에서 골든크로스

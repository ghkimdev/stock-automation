"""indicators/moving_average.py 단위 테스트"""
from __future__ import annotations

import pandas as pd
import pytest

from indicators.moving_average import add_ma, detect_crossover
from tests.conftest import make_ohlcv, golden_cross_df  # noqa: F401


class TestAddMa:
    def test_adds_default_columns(self, sample_df):
        result = add_ma(sample_df)
        assert "MA5" in result.columns
        assert "MA20" in result.columns
        assert "MA60" in result.columns

    def test_custom_windows(self, sample_df):
        result = add_ma(sample_df, windows=[10, 30])
        assert "MA10" in result.columns
        assert "MA30" in result.columns
        assert "MA5" not in result.columns

    def test_ma5_equals_manual_rolling(self, sample_df):
        result = add_ma(sample_df)
        expected = sample_df["Close"].rolling(5).mean()
        pd.testing.assert_series_equal(result["MA5"], expected, check_names=False)

    def test_does_not_mutate_original(self, sample_df):
        original_cols = list(sample_df.columns)
        add_ma(sample_df)
        assert list(sample_df.columns) == original_cols


class TestDetectCrossover:
    def test_returns_zeros_without_ma_columns(self, sample_df):
        result = detect_crossover(sample_df)
        assert (result == 0).all()

    def test_golden_cross_detected(self, golden_cross_df):
        df = add_ma(golden_cross_df)
        cross = detect_crossover(df)
        assert (cross == 1).any(), "골든크로스가 감지되어야 합니다"

    def test_only_plus_minus_one_or_zero(self, sample_df):
        df = add_ma(sample_df)
        cross = detect_crossover(df)
        assert set(cross.unique()).issubset({-1, 0, 1})

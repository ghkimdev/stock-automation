"""indicators/adx.py 단위 테스트"""
from __future__ import annotations

import pandas as pd
import pytest
from indicators.adx import add_adx, add_volume_ma, is_trending, is_volume_confirmed
from tests.conftest import make_ohlcv


class TestAddAdx:
    def test_adds_adx_columns(self, sample_df):
        result = add_adx(sample_df)
        assert "ADX" in result.columns
        assert "Plus_DI" in result.columns
        assert "Minus_DI" in result.columns

    def test_adx_is_non_negative(self, sample_df):
        result = add_adx(sample_df)
        assert (result["ADX"].dropna() >= 0).all()

    def test_does_not_mutate_original(self, sample_df):
        cols = list(sample_df.columns)
        add_adx(sample_df)
        assert list(sample_df.columns) == cols


class TestAddVolumeMa:
    def test_adds_volume_ma_column(self, sample_df):
        result = add_volume_ma(sample_df)
        assert "Volume_MA" in result.columns

    def test_volume_ma_equals_rolling_mean(self, sample_df):
        result = add_volume_ma(sample_df, period=20)
        expected = sample_df["Volume"].rolling(20).mean()
        pd.testing.assert_series_equal(result["Volume_MA"], expected, check_names=False)


class TestIsTrending:
    def test_returns_true_without_adx_column(self, sample_df):
        result = is_trending(sample_df)
        assert result.all()

    def test_trending_above_threshold(self):
        dates = pd.date_range("2024-01-01", periods=3, freq="B")
        df = pd.DataFrame({"ADX": [15.0, 20.0, 30.0]}, index=dates)
        result = is_trending(df, threshold=20)
        assert not result.iloc[0]   # 15 < 20 → 횡보
        assert result.iloc[1]       # 20 >= 20 → 추세
        assert result.iloc[2]       # 30 >= 20 → 추세


class TestIsVolumeConfirmed:
    def test_returns_true_without_volume_ma(self, sample_df):
        result = is_volume_confirmed(sample_df)
        assert result.all()

    def test_confirmed_when_volume_above_ma(self):
        dates = pd.date_range("2024-01-01", periods=3, freq="B")
        df = pd.DataFrame(
            {"Volume": [500, 1000, 1500], "Volume_MA": [1000.0, 1000.0, 1000.0]},
            index=dates,
        )
        result = is_volume_confirmed(df)
        assert not result.iloc[0]   # 500 < 1000
        assert result.iloc[1]       # 1000 >= 1000
        assert result.iloc[2]       # 1500 >= 1000

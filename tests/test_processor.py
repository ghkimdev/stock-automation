"""data/processor.py 단위 테스트"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from data.processor import InsufficientDataError, clean, validate
from tests.conftest import make_ohlcv


class TestClean:
    def test_removes_nan_rows(self):
        df = make_ohlcv(10)
        df.iloc[2, df.columns.get_loc("Close")] = np.nan
        result = clean(df)
        assert len(result) == 9
        assert result.isna().sum().sum() == 0

    def test_casts_price_columns_to_float(self):
        df = make_ohlcv(10).astype(object)
        result = clean(df)
        for col in ["Open", "High", "Low", "Close"]:
            assert result[col].dtype == float

    def test_casts_volume_to_int(self):
        df = make_ohlcv(10)
        result = clean(df)
        assert result["Volume"].dtype == int

    def test_does_not_mutate_original(self):
        df = make_ohlcv(10)
        original_len = len(df)
        df.iloc[0, df.columns.get_loc("Close")] = np.nan
        clean(df)
        assert len(df) == original_len  # 원본 불변


class TestValidate:
    def test_passes_with_enough_rows(self, sample_df):
        assert validate(sample_df) is True

    def test_raises_with_too_few_rows(self, small_df):
        with pytest.raises(InsufficientDataError):
            validate(small_df)

    def test_custom_min_rows(self):
        df = make_ohlcv(n=10)
        assert validate(df, min_rows=5) is True
        with pytest.raises(InsufficientDataError):
            validate(df, min_rows=20)

"""indicators/atr.py 단위 테스트"""
from __future__ import annotations

import pytest
from indicators.atr import add_atr, get_stop_and_target
from tests.conftest import make_ohlcv


class TestAddAtr:
    def test_adds_atr_column(self, sample_df):
        result = add_atr(sample_df)
        assert "ATR" in result.columns

    def test_atr_is_positive(self, sample_df):
        result = add_atr(sample_df)
        assert (result["ATR"].dropna() > 0).all()

    def test_does_not_mutate_original(self, sample_df):
        cols = list(sample_df.columns)
        add_atr(sample_df)
        assert list(sample_df.columns) == cols


class TestGetStopAndTarget:
    def test_buy_stop_below_price(self):
        stop, target = get_stop_and_target(100.0, 5.0, "BUY")
        assert stop < 100.0
        assert target > 100.0

    def test_sell_stop_above_price(self):
        stop, target = get_stop_and_target(100.0, 5.0, "SELL")
        assert stop > 100.0
        assert target < 100.0

    def test_risk_reward_ratio(self):
        price, atr = 50_000.0, 1_000.0
        stop, target = get_stop_and_target(price, atr, "BUY", stop_mult=1.5, target_mult=3.0)
        risk   = price - stop
        reward = target - price
        assert abs(reward / risk - 2.0) < 0.01  # RR = 2:1

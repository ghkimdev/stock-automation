"""backtest/engine.py 단위 테스트"""
from __future__ import annotations

from datetime import date
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from backtest.engine import BacktestResult, _calc_max_drawdown, run
from signals.generator import Signal, SignalType
from tests.conftest import make_ohlcv


class TestCalcMaxDrawdown:
    def test_no_drawdown(self):
        assert _calc_max_drawdown([100.0, 110.0, 120.0]) == 0.0

    def test_simple_drawdown(self):
        # 100 → 80 → 90: MDD = (100-80)/100 = 20%
        result = _calc_max_drawdown([100.0, 80.0, 90.0])
        assert abs(result - 20.0) < 0.01

    def test_empty_curve(self):
        assert _calc_max_drawdown([]) == 0.0

    def test_recovery_after_drawdown(self):
        # 100 → 50 → 150: MDD = 50%
        result = _calc_max_drawdown([100.0, 50.0, 150.0])
        assert abs(result - 50.0) < 0.01


class TestBacktestRun:
    def _make_signals(self, df: pd.DataFrame, ticker: str = "TEST") -> list[Signal]:
        """테스트용 신호 목록 생성."""
        idx = df.index
        return [
            Signal(
                ticker=ticker,
                date=idx[20].date(),
                signal=SignalType.BUY,
                reason="테스트 BUY",
                price=float(df["Close"].iloc[20]),
                stop_loss=float(df["Close"].iloc[20]) * 0.95,
                target=float(df["Close"].iloc[20]) * 1.10,
            ),
            Signal(
                ticker=ticker,
                date=idx[60].date(),
                signal=SignalType.SELL,
                reason="테스트 SELL",
                price=float(df["Close"].iloc[60]),
                stop_loss=None,
                target=None,
            ),
        ]

    def test_returns_backtest_result(self):
        df = make_ohlcv(120)
        signals = self._make_signals(df)
        with patch("backtest.engine.fetch_ohlcv", return_value=df), \
             patch("backtest.engine.generate", return_value=signals):
            result = run("TEST", "2024-01-01", "2024-12-31")
        assert isinstance(result, BacktestResult)

    def test_trade_count_correct(self):
        df = make_ohlcv(120)
        signals = self._make_signals(df)
        with patch("backtest.engine.fetch_ohlcv", return_value=df), \
             patch("backtest.engine.generate", return_value=signals):
            result = run("TEST", "2024-01-01", "2024-12-31")
        assert result.trade_count >= 1

    def test_stop_loss_triggered(self):
        """진입 다음날 저가가 손절가 아래 → stop_loss_hits 증가."""
        df = make_ohlcv(120)
        entry_price = float(df["Close"].iloc[20])
        stop = entry_price * 0.99  # 타이트한 손절 (1%)

        # 진입 다음날 저가를 손절가 아래로 강제 설정
        df = df.copy()
        df.iloc[21, df.columns.get_loc("Low")] = stop * 0.98

        signals = [
            Signal(
                ticker="TEST",
                date=df.index[20].date(),
                signal=SignalType.BUY,
                reason="BUY",
                price=entry_price,
                stop_loss=stop,
                target=entry_price * 1.10,
            )
        ]
        with patch("backtest.engine.fetch_ohlcv", return_value=df), \
             patch("backtest.engine.generate", return_value=signals):
            result = run("TEST", "2024-01-01", "2024-12-31")
        assert result.stop_loss_hits == 1

    def test_target_hit(self):
        """진입 다음날 고가가 목표가 이상 → target_hits 증가."""
        df = make_ohlcv(120)
        entry_price = float(df["Close"].iloc[20])
        target = entry_price * 1.01  # 타이트한 목표 (1%)

        df = df.copy()
        df.iloc[21, df.columns.get_loc("High")] = target * 1.02

        signals = [
            Signal(
                ticker="TEST",
                date=df.index[20].date(),
                signal=SignalType.BUY,
                reason="BUY",
                price=entry_price,
                stop_loss=entry_price * 0.90,
                target=target,
            )
        ]
        with patch("backtest.engine.fetch_ohlcv", return_value=df), \
             patch("backtest.engine.generate", return_value=signals):
            result = run("TEST", "2024-01-01", "2024-12-31")
        assert result.target_hits == 1

    def test_max_drawdown_non_negative(self):
        df = make_ohlcv(120)
        signals = self._make_signals(df)
        with patch("backtest.engine.fetch_ohlcv", return_value=df), \
             patch("backtest.engine.generate", return_value=signals):
            result = run("TEST", "2024-01-01", "2024-12-31")
        assert result.max_drawdown >= 0.0

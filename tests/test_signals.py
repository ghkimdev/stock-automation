"""signals/generator.py 단위 테스트"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from data.processor import clean, validate
from signals.generator import Signal, SignalType, generate, print_signals
from tests.conftest import make_ohlcv


class TestGenerate:
    def test_returns_list_of_signals(self, sample_df):
        df = clean(sample_df)
        result = generate(df, "TEST")
        assert isinstance(result, list)
        assert all(isinstance(s, Signal) for s in result)

    def test_signal_types_are_buy_or_sell(self, sample_df):
        df = clean(sample_df)
        result = generate(df, "TEST")
        for s in result:
            assert s.signal in (SignalType.BUY, SignalType.SELL)

    def test_signal_has_correct_ticker(self, sample_df):
        df = clean(sample_df)
        result = generate(df, "SAMSUNG")
        for s in result:
            assert s.ticker == "SAMSUNG"

    def test_empty_df_returns_empty_list(self):
        df = pd.DataFrame(columns=["Open", "High", "Low", "Close", "Volume"])
        result = generate(df, "EMPTY")
        assert result == []

    def test_majority_vote_buy(self):
        """BUY 지표 2개 이상 → BUY 신호 발생 시나리오."""
        # RSI 과매도 + 볼린저 하단 조건을 직접 주입
        dates = pd.date_range("2024-01-01", periods=100, freq="B")
        np.random.seed(0)
        close = np.ones(100) * 50_000
        close[-1] = 30_000  # 급락 → RSI 과매도 + BB 하단 터치 유도
        df = pd.DataFrame(
            {
                "Open": close * 0.99, "High": close * 1.01,
                "Low": close * 0.98, "Close": close,
                "Volume": np.ones(100, dtype=int) * 1_000_000,
            },
            index=dates,
        )
        df = clean(df)
        signals = generate(df, "TEST")
        buy_signals = [s for s in signals if s.signal == SignalType.BUY]
        assert len(buy_signals) > 0


class TestPrintSignals:
    def test_prints_no_signal_message(self, capsys):
        print_signals([])
        captured = capsys.readouterr()
        assert "신호 없음" in captured.out

    def test_prints_buy_signal(self, capsys):
        from datetime import date
        signals = [
            Signal(
                ticker="TEST",
                date=date(2024, 1, 15),
                signal=SignalType.BUY,
                reason="RSI 과매도",
                price=48_000.0,
            )
        ]
        print_signals(signals)
        captured = capsys.readouterr()
        assert "BUY" in captured.out
        assert "48,000" in captured.out

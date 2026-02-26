from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

import pandas as pd

from config import DEFAULT_CAPITAL
from data.fetcher import fetch_ohlcv
from data.processor import clean, validate
from signals.generator import Signal, SignalType, generate
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class BacktestResult:
    ticker: str
    start_date: date
    end_date: date
    total_return: float
    trade_count: int
    win_rate: float
    signals: list[Signal] = field(default_factory=list)


def run(
    ticker: str,
    start: str,
    end: str,
    initial_capital: float = DEFAULT_CAPITAL,
) -> BacktestResult:
    """
    지정 기간 동안 신호 기반 매매 시뮬레이션을 실행합니다.
    수익률, 승률, 매매 횟수를 반환합니다.
    """
    df = fetch_ohlcv(ticker, period="2y")
    df = clean(df)
    validate(df)

    # 기간 필터
    df = df.loc[start:end]
    if df.empty:
        logger.warning(f"{ticker}: 지정 기간 내 데이터 없음")
        return BacktestResult(
            ticker=ticker,
            start_date=date.fromisoformat(start),
            end_date=date.fromisoformat(end),
            total_return=0.0,
            trade_count=0,
            win_rate=0.0,
        )

    signals = generate(df, ticker)

    capital = initial_capital
    position = 0.0      # 보유 주식 수
    buy_price = 0.0
    wins = 0
    trades = 0

    for sig in signals:
        price = sig.price
        if sig.signal == SignalType.BUY and position == 0:
            position = capital / price
            buy_price = price
            capital = 0.0
            logger.debug(f"[백테스트] {sig.date} BUY @ {price:,.0f}")
        elif sig.signal == SignalType.SELL and position > 0:
            capital = position * price
            if price > buy_price:
                wins += 1
            trades += 1
            position = 0.0
            logger.debug(f"[백테스트] {sig.date} SELL @ {price:,.0f}")

    # 미청산 포지션 마지막 가격으로 정산
    if position > 0:
        final_price = float(df["Close"].iloc[-1])
        capital = position * final_price
        if final_price > buy_price:
            wins += 1
        trades += 1

    total_return = (capital - initial_capital) / initial_capital * 100
    win_rate = (wins / trades * 100) if trades > 0 else 0.0

    return BacktestResult(
        ticker=ticker,
        start_date=df.index[0].date(),
        end_date=df.index[-1].date(),
        total_return=round(total_return, 2),
        trade_count=trades,
        win_rate=round(win_rate, 2),
        signals=signals,
    )

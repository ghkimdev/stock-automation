from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional

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
    stop_loss_hits: int = 0     # 손절 청산 횟수
    target_hits: int = 0        # 목표가 달성 횟수
    max_drawdown: float = 0.0   # 최대 낙폭 (%)
    signals: list[Signal] = field(default_factory=list)


def _calc_max_drawdown(equity_curve: list[float]) -> float:
    """자본 곡선에서 최대 낙폭(MDD)을 계산합니다."""
    if not equity_curve:
        return 0.0
    peak = equity_curve[0]
    max_dd = 0.0
    for val in equity_curve:
        if val > peak:
            peak = val
        dd = (peak - val) / peak * 100
        if dd > max_dd:
            max_dd = dd
    return round(max_dd, 2)


def run(
    ticker: str,
    start: str,
    end: str,
    initial_capital: float = DEFAULT_CAPITAL,
) -> BacktestResult:
    """
    지정 기간 동안 신호 기반 매매 시뮬레이션을 실행합니다.

    진입: BUY 신호 발생 시
    청산 우선순위:
      1. 당일 Low ≤ stop_loss  → 손절 (stop_loss 가격에 청산)
      2. 당일 High ≥ target    → 목표가 달성 (target 가격에 청산)
      3. SELL 신호 발생         → 신호 가격에 청산
    """
    df = fetch_ohlcv(ticker, period="2y")
    df = clean(df)
    validate(df)

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
    # 날짜 → Signal 매핑 (빠른 조회)
    sig_map: dict[date, Signal] = {s.date: s for s in signals}

    capital = initial_capital
    position = 0.0
    entry_price = 0.0
    stop_loss: Optional[float] = None
    target: Optional[float] = None

    wins = 0
    trades = 0
    stop_loss_hits = 0
    target_hits = 0
    equity_curve: list[float] = []

    for idx, row in df.iterrows():
        row_date = idx.date() if hasattr(idx, "date") else idx
        low  = float(row["Low"])
        high = float(row["High"])
        close = float(row["Close"])
        current_value = capital + position * close
        equity_curve.append(current_value)

        # 포지션 보유 중: 손절/목표가 먼저 체크
        if position > 0 and stop_loss is not None:
            # 1. 손절 체크 (당일 저가가 손절가 이하)
            if low <= stop_loss:
                exit_price = stop_loss
                capital = position * exit_price
                logger.debug(f"[손절] {row_date} @ {exit_price:,.0f}")
                position = 0.0
                stop_loss_hits += 1
                trades += 1
                # 손절 → 진입가 대비 손실
                stop_loss = None
                target = None
                continue

            # 2. 목표가 체크 (당일 고가가 목표가 이상)
            if target is not None and high >= target:
                exit_price = target
                capital = position * exit_price
                logger.debug(f"[목표가] {row_date} @ {exit_price:,.0f}")
                wins += 1
                position = 0.0
                target_hits += 1
                trades += 1
                stop_loss = None
                target = None
                continue

        # 신호 처리
        sig = sig_map.get(row_date)
        if sig is None:
            continue

        if sig.signal == SignalType.BUY and position == 0:
            position = capital / sig.price
            entry_price = sig.price
            stop_loss = sig.stop_loss
            target = sig.target
            capital = 0.0
            logger.debug(
                f"[진입] {row_date} BUY @ {sig.price:,.0f} "
                f"손절: {stop_loss:,.0f} 목표: {target:,.0f}"
            )

        elif sig.signal == SignalType.SELL and position > 0:
            exit_price = sig.price
            capital = position * exit_price
            if exit_price > entry_price:
                wins += 1
            trades += 1
            position = 0.0
            stop_loss = None
            target = None
            logger.debug(f"[청산] {row_date} SELL @ {exit_price:,.0f}")

    # 미청산 포지션 마지막 종가로 정산
    if position > 0:
        final_price = float(df["Close"].iloc[-1])
        capital = position * final_price
        if final_price > entry_price:
            wins += 1
        trades += 1

    total_return = (capital - initial_capital) / initial_capital * 100

    return BacktestResult(
        ticker=ticker,
        start_date=df.index[0].date(),
        end_date=df.index[-1].date(),
        total_return=round(total_return, 2),
        trade_count=trades,
        win_rate=round((wins / trades * 100) if trades > 0 else 0.0, 2),
        stop_loss_hits=stop_loss_hits,
        target_hits=target_hits,
        max_drawdown=_calc_max_drawdown(equity_curve),
        signals=signals,
    )

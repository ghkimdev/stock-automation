from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Optional

import pandas as pd

from indicators.adx import add_adx, add_volume_ma, is_trending, is_volume_confirmed
from indicators.atr import add_atr, get_stop_and_target
from indicators.bollinger import add_bollinger, get_bb_signal
from indicators.macd import add_macd, detect_macd_cross
from indicators.moving_average import add_ma, detect_crossover
from indicators.rsi import add_rsi, get_rsi_signal
from indicators.stochastic import add_stochastic, get_stoch_signal
from utils.logger import get_logger

logger = get_logger(__name__)


class SignalType(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


@dataclass
class Signal:
    ticker: str
    date: date
    signal: SignalType
    reason: str
    price: float
    stop_loss: Optional[float] = field(default=None)   # ATR 기반 손절가
    target: Optional[float] = field(default=None)      # ATR 기반 목표가


def _add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """모든 지표를 DataFrame에 추가합니다."""
    df = add_ma(df)
    df = add_rsi(df)
    df = add_macd(df)
    df = add_bollinger(df)
    df = add_stochastic(df)
    df = add_atr(df)
    df = add_adx(df)
    df = add_volume_ma(df)
    return df


def generate(df: pd.DataFrame, ticker: str) -> list[Signal]:
    """
    모든 지표 신호를 종합하여 최종 Signal 리스트를 반환합니다.

    필터:
      - ADX < 20 (횡보장): 신호 무효 처리
      - 거래량 < 거래량MA: 신호 무효 처리
    다수결: 5개 지표 중 2개 이상 BUY → BUY, 2개 이상 SELL → SELL
    """
    df = _add_all_indicators(df)
    df = df.dropna()

    if df.empty:
        logger.warning(f"{ticker}: 지표 계산 후 유효 데이터 없음")
        return []

    ma_cross   = detect_crossover(df)
    rsi_sig    = get_rsi_signal(df)
    macd_cross = detect_macd_cross(df)
    bb_sig     = get_bb_signal(df)
    stoch_sig  = get_stoch_signal(df)
    trending   = is_trending(df)
    vol_ok     = is_volume_confirmed(df)

    signals: list[Signal] = []
    for idx in df.index:
        # 필터: 횡보장 or 거래량 부족 → 스킵
        if not trending.get(idx, True) or not vol_ok.get(idx, True):
            continue

        votes = [
            int(ma_cross.get(idx, 0)),
            int(rsi_sig.get(idx, 0)),
            int(macd_cross.get(idx, 0)),
            int(bb_sig.get(idx, 0)),
            int(stoch_sig.get(idx, 0)),
        ]
        score = sum(votes)

        reasons = []
        if ma_cross.get(idx, 0) == 1:    reasons.append("MA 골든크로스")
        elif ma_cross.get(idx, 0) == -1: reasons.append("MA 데드크로스")
        if rsi_sig.get(idx, 0) == 1:     reasons.append(f"RSI 과매도({df.loc[idx, 'RSI']:.1f})")
        elif rsi_sig.get(idx, 0) == -1:  reasons.append(f"RSI 과매수({df.loc[idx, 'RSI']:.1f})")
        if macd_cross.get(idx, 0) == 1:  reasons.append("MACD 골든크로스")
        elif macd_cross.get(idx, 0) == -1: reasons.append("MACD 데드크로스")
        if bb_sig.get(idx, 0) == 1:      reasons.append("BB 하단 터치")
        elif bb_sig.get(idx, 0) == -1:   reasons.append("BB 상단 터치")
        if stoch_sig.get(idx, 0) == 1:   reasons.append("스토캐스틱 BUY")
        elif stoch_sig.get(idx, 0) == -1: reasons.append("스토캐스틱 SELL")

        if score >= 2:
            sig_type = SignalType.BUY
        elif score <= -2:
            sig_type = SignalType.SELL
        else:
            continue

        price = float(df.loc[idx, "Close"])
        atr   = float(df.loc[idx, "ATR"])
        stop, target = get_stop_and_target(price, atr, sig_type.value)

        signals.append(
            Signal(
                ticker=ticker,
                date=idx.date() if hasattr(idx, "date") else idx,
                signal=sig_type,
                reason=", ".join(reasons) if reasons else "복합 신호",
                price=price,
                stop_loss=stop,
                target=target,
            )
        )

    return signals


def print_signals(signals: list[Signal]) -> None:
    """신호를 콘솔에 포맷팅하여 출력합니다."""
    if not signals:
        print("  신호 없음")
        return
    for s in signals:
        icon = "📈" if s.signal == SignalType.BUY else "📉"
        stop_str   = f"{s.stop_loss:>10,.0f}" if s.stop_loss is not None else "       N/A"
        target_str = f"{s.target:>10,.0f}"    if s.target    is not None else "       N/A"
        print(
            f"  {icon} [{s.date}] {s.signal.value:4s} | "
            f"진입: {s.price:>10,.0f} | "
            f"손절: {stop_str} | "
            f"목표: {target_str} | "
            f"{s.reason}"
        )

"""ATR (Average True Range) — 평균 변동폭 및 손절/목표가 계산"""
from __future__ import annotations

import pandas as pd

ATR_PERIOD: int = 14
ATR_STOP_MULT: float = 1.5   # 손절: 진입가 - ATR * 1.5
ATR_TARGET_MULT: float = 3.0  # 목표가: 진입가 + ATR * 3.0


def add_atr(df: pd.DataFrame, period: int = ATR_PERIOD) -> pd.DataFrame:
    """ATR 컬럼을 추가합니다."""
    df = df.copy()
    prev_close = df["Close"].shift(1)
    tr = pd.concat(
        [
            df["High"] - df["Low"],
            (df["High"] - prev_close).abs(),
            (df["Low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    df["ATR"] = tr.rolling(window=period).mean()
    return df


def get_stop_and_target(
    price: float,
    atr: float,
    signal: str,
    stop_mult: float = ATR_STOP_MULT,
    target_mult: float = ATR_TARGET_MULT,
) -> tuple[float, float]:
    """
    ATR 기반 손절가와 목표가를 반환합니다.

    BUY:  손절 = price - ATR * stop_mult,  목표 = price + ATR * target_mult
    SELL: 손절 = price + ATR * stop_mult,  목표 = price - ATR * target_mult
    """
    if signal == "BUY":
        stop = price - atr * stop_mult
        target = price + atr * target_mult
    else:
        stop = price + atr * stop_mult
        target = price - atr * target_mult
    return round(stop, 2), round(target, 2)

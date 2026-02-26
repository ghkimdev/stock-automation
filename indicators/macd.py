from __future__ import annotations

import pandas as pd

from config import MACD_FAST, MACD_SIGNAL, MACD_SLOW


def add_macd(
    df: pd.DataFrame,
    fast: int = MACD_FAST,
    slow: int = MACD_SLOW,
    signal: int = MACD_SIGNAL,
) -> pd.DataFrame:
    """MACD, MACD_signal 컬럼을 추가합니다."""
    df = df.copy()
    ema_fast = df["Close"].ewm(span=fast, adjust=False).mean()
    ema_slow = df["Close"].ewm(span=slow, adjust=False).mean()
    df["MACD"] = ema_fast - ema_slow
    df["MACD_signal"] = df["MACD"].ewm(span=signal, adjust=False).mean()
    return df


def detect_macd_cross(df: pd.DataFrame) -> pd.Series:
    """MACD 골든크로스(+1) / 데드크로스(-1) / 없음(0)을 반환합니다."""
    if "MACD" not in df.columns or "MACD_signal" not in df.columns:
        return pd.Series(0, index=df.index)

    cross = pd.Series(0, index=df.index)
    prev_diff = df["MACD"].shift(1) - df["MACD_signal"].shift(1)
    curr_diff = df["MACD"] - df["MACD_signal"]

    cross[(prev_diff < 0) & (curr_diff >= 0)] = 1
    cross[(prev_diff > 0) & (curr_diff <= 0)] = -1
    return cross

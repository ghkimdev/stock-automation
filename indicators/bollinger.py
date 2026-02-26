from __future__ import annotations

import pandas as pd

from config import BB_PERIOD, BB_STD


def add_bollinger(
    df: pd.DataFrame,
    period: int = BB_PERIOD,
    std: float = BB_STD,
) -> pd.DataFrame:
    """BB_upper, BB_lower, BB_mid 컬럼을 추가합니다."""
    df = df.copy()
    df["BB_mid"] = df["Close"].rolling(window=period).mean()
    rolling_std = df["Close"].rolling(window=period).std()
    df["BB_upper"] = df["BB_mid"] + std * rolling_std
    df["BB_lower"] = df["BB_mid"] - std * rolling_std
    return df


def get_bb_signal(df: pd.DataFrame) -> pd.Series:
    """하단 터치: +1(BUY), 상단 터치: -1(SELL), 그 외: 0(HOLD)."""
    if "BB_upper" not in df.columns or "BB_lower" not in df.columns:
        return pd.Series(0, index=df.index)

    signal = pd.Series(0, index=df.index)
    signal[df["Close"] <= df["BB_lower"]] = 1
    signal[df["Close"] >= df["BB_upper"]] = -1
    return signal

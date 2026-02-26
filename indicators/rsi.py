from __future__ import annotations

import pandas as pd

from config import RSI_OVERBOUGHT, RSI_OVERSOLD, RSI_PERIOD


def add_rsi(df: pd.DataFrame, period: int = RSI_PERIOD) -> pd.DataFrame:
    """RSI 컬럼을 추가합니다."""
    df = df.copy()
    delta = df["Close"].diff()
    gain = delta.clip(lower=0).rolling(window=period).mean()
    loss = (-delta.clip(upper=0)).rolling(window=period).mean()
    rs = gain / loss.replace(0, float("nan"))
    df["RSI"] = 100 - (100 / (1 + rs))
    return df


def get_rsi_signal(df: pd.DataFrame) -> pd.Series:
    """과매수(RSI>70): -1(SELL), 과매도(RSI<30): +1(BUY), 그 외: 0(HOLD)."""
    if "RSI" not in df.columns:
        return pd.Series(0, index=df.index)

    signal = pd.Series(0, index=df.index)
    signal[df["RSI"] > RSI_OVERBOUGHT] = -1
    signal[df["RSI"] < RSI_OVERSOLD] = 1
    return signal

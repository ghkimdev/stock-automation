"""Stochastic Oscillator — 단기 과매수/과매도 감지"""
from __future__ import annotations

import pandas as pd

STOCH_K: int = 14
STOCH_D: int = 3
STOCH_OVERBOUGHT: int = 80
STOCH_OVERSOLD: int = 20


def add_stochastic(
    df: pd.DataFrame,
    k_period: int = STOCH_K,
    d_period: int = STOCH_D,
) -> pd.DataFrame:
    """%K, %D 컬럼을 추가합니다."""
    df = df.copy()
    lowest_low = df["Low"].rolling(window=k_period).min()
    highest_high = df["High"].rolling(window=k_period).max()
    df["Stoch_K"] = (df["Close"] - lowest_low) / (highest_high - lowest_low) * 100
    df["Stoch_D"] = df["Stoch_K"].rolling(window=d_period).mean()
    return df


def get_stoch_signal(df: pd.DataFrame) -> pd.Series:
    """
    과매도 영역(K < 20)에서 %K가 %D 상향 돌파 → +1 (BUY)
    과매수 영역(K > 80)에서 %K가 %D 하향 돌파 → -1 (SELL)
    그 외 → 0 (HOLD)
    """
    if "Stoch_K" not in df.columns or "Stoch_D" not in df.columns:
        return pd.Series(0, index=df.index)

    signal = pd.Series(0, index=df.index)
    prev_k = df["Stoch_K"].shift(1)
    prev_d = df["Stoch_D"].shift(1)

    golden = (prev_k < prev_d) & (df["Stoch_K"] >= df["Stoch_D"]) & (df["Stoch_K"] < STOCH_OVERBOUGHT)
    dead   = (prev_k > prev_d) & (df["Stoch_K"] <= df["Stoch_D"]) & (df["Stoch_K"] > STOCH_OVERSOLD)

    signal[golden & (df["Stoch_K"] < STOCH_OVERBOUGHT)] = 1
    signal[dead   & (df["Stoch_K"] > STOCH_OVERSOLD)]   = -1
    return signal

from __future__ import annotations

import pandas as pd

from config import MA_WINDOWS


def add_ma(df: pd.DataFrame, windows: list[int] = MA_WINDOWS) -> pd.DataFrame:
    """이동평균 컬럼(MA5, MA20, MA60)을 추가합니다."""
    df = df.copy()
    for w in windows:
        df[f"MA{w}"] = df["Close"].rolling(window=w).mean()
    return df


def detect_crossover(df: pd.DataFrame) -> pd.Series:
    """골든크로스(+1) / 데드크로스(-1) / 없음(0) 시리즈를 반환합니다."""
    if "MA5" not in df.columns or "MA20" not in df.columns:
        return pd.Series(0, index=df.index)

    cross = pd.Series(0, index=df.index)
    prev_diff = df["MA5"].shift(1) - df["MA20"].shift(1)
    curr_diff = df["MA5"] - df["MA20"]

    cross[(prev_diff < 0) & (curr_diff >= 0)] = 1   # 골든크로스
    cross[(prev_diff > 0) & (curr_diff <= 0)] = -1  # 데드크로스
    return cross

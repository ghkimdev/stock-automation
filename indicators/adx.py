"""ADX (Average Directional Index) + 거래량 필터"""
from __future__ import annotations

import pandas as pd

ADX_PERIOD: int = 14
ADX_TREND_THRESHOLD: int = 20   # ADX < 20 → 횡보장 (신호 무효)
VOLUME_MA_PERIOD: int = 20


def add_adx(df: pd.DataFrame, period: int = ADX_PERIOD) -> pd.DataFrame:
    """ADX, +DI, -DI 컬럼을 추가합니다."""
    df = df.copy()
    prev_high = df["High"].shift(1)
    prev_low = df["Low"].shift(1)
    prev_close = df["Close"].shift(1)

    plus_dm = df["High"] - prev_high
    minus_dm = prev_low - df["Low"]
    plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0.0)
    minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0.0)

    tr = pd.concat(
        [
            df["High"] - df["Low"],
            (df["High"] - prev_close).abs(),
            (df["Low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)

    atr = tr.ewm(span=period, adjust=False).mean()
    plus_di = 100 * plus_dm.ewm(span=period, adjust=False).mean() / atr
    minus_di = 100 * minus_dm.ewm(span=period, adjust=False).mean() / atr

    dx = (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, float("nan")) * 100
    df["ADX"] = dx.ewm(span=period, adjust=False).mean()
    df["Plus_DI"] = plus_di
    df["Minus_DI"] = minus_di
    return df


def add_volume_ma(df: pd.DataFrame, period: int = VOLUME_MA_PERIOD) -> pd.DataFrame:
    """거래량 이동평균(Volume_MA) 컬럼을 추가합니다."""
    df = df.copy()
    df["Volume_MA"] = df["Volume"].rolling(window=period).mean()
    return df


def is_trending(df: pd.DataFrame, threshold: int = ADX_TREND_THRESHOLD) -> pd.Series:
    """ADX >= threshold 이면 True (추세장), 미만이면 False (횡보장)."""
    if "ADX" not in df.columns:
        return pd.Series(True, index=df.index)
    return df["ADX"] >= threshold


def is_volume_confirmed(df: pd.DataFrame) -> pd.Series:
    """거래량이 Volume_MA 이상이면 True (신호 유효)."""
    if "Volume_MA" not in df.columns:
        return pd.Series(True, index=df.index)
    return df["Volume"] >= df["Volume_MA"]

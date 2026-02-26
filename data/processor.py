from __future__ import annotations

import pandas as pd

from config import MIN_DATA_ROWS
from utils.logger import get_logger

logger = get_logger(__name__)


class InsufficientDataError(Exception):
    """지표 계산에 필요한 최소 데이터 부족"""


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """결측값을 제거하고 데이터 타입을 정규화합니다."""
    df = df.copy()
    before = len(df)
    df.dropna(inplace=True)
    removed = before - len(df)
    if removed:
        logger.debug(f"결측값 {removed}행 제거")
    for col in ["Open", "High", "Low", "Close"]:
        if col in df.columns:
            df[col] = df[col].astype(float)
    if "Volume" in df.columns:
        df["Volume"] = df["Volume"].astype(int)
    return df


def validate(df: pd.DataFrame, min_rows: int = MIN_DATA_ROWS) -> bool:
    """최소 데이터 행 수를 검증합니다."""
    if len(df) < min_rows:
        raise InsufficientDataError(
            f"데이터 {len(df)}행 — 최소 {min_rows}행 필요"
        )
    return True

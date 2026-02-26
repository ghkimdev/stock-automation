from __future__ import annotations

import time

import pandas as pd
import yfinance as yf

from config import DATA_PERIOD, MAX_RETRY
from utils.logger import get_logger

logger = get_logger(__name__)


class DataFetchError(Exception):
    """데이터 수집 실패"""


def fetch_ohlcv(ticker: str, period: str = DATA_PERIOD) -> pd.DataFrame:
    """yfinance로 일봉 데이터를 수집합니다. 실패 시 MAX_RETRY회 재시도합니다."""
    for attempt in range(1, MAX_RETRY + 1):
        try:
            df = yf.download(ticker, period=period, progress=False, auto_adjust=True)
            if df.empty:
                raise DataFetchError(f"{ticker}: 데이터 없음")
            # 멀티인덱스 컬럼 평탄화
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            logger.info(f"{ticker}: {len(df)}행 수집 완료")
            return df
        except DataFetchError:
            raise
        except Exception as exc:
            logger.warning(f"{ticker}: 수집 실패 ({attempt}/{MAX_RETRY}) - {exc}")
            if attempt < MAX_RETRY:
                time.sleep(1)

    raise DataFetchError(f"{ticker}: {MAX_RETRY}회 재시도 후 실패")


def fetch_multiple(tickers: list[str]) -> dict[str, pd.DataFrame]:
    """여러 종목을 일괄 수집합니다. 실패 종목은 건너뜁니다."""
    results: dict[str, pd.DataFrame] = {}
    for ticker in tickers:
        try:
            results[ticker] = fetch_ohlcv(ticker)
        except DataFetchError as exc:
            logger.error(f"{ticker}: 건너뜀 - {exc}")
    return results

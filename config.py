from __future__ import annotations

from pathlib import Path

# 파일 경로
WATCHLIST_FILE: str = "watchlist.txt"
LOG_FILE: str = "signals.log"
LOG_LEVEL: str = "INFO"

# 데이터 수집
DATA_PERIOD: str = "1y"
MAX_RETRY: int = 3

# 지표 파라미터
MA_WINDOWS: list[int] = [5, 20, 60]
RSI_PERIOD: int = 14
RSI_OVERBOUGHT: int = 70
RSI_OVERSOLD: int = 30
MACD_FAST: int = 12
MACD_SLOW: int = 26
MACD_SIGNAL: int = 9
BB_PERIOD: int = 20
BB_STD: float = 2.0

# 백테스팅
DEFAULT_CAPITAL: float = 1_000_000.0
MIN_DATA_ROWS: int = 60


def load_watchlist(path: str = WATCHLIST_FILE) -> list[str]:
    """watchlist.txt에서 종목 코드 목록을 읽어 반환합니다."""
    tickers: list[str] = []
    watchlist_path = Path(path)

    if not watchlist_path.exists():
        return tickers

    for line in watchlist_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            tickers.append(line)

    return tickers

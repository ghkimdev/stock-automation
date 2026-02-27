"""
stock-automation: 주식 기술적 지표 기반 매매 신호 생성기

사용법:
  python main.py                        # watchlist.txt 전체 분석
  python main.py --ticker AAPL          # 단일 종목 분석
  python main.py --backtest AAPL        # 백테스팅 실행
  python main.py --backtest AAPL --start 2024-01-01 --end 2024-12-31
"""

import argparse
import sys

from config import load_watchlist
from data.fetcher import DataFetchError, fetch_ohlcv
from data.processor import InsufficientDataError, clean, validate
from signals.generator import generate, print_signals
from backtest.engine import run as run_backtest
from utils.logger import get_logger

logger = get_logger(__name__)


def analyze_ticker(ticker: str) -> None:
    """단일 종목을 분석하고 매매 신호를 출력합니다."""
    print(f"\n{'='*50}")
    print(f"  종목: {ticker}")
    print(f"{'='*50}")
    try:
        df = fetch_ohlcv(ticker)
        df = clean(df)
        validate(df)
        signals = generate(df, ticker)
        print_signals(signals)
    except (DataFetchError, InsufficientDataError) as exc:
        print(f"  ⚠️  건너뜀: {exc}")
        logger.error(f"{ticker}: {exc}")


def backtest_ticker(ticker: str, start: str, end: str) -> None:
    """단일 종목의 백테스팅을 실행하고 결과를 출력합니다."""
    print(f"\n{'='*50}")
    print(f"  백테스팅: {ticker} ({start} ~ {end})")
    print(f"{'='*50}")
    try:
        result = run_backtest(ticker, start, end)
        print(f"  수익률    : {result.total_return:+.2f}%")
        print(f"  최대 낙폭  : -{result.max_drawdown:.2f}%")
        print(f"  매매 횟수  : {result.trade_count}회")
        print(f"  승률      : {result.win_rate:.1f}%")
        print(f"  손절 청산  : {result.stop_loss_hits}회")
        print(f"  목표가 달성: {result.target_hits}회")
        print(f"\n  [매매 신호 내역]")
        print_signals(result.signals)
    except (DataFetchError, InsufficientDataError) as exc:
        print(f"  ⚠️  건너뜀: {exc}")
        logger.error(f"{ticker}: {exc}")


def main() -> None:
    parser = argparse.ArgumentParser(description="주식 매매 신호 생성기")
    parser.add_argument("--ticker", help="분석할 단일 종목 코드")
    parser.add_argument("--backtest", help="백테스팅할 종목 코드")
    parser.add_argument("--start", default="2024-01-01", help="백테스팅 시작일 (YYYY-MM-DD)")
    parser.add_argument("--end", default="2024-12-31", help="백테스팅 종료일 (YYYY-MM-DD)")
    args = parser.parse_args()

    if args.backtest:
        backtest_ticker(args.backtest, args.start, args.end)
        return

    tickers = [args.ticker] if args.ticker else load_watchlist()
    if not tickers:
        print("⚠️  분석할 종목이 없습니다. watchlist.txt를 확인하세요.")
        sys.exit(1)

    print(f"\n[주식 자동화 분석] 총 {len(tickers)}개 종목")
    for ticker in tickers:
        analyze_ticker(ticker)

    print(f"\n{'='*50}")
    print("  분석 완료. 로그: signals.log")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    main()

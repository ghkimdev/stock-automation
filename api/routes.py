from __future__ import annotations

import math
import os

import pandas as pd
from flask import Blueprint, Response, jsonify, request

from data.fetcher import DataFetchError, fetch_ohlcv
from data.processor import InsufficientDataError, clean, validate
from indicators.bollinger import add_bollinger
from indicators.macd import add_macd
from indicators.moving_average import add_ma
from indicators.rsi import add_rsi
from signals.generator import generate
from utils.logger import get_logger

logger = get_logger(__name__)
api_bp = Blueprint("api", __name__)

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_WATCHLIST_FILE = os.path.join(_BASE_DIR, "watchlist.txt")

_VALID_PERIODS = {"1mo", "3mo", "6mo", "1y"}


# ─── helpers ────────────────────────────────────────────────────────────────

def _safe_float(val: object) -> float | None:
    """numpy / pandas 숫자 → Python float. NaN 은 None 으로 반환합니다."""
    if val is None:
        return None
    try:
        f = float(val)
        return None if math.isnan(f) else round(f, 4)
    except (TypeError, ValueError):
        return None


def _df_to_ohlcv(df: pd.DataFrame) -> list[dict]:
    records = []
    for ts, row in df.iterrows():
        volume = row.get("Volume")
        records.append({
            "date": ts.strftime("%Y-%m-%d"),
            "open": _safe_float(row.get("Open")),
            "high": _safe_float(row.get("High")),
            "low": _safe_float(row.get("Low")),
            "close": _safe_float(row.get("Close")),
            "volume": int(volume) if volume is not None and pd.notna(volume) else None,
        })
    return records


def _df_to_indicators(df: pd.DataFrame) -> dict:
    ma_list, rsi_list, macd_list, bb_list = [], [], [], []

    for ts, row in df.iterrows():
        date_str = ts.strftime("%Y-%m-%d")

        ma_list.append({
            "date": date_str,
            "ma5": _safe_float(row.get("MA5")),
            "ma20": _safe_float(row.get("MA20")),
            "ma60": _safe_float(row.get("MA60")),
        })

        rsi_list.append({
            "date": date_str,
            "value": _safe_float(row.get("RSI")),
        })

        macd_val = _safe_float(row.get("MACD"))
        sig_val = _safe_float(row.get("MACD_signal"))
        hist = round(macd_val - sig_val, 4) if (macd_val is not None and sig_val is not None) else None
        macd_list.append({
            "date": date_str,
            "macd": macd_val,
            "signal": sig_val,
            "histogram": hist,
        })

        bb_list.append({
            "date": date_str,
            "upper": _safe_float(row.get("BB_upper")),
            "mid": _safe_float(row.get("BB_mid")),
            "lower": _safe_float(row.get("BB_lower")),
        })

    return {"ma": ma_list, "rsi": rsi_list, "macd": macd_list, "bollinger": bb_list}


def _signals_to_list(signals: list) -> list[dict]:
    result = []
    for s in signals:
        date_str = s.date.strftime("%Y-%m-%d") if hasattr(s.date, "strftime") else str(s.date)
        result.append({
            "date": date_str,
            "type": s.signal.value,
            "reason": s.reason,
            "price": round(float(s.price), 4),
            "stop_loss": round(float(s.stop_loss), 4) if s.stop_loss is not None else None,
            "target": round(float(s.target), 4) if s.target is not None else None,
        })
    return result


def _read_watchlist() -> list[str]:
    tickers: list[str] = []
    if not os.path.exists(_WATCHLIST_FILE):
        return tickers
    with open(_WATCHLIST_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                tickers.append(line)
    return tickers


def _write_watchlist(tickers: list[str]) -> None:
    with open(_WATCHLIST_FILE, "w", encoding="utf-8") as f:
        f.write("# 관심 종목 목록 (한 줄에 하나씩)\n")
        for t in tickers:
            f.write(f"{t}\n")


# ─── routes ─────────────────────────────────────────────────────────────────

@api_bp.route("/analyze")
def analyze() -> Response:
    """GET /api/analyze?ticker=AAPL&period=1y"""
    ticker = request.args.get("ticker", "").strip().upper()
    period = request.args.get("period", "1y")

    if not ticker:
        return jsonify({"error": "ticker is required"}), 400

    if period not in _VALID_PERIODS:
        period = "1y"

    try:
        df = fetch_ohlcv(ticker, period)
        df = clean(df)
        validate(df)

        chart_df = add_ma(df)
        chart_df = add_rsi(chart_df)
        chart_df = add_macd(chart_df)
        chart_df = add_bollinger(chart_df)

        signals = generate(df, ticker)

        result = {
            "ticker": ticker,
            "period": period,
            "last_updated": df.index[-1].strftime("%Y-%m-%d"),
            "ohlcv": _df_to_ohlcv(chart_df),
            "indicators": _df_to_indicators(chart_df),
            "signals": _signals_to_list(signals),
        }
        return jsonify(result)

    except DataFetchError as exc:
        return jsonify({"error": str(exc)}), 404
    except InsufficientDataError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        logger.error(f"Unexpected error for {ticker}: {exc}")
        return jsonify({"error": "Internal server error"}), 500


@api_bp.route("/watchlist", methods=["GET"])
def get_watchlist() -> Response:
    """GET /api/watchlist"""
    return jsonify({"tickers": _read_watchlist()})


@api_bp.route("/watchlist", methods=["POST"])
def add_watchlist() -> Response:
    """POST /api/watchlist  body: {"ticker": "AAPL"}"""
    body = request.get_json(silent=True) or {}
    ticker = body.get("ticker", "").strip().upper()

    if not ticker:
        return jsonify({"error": "ticker is required"}), 400

    tickers = _read_watchlist()
    if ticker in tickers:
        return jsonify({"error": f"{ticker} already in watchlist"}), 400

    tickers.append(ticker)
    _write_watchlist(tickers)
    return jsonify({"message": f"Added {ticker}", "tickers": tickers}), 201


@api_bp.route("/watchlist/<ticker>", methods=["DELETE"])
def remove_watchlist(ticker: str) -> Response:
    """DELETE /api/watchlist/<ticker>"""
    ticker = ticker.upper()
    tickers = _read_watchlist()

    if ticker not in tickers:
        return jsonify({"error": f"{ticker} not in watchlist"}), 404

    tickers.remove(ticker)
    _write_watchlist(tickers)
    return jsonify({"message": f"Removed {ticker}", "tickers": tickers})

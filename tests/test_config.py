"""config.py 단위 테스트"""
from __future__ import annotations

import tempfile
from pathlib import Path

from config import load_watchlist


class TestLoadWatchlist:
    def test_returns_empty_list_for_missing_file(self):
        result = load_watchlist("/nonexistent/path.txt")
        assert result == []

    def test_parses_tickers(self, tmp_path):
        wl = tmp_path / "watchlist.txt"
        wl.write_text("AAPL\nMSFT\n005930.KS\n", encoding="utf-8")
        result = load_watchlist(str(wl))
        assert result == ["AAPL", "MSFT", "005930.KS"]

    def test_ignores_comments(self, tmp_path):
        wl = tmp_path / "watchlist.txt"
        wl.write_text("# 코멘트\nAAPL\n# 또 다른 코멘트\nNVDA\n", encoding="utf-8")
        result = load_watchlist(str(wl))
        assert result == ["AAPL", "NVDA"]

    def test_ignores_empty_lines(self, tmp_path):
        wl = tmp_path / "watchlist.txt"
        wl.write_text("AAPL\n\n\nMSFT\n", encoding="utf-8")
        result = load_watchlist(str(wl))
        assert result == ["AAPL", "MSFT"]

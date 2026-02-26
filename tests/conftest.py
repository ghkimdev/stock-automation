"""공통 테스트 픽스처"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest


def make_ohlcv(n: int = 120, seed: int = 42, base: float = 50_000.0) -> pd.DataFrame:
    """n행짜리 합성 OHLCV DataFrame을 생성합니다."""
    np.random.seed(seed)
    dates = pd.date_range(start="2024-01-01", periods=n, freq="B")
    close = base + np.cumsum(np.random.randn(n) * 500)
    return pd.DataFrame(
        {
            "Open": close * 0.99,
            "High": close * 1.02,
            "Low": close * 0.97,
            "Close": close,
            "Volume": np.random.randint(1_000_000, 5_000_000, n),
        },
        index=dates,
    )


@pytest.fixture
def sample_df() -> pd.DataFrame:
    """기본 120행 OHLCV 픽스처."""
    return make_ohlcv()


@pytest.fixture
def small_df() -> pd.DataFrame:
    """MIN_DATA_ROWS(60)보다 작은 30행 픽스처."""
    return make_ohlcv(n=30)


@pytest.fixture
def golden_cross_df() -> pd.DataFrame:
    """MA5가 MA20을 상향 돌파하는 골든크로스 시나리오 픽스처."""
    n = 80
    dates = pd.date_range(start="2024-01-01", periods=n, freq="B")
    # 초반 하락 후 상승 → MA5가 MA20을 크로스
    close = np.concatenate([
        np.linspace(60_000, 48_000, 40),
        np.linspace(48_000, 62_000, 40),
    ])
    return pd.DataFrame(
        {
            "Open": close * 0.99,
            "High": close * 1.01,
            "Low": close * 0.98,
            "Close": close,
            "Volume": np.ones(n, dtype=int) * 1_000_000,
        },
        index=dates,
    )

# stock-automation Design Document

> **Summary**: 주식 기술적 지표 계산 및 매매 신호 생성 자동화 시스템 설계
>
> **Project**: stock-automation
> **Version**: 0.1.0
> **Author**: gwangho
> **Date**: 2026-02-27
> **Status**: Draft
> **Planning Doc**: [stock-automation.plan.md](../01-plan/features/stock-automation.plan.md)

---

## 1. Overview

### 1.1 Design Goals

- 각 모듈이 단일 책임을 갖는 명확한 계층 구조
- 지표 추가 시 기존 코드 수정 없이 확장 가능한 구조
- 데이터 수집 → 지표 계산 → 신호 생성 → 출력의 명확한 파이프라인

### 1.2 Design Principles

- **단일 책임**: 각 모듈은 하나의 역할만 담당
- **의존성 방향**: `main → signals → indicators → data`
- **타입 안전성**: 모든 함수에 타입 힌트 필수
- **실패 허용**: API 오류 시 재시도 후 스킵 (전체 중단 금지)

---

## 2. Architecture

### 2.1 컴포넌트 다이어그램

```
┌─────────────────────────────────────────────────────────┐
│                        main.py                          │
│                  (CLI 진입점, 오케스트레이터)              │
└──────────┬──────────────────────────┬───────────────────┘
           │                          │
           ▼                          ▼
┌─────────────────┐        ┌─────────────────────┐
│   config.py     │        │  backtest/engine.py  │
│ (설정, 종목목록) │        │   (백테스팅 엔진)    │
└─────────────────┘        └──────────┬──────────┘
                                      │
           ┌──────────────────────────┘
           ▼
┌─────────────────────┐
│  signals/           │
│  generator.py       │  ← 매매 신호 생성
└──────────┬──────────┘
           │ (지표 계산 요청)
           ▼
┌──────────────────────────────────────────────┐
│               indicators/                    │
│  moving_average.py  rsi.py  macd.py          │
│  bollinger.py                                │
└──────────────────────────┬───────────────────┘
                           │ (데이터 요청)
                           ▼
┌─────────────────────────────────────────────┐
│               data/                         │
│  fetcher.py (yfinance)  processor.py        │
└─────────────────────────────────────────────┘
           │
           ▼
┌─────────────────┐
│   utils/        │
│   logger.py     │  ← 전 계층에서 사용
└─────────────────┘
```

### 2.2 데이터 흐름

```
watchlist.txt
     │
     ▼
[fetcher] → yfinance API → DataFrame (OHLCV)
     │
     ▼
[processor] → 결측값 처리, 데이터 정규화
     │
     ▼
[indicators] → 지표 컬럼 추가 (MA5, MA20, RSI, MACD, BB)
     │
     ▼
[generator] → 신호 생성 (BUY / SELL / HOLD)
     │
     ▼
[main] → 콘솔 출력 + 로그 파일 저장
```

### 2.3 의존성

| 모듈 | 의존 대상 | 목적 |
|------|---------|------|
| main.py | config, signals, backtest, utils | 전체 흐름 제어 |
| signals/generator.py | indicators/*, data/* | 신호 계산 |
| indicators/*.py | data/processor | DataFrame 수신 |
| data/fetcher.py | yfinance | 주가 데이터 수집 |
| data/processor.py | pandas | 데이터 전처리 |
| backtest/engine.py | signals, data | 과거 신호 재계산 |

---

## 3. Data Model

### 3.1 핵심 데이터 구조 (Python dataclass)

```python
from dataclasses import dataclass
from datetime import date
from enum import Enum

class SignalType(Enum):
    BUY  = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

@dataclass
class StockData:
    ticker: str
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: int

@dataclass
class Signal:
    ticker: str
    date: date
    signal: SignalType
    reason: str          # 신호 발생 이유 (e.g., "골든크로스 MA5>MA20")
    price: float         # 신호 발생 시점 종가

@dataclass
class BacktestResult:
    ticker: str
    start_date: date
    end_date: date
    total_return: float  # 수익률 (%)
    trade_count: int
    win_rate: float      # 승률 (%)
    signals: list[Signal]
```

### 3.2 DataFrame 컬럼 정의

| 컬럼명 | 타입 | 설명 |
|--------|------|------|
| `Open` | float | 시가 |
| `High` | float | 고가 |
| `Low` | float | 저가 |
| `Close` | float | 종가 |
| `Volume` | int | 거래량 |
| `MA5` | float | 5일 이동평균 |
| `MA20` | float | 20일 이동평균 |
| `MA60` | float | 60일 이동평균 |
| `RSI` | float | RSI (14일) |
| `MACD` | float | MACD 값 |
| `MACD_signal` | float | MACD 시그널선 |
| `BB_upper` | float | 볼린저밴드 상단 |
| `BB_lower` | float | 볼린저밴드 하단 |

---

## 4. 모듈별 함수 명세

### 4.1 data/fetcher.py

```python
def fetch_ohlcv(ticker: str, period: str = "1y") -> pd.DataFrame:
    """yfinance로 일봉 데이터 수집. 실패 시 3회 재시도."""

def fetch_multiple(tickers: list[str]) -> dict[str, pd.DataFrame]:
    """여러 종목 일괄 수집. 실패 종목은 건너뜀."""
```

### 4.2 data/processor.py

```python
def clean(df: pd.DataFrame) -> pd.DataFrame:
    """결측값 제거, 데이터 타입 정규화."""

def validate(df: pd.DataFrame, min_rows: int = 60) -> bool:
    """최소 데이터 행 수 검증 (지표 계산에 필요한 최소치)."""
```

### 4.3 indicators/moving_average.py

```python
def add_ma(df: pd.DataFrame, windows: list[int] = [5, 20, 60]) -> pd.DataFrame:
    """이동평균 컬럼 추가 (MA5, MA20, MA60)."""

def detect_crossover(df: pd.DataFrame) -> pd.Series:
    """골든크로스(+1) / 데드크로스(-1) / 없음(0) 시리즈 반환."""
```

### 4.4 indicators/rsi.py

```python
def add_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """RSI 컬럼 추가."""

def get_rsi_signal(df: pd.DataFrame) -> pd.Series:
    """과매수(RSI>70): SELL, 과매도(RSI<30): BUY, 그 외: HOLD."""
```

### 4.5 indicators/macd.py

```python
def add_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    """MACD, MACD_signal 컬럼 추가."""

def detect_macd_cross(df: pd.DataFrame) -> pd.Series:
    """MACD 골든크로스(+1) / 데드크로스(-1) / 없음(0)."""
```

### 4.6 indicators/bollinger.py

```python
def add_bollinger(df: pd.DataFrame, period: int = 20, std: float = 2.0) -> pd.DataFrame:
    """BB_upper, BB_lower, BB_mid 컬럼 추가."""

def get_bb_signal(df: pd.DataFrame) -> pd.Series:
    """하단 터치: BUY, 상단 터치: SELL, 그 외: HOLD."""
```

### 4.7 signals/generator.py

```python
def generate(df: pd.DataFrame, ticker: str) -> list[Signal]:
    """
    모든 지표 신호를 종합하여 최종 Signal 리스트 반환.
    다수결 방식: 2개 이상 BUY → BUY, 2개 이상 SELL → SELL.
    """

def print_signals(signals: list[Signal]) -> None:
    """신호를 콘솔에 포맷팅하여 출력."""
```

### 4.8 backtest/engine.py

```python
def run(ticker: str, start: str, end: str, initial_capital: float = 1_000_000) -> BacktestResult:
    """
    지정 기간 동안 신호 기반 매매 시뮬레이션.
    수익률, 승률, 매매 횟수 반환.
    """
```

---

## 5. 에러 처리

### 5.1 에러 유형 및 처리 방식

| 에러 유형 | 처리 방식 |
|---------|---------|
| yfinance API 오류 | 3회 재시도 후 해당 종목 스킵, 경고 로그 |
| 데이터 부족 (< 60행) | 해당 종목 스킵, 경고 로그 |
| 잘못된 종목 코드 | 즉시 스킵, 에러 로그 |
| 계산 오류 (NaN 과다) | 해당 지표 건너뜀, 경고 로그 |

### 5.2 커스텀 예외

```python
class DataFetchError(Exception):
    """데이터 수집 실패"""

class InsufficientDataError(Exception):
    """지표 계산에 필요한 최소 데이터 부족"""
```

---

## 6. 설정 (config.py)

```python
# config.py
WATCHLIST_FILE = "watchlist.txt"
DATA_PERIOD    = "1y"          # yfinance 기간
LOG_FILE       = "signals.log"
LOG_LEVEL      = "INFO"

# 지표 파라미터
MA_WINDOWS     = [5, 20, 60]
RSI_PERIOD     = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD   = 30
MACD_FAST      = 12
MACD_SLOW      = 26
MACD_SIGNAL    = 9
BB_PERIOD      = 20
BB_STD         = 2.0

# 백테스팅
DEFAULT_CAPITAL = 1_000_000    # 초기 자본 (원)
```

---

## 7. 보안 고려사항

- [ ] API 키 하드코딩 금지 (yfinance는 무료/키 불필요)
- [ ] watchlist.txt 에 개인정보 포함 금지
- [ ] 로그 파일에 민감 정보 미포함

---

## 8. 테스트 계획

### 8.1 테스트 범위

| 유형 | 대상 | 도구 |
|------|------|------|
| 단위 테스트 | 각 지표 계산 함수 | pytest |
| 통합 테스트 | 데이터 수집 → 신호 생성 전체 흐름 | pytest |
| 수동 테스트 | 실제 종목으로 신호 출력 확인 | CLI 실행 |

### 8.2 주요 테스트 케이스

- [ ] 정상 종목 코드 → 신호 출력 확인
- [ ] 잘못된 종목 코드 → 에러 없이 스킵 확인
- [ ] 데이터 60행 미만 → InsufficientDataError 확인
- [ ] 골든크로스 조건 데이터 → BUY 신호 생성 확인
- [ ] RSI > 70 → SELL 신호 생성 확인

---

## 9. 구현 순서 (Do Phase 체크리스트)

1. [ ] `requirements.txt` 작성 및 패키지 설치
2. [ ] `utils/logger.py` 구현
3. [ ] `config.py` 구현
4. [ ] `data/fetcher.py` 구현 및 테스트
5. [ ] `data/processor.py` 구현
6. [ ] `indicators/moving_average.py` 구현
7. [ ] `indicators/rsi.py` 구현
8. [ ] `indicators/macd.py` 구현
9. [ ] `indicators/bollinger.py` 구현
10. [ ] `signals/generator.py` 구현
11. [ ] `backtest/engine.py` 구현
12. [ ] `main.py` CLI 구현
13. [ ] `watchlist.txt` 샘플 작성
14. [ ] 통합 테스트 실행

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-02-27 | Initial draft | gwangho |

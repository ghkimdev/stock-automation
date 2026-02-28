# stock-automation-webpage Design Document

> **Summary**: Flask REST API + 순수 HTML/JS 대시보드로 주식 분석 결과를 브라우저에서 시각화
>
> **Project**: stock-automation
> **Feature**: stock-automation-webpage
> **Version**: 0.1.0
> **Author**: gwangho
> **Date**: 2026-02-28
> **Status**: Draft
> **Planning Doc**: [stock-automation-webpage.plan.md](../01-plan/features/stock-automation-webpage.plan.md)
> **Backend Design**: [stock-automation.design.md](stock-automation.design.md)

---

## 1. Overview

### 1.1 Design Goals

- 기존 `indicators/`, `signals/`, `data/` 모듈을 그대로 재사용 (코드 중복 없음)
- Flask API가 기존 Python 분석 로직과 HTML 프론트엔드를 연결
- Chart.js CDN만으로 의존성 최소화 (npm/빌드 과정 불필요)
- `python app.py` 단일 명령으로 서버 실행

### 1.2 Design Principles

- **재사용 우선**: 기존 indicators/signals 모듈 import, 재구현 금지
- **단순성**: SPA 프레임워크 없이 순수 HTML/JS + fetch API
- **반응형**: 로딩 상태, 에러 메시지 명시적 표시
- **분리**: API 로직(api/routes.py)과 뷰(templates/)를 명확히 분리

---

## 2. Architecture

### 2.1 시스템 구성도

```
Browser (http://localhost:5000)
        │
        │  GET /               → HTML 페이지 반환
        │  GET /api/analyze    → JSON 분석 결과
        │  GET /api/watchlist  → JSON 관심 종목
        │  POST /api/watchlist → 종목 추가
        │  DELETE /api/watchlist/<ticker> → 종목 삭제
        ▼
┌──────────────────────────────────────────┐
│            Flask App (app.py)            │
│                                          │
│  ┌──────────────────────────────────┐    │
│  │         api/routes.py            │    │
│  │  Blueprint: /api                 │    │
│  └─────────────┬────────────────────┘    │
│                │  import                 │
│                ▼                         │
│  ┌──────────────────────────────────┐    │
│  │    기존 stock-automation 모듈    │    │
│  │  data/fetcher.py                 │    │
│  │  data/processor.py               │    │
│  │  indicators/*.py                 │    │
│  │  signals/generator.py            │    │
│  │  config.py                       │    │
│  └──────────────────────────────────┘    │
└──────────────────────────────────────────┘
        │
        │  정적 파일 제공
        ▼
┌──────────────────────────────────────────┐
│  static/js/dashboard.js                  │
│  static/css/style.css                    │
│  templates/index.html                    │
└──────────────────────────────────────────┘
```

### 2.2 폴더 구조 (신규 파일만)

```
stock-automation/
├── app.py                    # NEW: Flask 앱 진입점
├── api/                      # NEW
│   ├── __init__.py
│   └── routes.py             # REST API 라우트 (Blueprint)
├── static/                   # NEW
│   ├── css/
│   │   └── style.css         # 대시보드 스타일
│   └── js/
│       └── dashboard.js      # Chart.js 렌더링 + fetch 로직
└── templates/                # NEW
    └── index.html            # 단일 대시보드 페이지
```

### 2.3 데이터 흐름

```
[Browser] → GET /api/analyze?ticker=AAPL&period=1y
                │
                ▼
[routes.py] → fetch_ohlcv(ticker, period)
                │
                ▼
[data/processor.py] → clean(df)
                │
                ▼
[indicators/*.py] → add_ma(), add_rsi(), add_macd(), add_bollinger()
                │
                ▼
[signals/generator.py] → generate(df, ticker) → [Signal, ...]
                │
                ▼
[routes.py] → DataFrame + Signals → JSON 직렬화
                │
                ▼
[Browser] → dashboard.js → Chart.js 렌더링
```

---

## 3. API Endpoint 명세

### 3.1 GET /api/analyze

종목 분석 결과를 JSON으로 반환합니다.

**Query Parameters**:

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `ticker` | string | 필수 | 종목 코드 (예: AAPL, 005930.KS) |
| `period` | string | `1y` | 기간 (1mo, 3mo, 6mo, 1y) |

**Response** (200 OK):

```json
{
  "ticker": "AAPL",
  "period": "1y",
  "last_updated": "2026-02-28",
  "ohlcv": [
    {
      "date": "2025-03-01",
      "open": 170.5,
      "high": 173.2,
      "low": 169.8,
      "close": 172.0,
      "volume": 58000000
    }
  ],
  "indicators": {
    "ma": [
      { "date": "2025-03-01", "ma5": 171.2, "ma20": 168.5, "ma60": 162.3 }
    ],
    "rsi": [
      { "date": "2025-03-01", "value": 58.4 }
    ],
    "macd": [
      { "date": "2025-03-01", "macd": 2.1, "signal": 1.8, "histogram": 0.3 }
    ],
    "bollinger": [
      { "date": "2025-03-01", "upper": 178.0, "mid": 168.5, "lower": 159.0 }
    ]
  },
  "signals": [
    {
      "date": "2026-02-15",
      "type": "BUY",
      "reason": "골든크로스 MA5>MA20",
      "price": 171.5
    }
  ]
}
```

**Error Responses**:

| 상태코드 | 조건 | 응답 body |
|---------|------|---------|
| 400 | ticker 파라미터 없음 | `{"error": "ticker is required"}` |
| 404 | 데이터 없음 / 잘못된 종목코드 | `{"error": "No data for ticker: XYZ"}` |
| 500 | 서버 내부 오류 | `{"error": "Internal server error"}` |

---

### 3.2 GET /api/watchlist

관심 종목 목록을 반환합니다.

**Response** (200 OK):

```json
{
  "tickers": ["AAPL", "MSFT", "005930.KS"]
}
```

---

### 3.3 POST /api/watchlist

관심 종목을 추가합니다.

**Request body** (JSON):

```json
{ "ticker": "TSLA" }
```

**Response** (201 Created):

```json
{ "message": "Added TSLA", "tickers": ["AAPL", "MSFT", "005930.KS", "TSLA"] }
```

**Error**:

| 상태코드 | 조건 |
|---------|------|
| 400 | ticker 누락 또는 이미 존재 |

---

### 3.4 DELETE /api/watchlist/\<ticker\>

관심 종목을 삭제합니다.

**Response** (200 OK):

```json
{ "message": "Removed TSLA", "tickers": ["AAPL", "MSFT", "005930.KS"] }
```

**Error**:

| 상태코드 | 조건 |
|---------|------|
| 404 | ticker가 목록에 없음 |

---

## 4. 모듈별 설계

### 4.1 app.py

```python
from __future__ import annotations
import sys
import os

# 기존 모듈 import 경로 추가 (stock-automation 루트)
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask
from flask_cors import CORS
from api.routes import api_bp

def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app)
    app.register_blueprint(api_bp, url_prefix="/api")
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)
```

---

### 4.2 api/routes.py

```python
from __future__ import annotations
from flask import Blueprint, jsonify, request, Response
import pandas as pd

from data.fetcher import fetch_ohlcv, DataFetchError
from data.processor import clean, validate
from indicators.moving_average import add_ma
from indicators.rsi import add_rsi
from indicators.macd import add_macd
from indicators.bollinger import add_bollinger
from signals.generator import generate
from config import load_watchlist, WATCHLIST_FILE

api_bp = Blueprint("api", __name__)

# --- Helper ---
def _df_to_ohlcv_list(df: pd.DataFrame) -> list[dict]:
    """DataFrame → OHLCV JSON 변환"""

def _df_to_indicator_dict(df: pd.DataFrame) -> dict:
    """DataFrame → indicators JSON 변환"""

def _signals_to_list(signals) -> list[dict]:
    """Signal 객체 리스트 → JSON 직렬화"""

# --- Routes ---
@api_bp.route("/analyze")
def analyze() -> Response:
    """GET /api/analyze?ticker=AAPL&period=1y"""

@api_bp.route("/watchlist", methods=["GET"])
def get_watchlist() -> Response:
    """GET /api/watchlist"""

@api_bp.route("/watchlist", methods=["POST"])
def add_watchlist() -> Response:
    """POST /api/watchlist"""

@api_bp.route("/watchlist/<ticker>", methods=["DELETE"])
def remove_watchlist(ticker: str) -> Response:
    """DELETE /api/watchlist/<ticker>"""
```

---

### 4.3 templates/index.html 화면 구성

```
┌─────────────────────────────────────────────────────────────┐
│  Stock Dashboard                              [Dark/Light]   │
├────────────────────┬────────────────────────────────────────┤
│  Watchlist         │  Search: [AAPL    ] [Period: 1y ▼] [Go]│
│  ─────────         ├────────────────────────────────────────┤
│  AAPL         →   │  AAPL  |  $172.00  |  ▲ BUY signal     │
│  MSFT         →   ├────────────────────────────────────────┤
│  005930.KS    →   │  [Price + MA Chart         ] ← 메인차트 │
│                   │  Close ─── MA5 ─── MA20 ─── MA60        │
│  [+ Add]          │  볼린저밴드 상/하단 점선 오버레이        │
│  [Delete]         │  매수▲ / 매도▽ 마커 표시               │
│                   ├────────────────────────────────────────┤
│                   │  [RSI Chart                ]            │
│                   │  과매수(70) ─── 과매도(30) 기준선        │
│                   ├────────────────────────────────────────┤
│                   │  [MACD Chart               ]            │
│                   │  MACD Bar + Signal Line                  │
└────────────────────┴────────────────────────────────────────┘
```

---

### 4.4 static/js/dashboard.js 구조

```javascript
// 1. 상태 관리
const state = {
  ticker: '',
  period: '1y',
  data: null,
  charts: {}   // Chart.js 인스턴스 캐시
};

// 2. API 호출
async function analyzeStock(ticker, period) { ... }
async function fetchWatchlist() { ... }
async function addToWatchlist(ticker) { ... }
async function removeFromWatchlist(ticker) { ... }

// 3. 차트 렌더링 (Chart.js)
function renderPriceChart(data) { ... }    // Close + MA + BB
function renderRsiChart(data) { ... }      // RSI + 기준선
function renderMacdChart(data) { ... }     // MACD Bar + Signal

// 4. 신호 마커 (Chart.js annotation plugin)
function addSignalAnnotations(chart, signals) { ... }

// 5. Watchlist UI
function renderWatchlist(tickers) { ... }

// 6. 이벤트 핸들러
document.getElementById('search-btn').addEventListener('click', ...);
```

---

## 5. Chart.js 설계

### 5.1 사용 라이브러리 (CDN)

```html
<!-- Chart.js -->
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<!-- 어노테이션 (신호 마커용) -->
<script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-annotation@3"></script>
```

### 5.2 차트 레이아웃

| 차트 | 타입 | 데이터 | 높이 비율 |
|------|------|--------|---------|
| 메인 (Price) | Line | Close + MA5/20/60 + BB upper/lower | 50% |
| RSI | Line | RSI + 70/30 기준선 | 25% |
| MACD | Bar + Line | Histogram + Signal | 25% |

### 5.3 색상 팔레트

| 항목 | 색상 |
|------|------|
| Close | `#2196F3` (파랑) |
| MA5 | `#FF9800` (주황) |
| MA20 | `#9C27B0` (보라) |
| MA60 | `#F44336` (빨강) |
| BB Upper/Lower | `#78909C` (회색, 점선) |
| RSI | `#00BCD4` (청록) |
| MACD Bar (양수) | `#4CAF50` (초록) |
| MACD Bar (음수) | `#F44336` (빨강) |
| 매수 마커 | `#4CAF50` (초록 삼각 ▲) |
| 매도 마커 | `#F44336` (빨강 삼각 ▽) |

---

## 6. 에러 처리

### 6.1 API 레이어

| 상황 | 처리 |
|------|------|
| `DataFetchError` | 404 응답 + `{"error": "..."}` |
| `InsufficientDataError` | 400 응답 |
| 예상치 못한 예외 | 500 응답 + 서버 로그 |

### 6.2 프론트엔드

| 상황 | UI 처리 |
|------|---------|
| 로딩 중 | 스피너 표시, 버튼 비활성화 |
| 404 (종목 없음) | `"종목을 찾을 수 없습니다: {ticker}"` 알림 |
| 네트워크 오류 | `"서버에 연결할 수 없습니다"` 알림 |
| 빈 데이터 | `"분석 데이터가 없습니다"` 메시지 |

---

## 7. 보안 고려사항

- [ ] Flask `debug=False` in production (개발용 `app.run(debug=True)`)
- [ ] ticker 파라미터 길이 제한 (최대 20자) — SQL Injection 해당 없으나 방어적 처리
- [ ] watchlist.txt 경로 traversal 방지 (고정 경로 사용)
- [ ] CORS: 개발 시 전체 허용, 프로덕션 시 도메인 제한

---

## 8. 의존성 추가

기존 `requirements.txt`에 추가:

```
flask>=2.0,<3.0
flask-cors>=3.0
```

---

## 9. 구현 순서 (Do Phase 체크리스트)

1. [ ] `requirements.txt`에 flask, flask-cors 추가 및 설치
2. [ ] `api/__init__.py` 생성
3. [ ] `api/routes.py` — `/analyze` 엔드포인트 구현 (핵심)
4. [ ] `api/routes.py` — `/watchlist` CRUD 엔드포인트 구현
5. [ ] `app.py` — Flask 앱 팩토리 + Blueprint 등록
6. [ ] `templates/index.html` — 기본 레이아웃 (검색창 + 차트 영역)
7. [ ] `static/css/style.css` — 레이아웃 스타일
8. [ ] `static/js/dashboard.js` — API fetch 함수 구현
9. [ ] `static/js/dashboard.js` — 메인 Price 차트 구현
10. [ ] `static/js/dashboard.js` — RSI 차트 구현
11. [ ] `static/js/dashboard.js` — MACD 차트 구현
12. [ ] `static/js/dashboard.js` — 신호 마커 구현
13. [ ] `static/js/dashboard.js` — Watchlist UI 구현
14. [ ] 통합 테스트: `python app.py` → 브라우저 확인

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-02-28 | Initial draft | gwangho |

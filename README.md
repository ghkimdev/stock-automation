# stock-automation

[![Tests](https://github.com/ghkimdev/stock-automation/actions/workflows/test.yml/badge.svg)](https://github.com/ghkimdev/stock-automation/actions/workflows/test.yml)

주식 기술적 지표 기반 매매 신호 생성 및 백테스팅 시스템

## 기능

- **기술적 지표 계산**: 이동평균(MA5/20/60), RSI, MACD, 볼린저밴드
- **매매 신호 생성**: 다수결 방식 BUY/SELL 신호 (2개 이상 지표 일치 시 발생)
- **백테스팅**: 지정 기간 신호 기반 매매 시뮬레이션 (수익률/승률 계산)
- **관심 종목 관리**: `watchlist.txt`로 다중 종목 일괄 분석

## 설치

```bash
pip install -r requirements.txt
```

## 사용법

```bash
# watchlist.txt 전체 종목 분석
python main.py

# 단일 종목 분석
python main.py --ticker AAPL
python main.py --ticker 005930.KS   # 삼성전자

# 백테스팅
python main.py --backtest AAPL
python main.py --backtest AAPL --start 2024-01-01 --end 2024-12-31
```

## 출력 예시

```
==================================================
  종목: AAPL
==================================================
  📈 [2024-03-15] BUY  | 가격:     172,000 | RSI 과매도(28.3), BB 하단 터치
  📉 [2024-07-22] SELL | 가격:     195,000 | MA 데드크로스, RSI 과매수(74.1)
```

## 관심 종목 설정

`watchlist.txt`에 한 줄씩 종목 코드를 입력합니다.

```
# 한국 주식 (KOSPI: .KS / KOSDAQ: .KQ)
005930.KS   # 삼성전자
000660.KS   # SK하이닉스

# 미국 주식
AAPL
NVDA
```

## 신호 생성 기준

4개 지표의 다수결로 최종 신호를 결정합니다.

| 지표 | BUY 조건 | SELL 조건 |
|------|---------|---------|
| 이동평균 | MA5 > MA20 골든크로스 | MA5 < MA20 데드크로스 |
| RSI | RSI < 30 (과매도) | RSI > 70 (과매수) |
| MACD | MACD > 시그널선 크로스 | MACD < 시그널선 크로스 |
| 볼린저밴드 | 종가 ≤ 하단밴드 | 종가 ≥ 상단밴드 |

**2개 이상 BUY → BUY 신호 / 2개 이상 SELL → SELL 신호**

## 프로젝트 구조

```
stock-automation/
├── main.py              # CLI 진입점
├── config.py            # 설정 및 파라미터
├── watchlist.txt        # 관심 종목 목록
├── data/
│   ├── fetcher.py       # yfinance 데이터 수집
│   └── processor.py     # 전처리 및 검증
├── indicators/
│   ├── moving_average.py
│   ├── rsi.py
│   ├── macd.py
│   └── bollinger.py
├── signals/
│   └── generator.py     # 신호 생성 (다수결)
├── backtest/
│   └── engine.py        # 백테스팅 엔진
├── utils/
│   └── logger.py
├── tests/               # pytest 단위 테스트 (46개)
└── docs/                # PDCA 설계 문서
```

## 테스트

```bash
python -m pytest tests/ -v
```

## 주의사항

> 이 프로그램은 **매매 참고용**입니다. 실제 투자 결정에 따른 손익은 사용자 본인에게 있습니다.

- 실제 자동 주문 기능 없음 (알림만 제공)
- 과거 수익률이 미래를 보장하지 않음
- API 한도 초과 시 데이터 수집 실패 가능

## 환경

- Python 3.8+
- yfinance 0.2.38
- pandas 1.3+

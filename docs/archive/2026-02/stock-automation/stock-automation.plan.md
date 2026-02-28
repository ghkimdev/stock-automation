# stock-automation Planning Document

> **Summary**: 주식 데이터를 자동으로 수집·분석하고 매매 신호를 생성하는 자동화 시스템
>
> **Project**: stock-automation
> **Version**: 0.1.0
> **Author**: gwangho
> **Date**: 2026-02-27
> **Status**: Draft

---

## 1. Overview

### 1.1 Purpose

주식 시장 데이터를 자동으로 수집하고, 기술적 지표를 분석하여 매매 신호를 생성합니다.
수동으로 차트를 확인하는 시간을 줄이고, 감정에 의한 매매 결정을 최소화합니다.

### 1.2 Background

- 주식 투자 시 매일 수십 종목의 차트를 수동으로 확인하는 반복 작업 존재
- 감정적 판단으로 인한 매매 실수 방지 필요
- 백테스팅을 통한 전략 검증 후 자동화 적용 목표

### 1.3 Related Documents

- References: KRX (한국거래소), Yahoo Finance API

---

## 2. Scope

### 2.1 In Scope

- [ ] 주식 데이터 자동 수집 (일봉 OHLCV)
- [ ] 기술적 지표 계산 (이동평균, RSI, MACD, 볼린저밴드)
- [ ] 매매 신호 생성 및 알림 (이메일 또는 콘솔 출력)
- [ ] 백테스팅 기능 (과거 데이터로 전략 검증)
- [ ] 종목 관심 목록 관리

### 2.2 Out of Scope

- 실제 자동 매매 주문 (증권사 API 연동)
- 실시간 틱 데이터 처리
- 웹 UI / 대시보드

---

## 3. Requirements

### 3.1 Functional Requirements

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-01 | 종목 코드 입력 시 일봉 데이터 수집 (최근 1년) | High | Pending |
| FR-02 | 이동평균선(5, 20, 60일) 계산 및 골든크로스/데드크로스 감지 | High | Pending |
| FR-03 | RSI 계산 및 과매수(70)/과매도(30) 신호 생성 | High | Pending |
| FR-04 | MACD 계산 및 시그널 크로스 감지 | Medium | Pending |
| FR-05 | 볼린저밴드 계산 및 상단/하단 터치 감지 | Medium | Pending |
| FR-06 | 매매 신호 발생 시 콘솔 출력 및 로그 저장 | High | Pending |
| FR-07 | 백테스팅: 기간 지정 후 전략 수익률 계산 | Medium | Pending |
| FR-08 | 관심 종목 목록 파일로 관리 (watchlist.txt) | Low | Pending |

### 3.2 Non-Functional Requirements

| Category | Criteria | Measurement Method |
|----------|----------|-------------------|
| Performance | 종목당 데이터 처리 < 5초 | 실행 시간 측정 |
| Reliability | API 오류 시 재시도 3회 | 에러 로그 확인 |
| Usability | CLI로 단일 명령어 실행 가능 | 직접 실행 테스트 |

---

## 4. Success Criteria

### 4.1 Definition of Done

- [ ] 종목 코드 입력 → 매매 신호 출력 동작
- [ ] 주요 기술적 지표 3개 이상 구현
- [ ] 백테스팅 결과 수익률 출력
- [ ] README에 사용법 문서화

### 4.2 Quality Criteria

- [ ] 타입 힌트 100% 적용
- [ ] 함수별 docstring 작성
- [ ] black 포맷팅 통과

---

## 5. Risks and Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| 데이터 소스 API 변경/중단 | High | Medium | yfinance + pykrx 이중 소스 사용 |
| 잘못된 신호로 인한 손실 | High | Medium | 백테스팅 필수, 알림만 제공 (자동매매 X) |
| 데이터 품질 이슈 (결측값) | Medium | Low | 결측값 처리 로직 추가 |

---

## 6. Architecture Considerations

### 6.1 Project Level Selection

| Level | Characteristics | Recommended For | Selected |
|-------|-----------------|-----------------|:--------:|
| **Starter** | Simple structure | Static sites | ☐ |
| **Dynamic** | Feature-based modules | Web apps, SaaS | ☐ |
| **Enterprise** | Strict layer separation | High-traffic systems | ☐ |
| **Script** | 단일 Python 스크립트 모듈 구조 | CLI 도구, 자동화 스크립트 | ☑ |

### 6.2 Key Architectural Decisions

| Decision | Options | Selected | Rationale |
|----------|---------|----------|-----------|
| 언어 | Python | Python | 데이터 분석 생태계 |
| 데이터 소스 | yfinance / pykrx | yfinance | 글로벌 + 간편 설치 |
| 데이터 처리 | pandas / numpy | pandas | 시계열 데이터 처리 |
| 지표 계산 | ta-lib / pandas-ta / 직접구현 | pandas-ta | 설치 간편, 다양한 지표 |
| 알림 | 이메일 / 콘솔 / 슬랙 | 콘솔 + 로그파일 | 초기 버전 단순화 |
| 스케줄러 | cron / APScheduler / 수동 | 수동 실행 | 초기 버전 단순화 |

### 6.3 Folder Structure

```
stock-automation/
├── main.py              # 진입점 (CLI)
├── config.py            # 설정 (종목 목록, 파라미터)
├── data/
│   ├── fetcher.py       # 데이터 수집 (yfinance)
│   └── processor.py     # 데이터 전처리
├── indicators/
│   ├── moving_average.py
│   ├── rsi.py
│   ├── macd.py
│   └── bollinger.py
├── signals/
│   └── generator.py     # 매매 신호 생성
├── backtest/
│   └── engine.py        # 백테스팅 엔진
├── utils/
│   └── logger.py        # 로깅
├── watchlist.txt        # 관심 종목 목록
├── requirements.txt
└── docs/                # PDCA 문서
```

---

## 7. Convention Prerequisites

### 7.1 Existing Project Conventions

- [x] `/study/CLAUDE.md` 에 Python 규칙 존재
- [ ] `docs/01-plan/conventions.md` 미존재
- [ ] `requirements.txt` 미존재

### 7.2 Conventions to Define/Verify

| Category | Current State | To Define | Priority |
|----------|---------------|-----------|:--------:|
| **Naming** | CLAUDE.md 참조 | snake_case 전체 적용 | High |
| **Folder structure** | 위 6.3 기준 | 위 구조 확정 | High |
| **타입 힌트** | CLAUDE.md 적용 | 모든 함수 필수 | High |
| **로깅** | 미정 | logging 모듈 사용 | Medium |

### 7.3 Environment Variables Needed

| Variable | Purpose | Scope | To Be Created |
|----------|---------|-------|:-------------:|
| `LOG_LEVEL` | 로그 레벨 설정 | 로컬 | ☐ |

---

## 8. Next Steps

1. [ ] 설계 문서 작성 (`stock-automation.design.md`)
2. [ ] requirements.txt 작성 및 패키지 설치
3. [ ] 구현 시작

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-02-27 | Initial draft | gwangho |

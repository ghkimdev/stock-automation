# stock-automation-webpage Planning Document

> **Summary**: 기존 주식 자동화 분석 시스템에 웹 UI/대시보드를 추가하여 브라우저에서 지표와 매매 신호를 시각화
>
> **Project**: stock-automation
> **Feature**: stock-automation-webpage
> **Version**: 0.1.0
> **Author**: gwangho
> **Date**: 2026-02-28
> **Status**: Draft

---

## 1. Overview

### 1.1 Purpose

기존 CLI 기반 주식 자동화 시스템을 웹 브라우저에서 접근 가능한 대시보드로 확장합니다.
차트, 기술적 지표, 매매 신호를 시각적으로 표현하여 가독성과 사용성을 높입니다.

### 1.2 Background

- 기존 `stock-automation` v1.0 은 CLI 출력 + 로그파일 방식 (완료, Match Rate 93%)
- 데이터는 정상적으로 수집·분석되지만 시각화가 없어 직관적 해석이 어려움
- 브라우저 기반 대시보드를 통해 비개발자도 분석 결과 활용 가능

### 1.3 Related Documents

- `docs/01-plan/features/stock-automation.plan.md` — 기존 백엔드 플랜
- `docs/02-design/features/stock-automation.design.md` — 기존 백엔드 설계
- `docs/04-report/stock-automation.report.md` — 기존 완료 리포트

---

## 2. Scope

### 2.1 In Scope

- [ ] Flask 또는 FastAPI 기반 REST API 서버 구축
- [ ] 종목 검색 및 분석 결과 API 엔드포인트
- [ ] 가격 차트 (OHLCV + 이동평균선) 시각화
- [ ] RSI, MACD, 볼린저밴드 서브차트
- [ ] 매매 신호 표시 (매수/매도 마커)
- [ ] 관심 종목 목록(watchlist) UI 관리
- [ ] 단일 페이지 HTML 대시보드 (SPA 없이 순수 HTML/JS)

### 2.2 Out of Scope

- 실시간 WebSocket 스트리밍
- 사용자 인증/로그인
- 실제 자동 매매 주문
- 데이터베이스 도입 (기존 yfinance 캐시 활용)
- 모바일 앱

---

## 3. Requirements

### 3.1 Functional Requirements

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-01 | 종목 코드 입력 → 분석 결과 JSON 반환 API | High | Pending |
| FR-02 | OHLCV 가격 차트 + 이동평균선(5/20/60일) 시각화 | High | Pending |
| FR-03 | RSI 서브차트 (과매수/과매도 기준선 포함) | High | Pending |
| FR-04 | MACD 서브차트 (시그널 라인, 히스토그램) | Medium | Pending |
| FR-05 | 볼린저밴드 차트 오버레이 | Medium | Pending |
| FR-06 | 매매 신호 마커 (차트 위 매수▲/매도▽ 표시) | High | Pending |
| FR-07 | 관심 종목 목록 화면 표시 및 클릭으로 분석 | Medium | Pending |
| FR-08 | 분석 기간 선택 (1개월/3개월/6개월/1년) | Low | Pending |

### 3.2 Non-Functional Requirements

| Category | Criteria | Measurement Method |
|----------|----------|-------------------|
| Performance | 분석 결과 응답 < 10초 | 브라우저 네트워크 탭 |
| Usability | `python app.py` 단일 명령으로 서버 시작 | 직접 실행 테스트 |
| Compatibility | Chrome/Firefox 최신 버전 지원 | 브라우저 테스트 |
| Portability | 추가 설치 없이 pip requirements로 실행 | 환경 재구성 테스트 |

---

## 4. Success Criteria

### 4.1 Definition of Done

- [ ] `python app.py` 실행 → `http://localhost:5000` 접속 가능
- [ ] 종목 코드(예: AAPL, 005930.KS) 입력 → 차트 렌더링
- [ ] MA, RSI, MACD, 볼린저밴드 4개 지표 모두 시각화
- [ ] 매매 신호가 차트에 마커로 표시

### 4.2 Quality Criteria

- [ ] 기존 indicators/ 모듈 재사용 (코드 중복 없음)
- [ ] API 에러 시 사용자 친화적 메시지 표시
- [ ] 타입 힌트 + docstring 적용 (Python 파일)

---

## 5. Risks and Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| yfinance 응답 지연으로 UI 느림 | Medium | High | 로딩 스피너 + 비동기 fetch |
| 차트 라이브러리 선택 (의존성) | Low | Low | Chart.js CDN 사용 (설치 불필요) |
| 기존 indicators 모듈 import 충돌 | Medium | Low | 경로 설정 및 패키지 구조 검토 |
| Python 3.8 호환성 | Medium | Medium | `from __future__ import annotations` 적용 |

---

## 6. Architecture Considerations

### 6.1 Project Level Selection

| Level | Characteristics | Selected |
|-------|-----------------|:--------:|
| **Script** | 단순 CLI 추가 | ☐ |
| **Starter** | 정적 HTML + API | ☑ |
| **Dynamic** | React/Vue + 풀스택 | ☐ |

> **Rationale**: 기존 Python 모듈을 Flask API로 래핑 + 순수 HTML/JS 프론트엔드.
> 빠른 구현과 최소 의존성을 위해 Starter 수준으로 결정.

### 6.2 Key Architectural Decisions

| Decision | Options | Selected | Rationale |
|----------|---------|----------|-----------|
| 백엔드 프레임워크 | Flask / FastAPI / Django | Flask | 경량, Python 3.8 호환, 빠른 프로토타입 |
| 차트 라이브러리 | Chart.js / Plotly.js / D3.js | Chart.js | CDN 사용, 학습 곡선 낮음 |
| 프론트엔드 방식 | React SPA / 순수 HTML | 순수 HTML/JS | 빌드 과정 불필요 |
| 데이터 포맷 | JSON REST API | JSON | 기존 pandas 데이터 직렬화 |

### 6.3 Folder Structure

```
stock-automation/
├── app.py                   # Flask 앱 진입점 (NEW)
├── api/                     # NEW
│   ├── __init__.py
│   └── routes.py            # REST API 라우트
├── static/                  # NEW
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── dashboard.js     # 차트 렌더링 로직
├── templates/               # NEW
│   └── index.html           # 단일 대시보드 페이지
├── data/                    # 기존
├── indicators/              # 기존 (재사용)
├── signals/                 # 기존 (재사용)
└── docs/
```

---

## 7. Convention Prerequisites

### 7.1 Conventions to Apply

| Category | Convention |
|----------|------------|
| Python | `from __future__ import annotations`, black 포맷 |
| HTML/CSS | 시맨틱 태그, kebab-case 클래스명 |
| JavaScript | `const`/`let` 사용, 세미콜론, async/await |
| API | REST, JSON 응답, HTTP 상태코드 준수 |

### 7.2 Dependencies to Add

| Package | Version | Purpose |
|---------|---------|---------|
| flask | >=2.0,<3.0 | 웹 서버 |
| flask-cors | >=3.0 | CORS 헤더 |

---

## 8. Next Steps

1. [ ] 설계 문서 작성 (`stock-automation-webpage.design.md`)
2. [ ] Flask API 라우트 설계 (엔드포인트 목록)
3. [ ] Chart.js 차트 컴포넌트 설계
4. [ ] 구현 시작

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-02-28 | Initial draft | gwangho |

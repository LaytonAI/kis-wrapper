# Phase 7: 문서화

## 목표
- README.md 작성
- API 사용 예제
- CHANGELOG 작성

## 7.1 README.md

### 포함 내용
- 프로젝트 소개
- 설치 방법
- 빠른 시작 (Quick Start)
- API 레퍼런스 개요
- 예제 코드
- 라이선스

## 7.2 API 레퍼런스

### 모듈 구조
```
kis/
├── KIS          - API 클라이언트
├── domestic     - 국내주식 API
├── overseas     - 해외주식 API
├── WSClient     - 실시간 WebSocket
├── calc         - 계산 유틸리티
└── snapshot     - 스냅샷 저장/검증
```

### domestic 모듈
| 함수 | 설명 |
|------|------|
| price(kis, symbol) | 현재가 조회 |
| orderbook(kis, symbol) | 호가 조회 |
| daily(kis, symbol, period) | 일/주/월봉 |
| buy(kis, symbol, qty, price) | 매수 |
| sell(kis, symbol, qty, price) | 매도 |
| cancel(kis, order_no, qty) | 취소 |
| modify(kis, order_no, qty, price) | 정정 |
| balance(kis) | 잔고 조회 |
| positions(kis) | 보유종목 |
| orders(kis) | 주문내역 |
| pending_orders(kis) | 미체결 |
| position(kis, symbol) | 종목별 포지션 |
| sell_all(kis, symbol) | 전량 매도 |

### overseas 모듈
| 함수 | 설명 |
|------|------|
| price(kis, symbol, exchange) | 현재가 조회 |
| daily(kis, symbol, exchange, period) | 기간별 시세 |
| buy(kis, symbol, exchange, qty, price) | 매수 |
| sell(kis, symbol, exchange, qty, price) | 매도 |
| cancel(kis, exchange, order_no, qty) | 취소 |
| balance(kis, exchange) | 잔고 조회 |
| exchange_rate(kis) | 환율 조회 |

### WSClient
| 메서드 | 설명 |
|--------|------|
| connect() | 연결 |
| subscribe(tr_id, symbols, callback) | 구독 |
| unsubscribe(tr_id, symbols) | 해제 |
| run() | 수신 루프 |
| close() | 종료 |

## 7.3 예제 코드

### examples/ 구조
```
examples/
├── basic.py           # 기본 사용
├── domestic_order.py  # 국내주식 주문
├── overseas_order.py  # 해외주식 주문
└── realtime.py        # 실시간 데이터
```

## 완료 조건
- [x] README.md 작성
- [x] examples/ 예제 코드
- [x] CHANGELOG.md 작성

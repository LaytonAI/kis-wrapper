# Changelog

## [0.2.0] - 2025-01-16

### Added
- **에러 처리 강화**
  - 공식 문서 기반 에러코드 체계 (EGW/OPSQ/OPSP/APBK)
  - 계층적 에러 클래스 (KISError → GatewayError → AuthError 등)
  - 429 Rate Limit 자동 재시도 (지수 백오프)

- **해외주식 API 확장**
  - 호가 조회 (orderbook)
  - 주문 정정 (modify)
  - 체결내역 조회 (orders)
  - 미체결 조회 (pending_orders)
  - 포지션 관리 (positions, position, sell_all)

### Changed
- 코드 단순화 및 최적화
- 테스트 파라미터화로 중복 제거

## [0.1.0] - 2025-01-16

### Added

- **Core**
  - `KIS` 클라이언트 클래스
  - 자동 토큰 관리 (발급/갱신)
  - 모의투자/실전 환경 전환

- **국내주식 (domestic)**
  - 현재가/호가 조회
  - 일/주/월봉 데이터
  - 매수/매도 주문 (지정가/시장가)
  - 주문 취소/정정
  - 잔고/보유종목 조회
  - 주문내역/미체결 조회
  - 종목별 포지션 조회
  - 전량 매도

- **해외주식 (overseas)**
  - 현재가/기간별 시세
  - 매수/매도 주문
  - 주문 취소
  - 잔고 조회
  - 환율 조회
  - 9개 거래소 지원 (NYS, NAS, AMS, HKS, SHS, SZS, TSE, HNX, HSX)

- **WebSocket (WSClient)**
  - 실시간 체결가/호가 수신
  - 자동 재연결 (지수 백오프)
  - AES 복호화 지원
  - 구독 복원

- **유틸리티**
  - 수익률/수익금 계산 (calc)
  - 평균단가 계산
  - 스냅샷 저장/검증 (snapshot)

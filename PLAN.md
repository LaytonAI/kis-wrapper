# KIS Wrapper SDK

## 설계 철학 (geohot style)
- **간결함이 생명**: less code is better
- **함수 중심**: 불필요한 클래스 추상화 자제
- **클래스는 상태 공유 필요시에만**: Client, WebSocket 정도
- **TDD**: 테스트 먼저, 구현은 그 다음
- **무결성**: 오차/결함 zero tolerance

## 개요
- **목적**: 자동매매 봇 + 범용 SDK
- **스택**: Python 3.11+
- **Source of Truth**: KIS 공식 문서 (Excel)

## 프로젝트 구조
```
kis-wrapper/
├── pyproject.toml
├── kis/                    # flat structure
│   ├── __init__.py
│   ├── auth.py             # 토큰 발급/갱신
│   ├── client.py           # KIS 클래스 (유일한 상태)
│   ├── ws.py               # WebSocket
│   ├── domestic.py         # 국내주식 함수
│   ├── overseas.py         # 해외주식 함수
│   ├── types.py            # TypedDict
│   └── utils.py
├── tests/
│   └── fixtures/           # API 응답 스냅샷
├── docs/                   # API 스펙
└── examples/
```

## 사용 예시
```python
from kis import KIS, domestic

# 모의투자
kis = KIS(app_key, app_secret, account, env="paper")

# 현재가
p = domestic.price(kis, "005930")

# 매수
order = domestic.buy(kis, "005930", qty=10, price=70000)

# 실전으로 전환
kis_prod = kis.switch("prod")
```

## Phase 문서
- [Phase1.md](./Phase1.md) - 프로젝트 초기화 + 문서 수집
- [Phase2.md](./Phase2.md) - Core (auth, client)
- [Phase3.md](./Phase3.md) - 국내주식 API
- [Phase4.md](./Phase4.md) - 데이터 무결성
- [Phase5.md](./Phase5.md) - WebSocket
- [Phase6.md](./Phase6.md) - 해외주식

## TDD 프로세스
1. 테스트 먼저 작성
2. 실패 확인 (red)
3. 최소 구현 (green)
4. 리팩토링
5. 스냅샷 저장

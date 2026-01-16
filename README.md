# KIS Wrapper

한국투자증권 Open API Python SDK

## 특징

- 간결한 함수 기반 API
- 국내/해외주식 지원
- 실시간 WebSocket
- 모의투자/실전 환경 전환
- 자동 토큰 관리

## 설치

```bash
pip install kis
```

또는 개발 환경:

```bash
git clone https://github.com/your-repo/kis-wrapper
cd kis-wrapper
uv sync
```

## 빠른 시작

### 환경 설정

```bash
# .env
KIS_APP_KEY=your_app_key
KIS_APP_SECRET=your_app_secret
KIS_ACCOUNT=12345678-01
```

### 기본 사용

```python
import os
from kis import KIS, domestic

kis = KIS(
    app_key=os.environ["KIS_APP_KEY"],
    app_secret=os.environ["KIS_APP_SECRET"],
    account=os.environ["KIS_ACCOUNT"],
    env="paper",  # 모의투자
)

# 삼성전자 현재가
p = domestic.price(kis, "005930")
print(f"현재가: {p['stck_prpr']}원")

# 호가
ob = domestic.orderbook(kis, "005930")

# 일봉 (최근 30일)
candles = domestic.daily(kis, "005930")
```

### 주문

```python
# 매수 (지정가)
order = domestic.buy(kis, "005930", qty=10, price=70000)
print(f"주문번호: {order['ODNO']}")

# 매수 (시장가)
order = domestic.buy(kis, "005930", qty=10)

# 매도
order = domestic.sell(kis, "005930", qty=5, price=72000)

# 주문 취소
domestic.cancel(kis, order_no="0001234567", qty=5)

# 주문 정정
domestic.modify(kis, order_no="0001234567", qty=10, price=71000)
```

### 계좌 조회

```python
# 잔고 (예수금 + 보유종목)
bal = domestic.balance(kis)

# 보유종목만
positions = domestic.positions(kis)
for p in positions:
    print(f"{p['prdt_name']}: {p['hldg_qty']}주")

# 특정 종목 포지션
pos = domestic.position(kis, "005930")
if pos:
    print(f"수익률: {pos['profit_rate']:.2f}%")

# 미체결 주문
pending = domestic.pending_orders(kis)
```

### 해외주식

```python
from kis import overseas

# 애플 현재가
p = overseas.price(kis, "AAPL", "NAS")
print(f"AAPL: ${p['last']}")

# 매수 (지정가)
order = overseas.buy(kis, "AAPL", "NAS", qty=1, price=150.00)

# 매수 (시장가 - 미국만 지원)
order = overseas.buy(kis, "AAPL", "NAS", qty=1)

# 잔고 조회
bal = overseas.balance(kis)  # 전체
bal = overseas.balance(kis, "NAS")  # 나스닥만

# 환율
rate = overseas.exchange_rate(kis)
```

#### 거래소 코드

| 코드 | 거래소 |
|------|--------|
| NYS | 뉴욕 (NYSE) |
| NAS | 나스닥 (NASDAQ) |
| AMS | 아멕스 (AMEX) |
| HKS | 홍콩 |
| SHS | 상해 |
| SZS | 심천 |
| TSE | 도쿄 |
| HNX | 하노이 |
| HSX | 호치민 |

### 실시간 데이터 (WebSocket)

```python
import asyncio
from kis import KIS, WSClient

async def main():
    kis = KIS(app_key, app_secret, account, env="paper")
    ws = WSClient(kis)

    async def on_price(data):
        print(f"{data['symbol']}: {data['price']:,}원 (거래량: {data['volume']})")

    await ws.subscribe("H0STCNT0", ["005930", "000660"], on_price)

    try:
        await ws.run()
    except KeyboardInterrupt:
        await ws.close()

asyncio.run(main())
```

#### TR ID 목록

| TR ID | 설명 |
|-------|------|
| H0STCNT0 | 국내주식 실시간체결 |
| H0STASP0 | 국내주식 실시간호가 |
| H0STCNI0 | 체결통보 |
| HDFSCNT0 | 해외주식 실시간체결 |

### 환경 전환

```python
# 모의투자 -> 실전
kis_prod = kis.switch("prod")

# 또는 처음부터 실전
kis = KIS(app_key, app_secret, account, env="prod")
```

### 계산 유틸리티

```python
from kis import calc

# 수익률
rate = calc.profit_rate(buy_price=70000, current_price=75000)
print(f"수익률: {float(rate) * 100:.2f}%")

# 수익금
profit = calc.profit_amount(70000, 75000, qty=10)

# 평균단가
orders = [{"price": 70000, "qty": 10}, {"price": 72000, "qty": 5}]
avg = calc.avg_price(orders)
```

### 스냅샷

```python
from kis import snapshot

# 현재 상태 저장
data = snapshot.snapshot(kis, "005930")
snapshot.save(data, "snapshots/005930.json")

# 로드 및 검증
loaded = snapshot.load("snapshots/005930.json")
assert snapshot.verify(loaded)
```

## API 레퍼런스

### KIS 클래스

```python
KIS(app_key: str, app_secret: str, account: str, env: Env = "paper")
```

| 속성/메서드 | 설명 |
|-------------|------|
| `is_paper` | 모의투자 여부 |
| `switch(env)` | 환경 전환 |
| `close()` | 연결 종료 |

### domestic 모듈

| 함수 | 설명 |
|------|------|
| `price(kis, symbol)` | 현재가 조회 |
| `orderbook(kis, symbol)` | 호가 조회 |
| `daily(kis, symbol, period="D")` | 일/주/월봉 |
| `buy(kis, symbol, qty, price=None)` | 매수 |
| `sell(kis, symbol, qty, price=None)` | 매도 |
| `cancel(kis, order_no, qty)` | 취소 |
| `modify(kis, order_no, qty, price)` | 정정 |
| `balance(kis)` | 잔고 조회 |
| `positions(kis)` | 보유종목 |
| `orders(kis, start_date, end_date)` | 주문내역 |
| `pending_orders(kis)` | 미체결 |
| `position(kis, symbol)` | 종목별 포지션 |
| `sell_all(kis, symbol)` | 전량 매도 |
| `cancel_remaining(kis, order_no)` | 미체결 전량 취소 |

### overseas 모듈

| 함수 | 설명 |
|------|------|
| `price(kis, symbol, exchange)` | 현재가 조회 |
| `daily(kis, symbol, exchange, period="D")` | 기간별 시세 |
| `buy(kis, symbol, exchange, qty, price=None)` | 매수 |
| `sell(kis, symbol, exchange, qty, price=None)` | 매도 |
| `cancel(kis, exchange, order_no, qty)` | 취소 |
| `balance(kis, exchange=None)` | 잔고 조회 |
| `exchange_rate(kis)` | 환율 조회 |

### WSClient 클래스

```python
WSClient(kis: KIS, max_retries: int = 5, retry_delay: float = 1.0)
```

| 메서드 | 설명 |
|--------|------|
| `connect()` | WebSocket 연결 |
| `subscribe(tr_id, symbols, callback)` | 구독 |
| `unsubscribe(tr_id, symbols)` | 구독 해제 |
| `run()` | 메시지 수신 루프 |
| `close()` | 연결 종료 |

## 개발

```bash
# 테스트
uv run pytest

# 커버리지
uv run pytest --cov=kis

# 린트
uv run ruff check kis/

# 포맷
uv run ruff format kis/
```

## 라이선스

MIT License

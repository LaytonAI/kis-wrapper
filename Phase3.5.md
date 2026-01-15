# Phase 3.5: 유틸리티 및 포지션 관리

## 목표
- 호가단위, 수수료 계산 유틸리티
- 포지션 관리 (스태킹, 일괄 청산)
- 부분체결 처리

## 조사 결과

### 수수료
| 구분 | 실전투자 | 모의투자 |
|------|----------|----------|
| 수수료 적용 | 실제 차감 | 시뮬레이션 적용 |
| 국내 (우대) | 0.003~0.004% | 확인 필요 |
| 해외 (미국) | 0.25% | 확인 필요 |
| 거래세 (매도) | 0.18% | - |

> 모의투자 수수료율은 실제 매매로 확인 예정

### 호가단위 (2023.01.25 개편)
| 가격대 | 호가단위 |
|--------|----------|
| ~2,000원 | 1원 |
| 2,000~5,000원 | 5원 |
| 5,000~10,000원 | 10원 |
| 10,000~20,000원 | 10원 |
| 20,000~50,000원 | 50원 |
| 50,000~100,000원 | 100원 |
| 100,000~200,000원 | 100원 |
| 200,000~500,000원 | 500원 |
| 500,000원~ | 1,000원 |

### 소수점 처리
- 국내: 정수만 (`int`)
- 해외: 6자리 (`Decimal`)

---

## 3.5.1 유틸리티 함수

### 인터페이스
```python
# kis/utils.py

def tick_size(price: int) -> int:
    """가격대별 호가단위 반환"""
    if price < 2000: return 1
    if price < 5000: return 5
    if price < 20000: return 10
    if price < 50000: return 50
    if price < 200000: return 100
    if price < 500000: return 500
    return 1000

def round_price(price: int, direction: str = "down") -> int:
    """호가단위에 맞게 가격 조정

    Args:
        direction: "down" (내림), "up" (올림), "nearest" (반올림)
    """
    tick = tick_size(price)
    if direction == "down":
        return (price // tick) * tick
    if direction == "up":
        return ((price + tick - 1) // tick) * tick
    # nearest
    return round(price / tick) * tick

def calc_fee(amount: int, rate: float = 0.00015) -> int:
    """수수료 계산 (기본: 0.015%)"""
    return int(amount * rate)

def calc_tax(amount: int, rate: float = 0.0018) -> int:
    """거래세 계산 (매도 시, 기본: 0.18%)"""
    return int(amount * rate)
```

### 테스트
```python
def test_tick_size():
    assert tick_size(1500) == 1
    assert tick_size(3000) == 5
    assert tick_size(15000) == 10
    assert tick_size(70000) == 100
    assert tick_size(300000) == 500

def test_round_price_down():
    assert round_price(70050, "down") == 70000
    assert round_price(70099, "down") == 70000

def test_round_price_up():
    assert round_price(70001, "up") == 70100
    assert round_price(70100, "up") == 70100
```

---

## 3.5.2 포지션 관리

### 인터페이스
```python
# kis/domestic.py 추가

def position(kis: KIS, symbol: str) -> dict | None:
    """종목별 포지션 조회

    Returns:
        {
            "symbol": "005930",
            "name": "삼성전자",
            "qty": 150,
            "avg_price": 68000,
            "current_price": 70000,
            "total_cost": 10200000,
            "eval_amount": 10500000,
            "profit": 300000,
            "profit_rate": 2.94
        }
        또는 None (미보유 시)
    """
    for p in positions(kis):
        if p["pdno"] == symbol:
            return {
                "symbol": symbol,
                "name": p["prdt_name"],
                "qty": int(p["hldg_qty"]),
                "avg_price": int(float(p["pchs_avg_pric"])),
                "current_price": int(p["prpr"]),
                "total_cost": int(p["pchs_amt"]),
                "eval_amount": int(p["evlu_amt"]),
                "profit": int(p["evlu_pfls_amt"]),
                "profit_rate": float(p["evlu_pfls_rt"]),
            }
    return None

def sell_all(kis: KIS, symbol: str) -> dict:
    """종목 전량 매도 (시장가)"""
    pos = position(kis, symbol)
    if not pos or pos["qty"] == 0:
        raise ValueError(f"No position for {symbol}")
    return sell(kis, symbol, qty=pos["qty"])

def cancel_remaining(kis: KIS, order_no: str) -> dict:
    """미체결 잔량 전부 취소"""
    body = {
        **_account_params(kis),
        "KRX_FWDG_ORD_ORGNO": "",
        "ORGN_ODNO": order_no,
        "ORD_DVSN": "00",
        "RVSE_CNCL_DVSN_CD": "02",
        "ORD_QTY": "0",
        "ORD_UNPR": "0",
        "QTY_ALL_ORD_YN": "Y",
    }
    return kis.post(
        "/uapi/domestic-stock/v1/trading/order-rvsecncl",
        body,
        _tr_id(kis, "VTTC0803U", "TTTC0803U"),
    )
```

### 테스트
```python
def test_position_found(kis, httpx_mock):
    httpx_mock.add_response(json={"rt_cd": "0", "output": balance_fixture})

    pos = domestic.position(kis, "005930")

    assert pos["symbol"] == "005930"
    assert pos["qty"] == 100
    assert pos["profit_rate"] == 2.94

def test_position_not_found(kis, httpx_mock):
    httpx_mock.add_response(json={"rt_cd": "0", "output": {"output1": []}})

    assert domestic.position(kis, "999999") is None

def test_sell_all(kis, httpx_mock):
    # balance 조회 -> sell 주문
    httpx_mock.add_response(json={"rt_cd": "0", "output": balance_fixture})
    httpx_mock.add_response(json={"rt_cd": "0", "output": {"ODNO": "123"}})

    result = domestic.sell_all(kis, "005930")

    # sell 요청 검증
    requests = httpx_mock.get_requests()
    sell_body = json.loads(requests[1].content)
    assert sell_body["ORD_QTY"] == "100"
```

---

## 3.5.3 부분체결 처리

### 체결 상태 판단
```python
def order_status(order: dict) -> str:
    """주문 체결 상태 반환

    Returns:
        "filled": 전량 체결
        "partial": 부분 체결
        "pending": 미체결
    """
    ord_qty = int(order.get("ord_qty", 0))
    ccld_qty = int(order.get("tot_ccld_qty", 0))

    if ccld_qty == 0:
        return "pending"
    if ccld_qty >= ord_qty:
        return "filled"
    return "partial"
```

---

## 완료 조건
- [x] kis/utils.py에 tick_size, round_price 구현
- [x] kis/utils.py에 calc_fee, calc_tax 구현
- [x] test_utils.py 테스트 작성/통과
- [x] kis/domestic.py에 position, sell_all 추가
- [x] kis/domestic.py에 cancel_remaining 추가
- [x] test_domestic.py에 포지션 테스트 추가
- [ ] 모의투자 수수료율 확인 (실매매 테스트)

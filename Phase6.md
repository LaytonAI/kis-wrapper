# Phase 6: 해외주식

## 목표
- 해외주식 시세 조회
- 해외주식 주문
- 환율/환전 조회

## 설계 원칙
- domestic.py와 동일한 패턴
- 거래소 코드 명시 필수
- 소수점 가격 지원 (float)

## 6.1 거래소 코드

```python
# kis/types.py
from typing import Literal

Exchange = Literal[
    "NYS",   # 뉴욕
    "NAS",   # 나스닥
    "AMS",   # 아멕스
    "HKS",   # 홍콩
    "SHS",   # 상해
    "SZS",   # 심천
    "TSE",   # 도쿄
    "HNX",   # 하노이
    "HSX",   # 호치민
]

EXCHANGE_MAP = {
    "NYS": "NYSE",
    "NAS": "NASD",
    "AMS": "AMEX",
    "HKS": "SEHK",
    "SHS": "SHAA",
    "SZS": "SZAA",
    "TSE": "TKSE",
}
```

## 6.2 해외주식 함수

### 인터페이스
```python
# kis/overseas.py
from kis.client import KIS
from kis.types import Exchange

def price(kis: KIS, symbol: str, exchange: Exchange) -> dict:
    """해외주식 현재가 조회

    Args:
        symbol: 종목코드 (예: "AAPL", "TSLA")
        exchange: 거래소 (예: "NAS", "NYS")

    Returns:
        {
            "last": "150.25",
            "diff": "2.50",
            "rate": "1.69",
            "tvol": "12345678",
            ...
        }
    """
    params = {
        "AUTH": "",
        "EXCD": exchange,
        "SYMB": symbol,
    }
    tr_id = "HHDFS00000300"
    return kis.get("/uapi/overseas-price/v1/quotations/price", params, tr_id)

def daily(
    kis: KIS,
    symbol: str,
    exchange: Exchange,
    period: str = "D",
    count: int = 30,
) -> list[dict]:
    """해외주식 기간별 시세

    Args:
        period: "D" (일), "W" (주), "M" (월)
    """
    params = {
        "AUTH": "",
        "EXCD": exchange,
        "SYMB": symbol,
        "GUBN": {"D": "0", "W": "1", "M": "2"}[period],
        "BYMD": "",
        "MODP": "1",
    }
    return kis.get("/uapi/overseas-price/v1/quotations/dailyprice", params, "HHDFS76240000")

def buy(
    kis: KIS,
    symbol: str,
    exchange: Exchange,
    qty: int,
    price: float | None = None,
) -> dict:
    """해외주식 매수

    Args:
        price: None이면 시장가 (지원 거래소만)
    """
    order_type = "00" if price else "01"  # 지정가/시장가

    body = {
        "CANO": kis.account[:8],
        "ACNT_PRDT_CD": kis.account[9:11],
        "OVRS_EXCG_CD": exchange,
        "PDNO": symbol,
        "ORD_QTY": str(qty),
        "OVRS_ORD_UNPR": str(price or 0),
        "ORD_SVR_DVSN_CD": "0",
        "ORD_DVSN": order_type,
    }

    # 거래소별 TR ID
    tr_id = _buy_tr_id(exchange, kis.is_paper)
    return kis.post("/uapi/overseas-stock/v1/trading/order", body, tr_id)

def sell(
    kis: KIS,
    symbol: str,
    exchange: Exchange,
    qty: int,
    price: float | None = None,
) -> dict:
    """해외주식 매도"""
    order_type = "00" if price else "01"

    body = {
        "CANO": kis.account[:8],
        "ACNT_PRDT_CD": kis.account[9:11],
        "OVRS_EXCG_CD": exchange,
        "PDNO": symbol,
        "ORD_QTY": str(qty),
        "OVRS_ORD_UNPR": str(price or 0),
        "ORD_SVR_DVSN_CD": "0",
        "ORD_DVSN": order_type,
        "SLL_TYPE": "00",
    }

    tr_id = _sell_tr_id(exchange, kis.is_paper)
    return kis.post("/uapi/overseas-stock/v1/trading/order", body, tr_id)

def cancel(kis: KIS, exchange: Exchange, order_no: str, qty: int) -> dict:
    """해외주식 주문 취소"""
    body = {
        "CANO": kis.account[:8],
        "ACNT_PRDT_CD": kis.account[9:11],
        "OVRS_EXCG_CD": exchange,
        "ORGN_ODNO": order_no,
        "RVSE_CNCL_DVSN_CD": "02",
        "ORD_QTY": str(qty),
        "OVRS_ORD_UNPR": "0",
    }
    return kis.post("/uapi/overseas-stock/v1/trading/order-rvsecncl", body, "TTTT1004U")

def balance(kis: KIS, exchange: Exchange | None = None) -> dict:
    """해외주식 잔고 조회

    Args:
        exchange: None이면 전체 거래소
    """
    params = {
        "CANO": kis.account[:8],
        "ACNT_PRDT_CD": kis.account[9:11],
        "OVRS_EXCG_CD": exchange or "",
        "TR_CRCY_CD": "",
        "CTX_AREA_FK200": "",
        "CTX_AREA_NK200": "",
    }
    return kis.get("/uapi/overseas-stock/v1/trading/inquire-balance", params, "TTTS3012R")

def exchange_rate(kis: KIS, currency: str = "USD") -> dict:
    """환율 조회"""
    params = {"CANO": kis.account[:8], "ACNT_PRDT_CD": kis.account[9:11]}
    return kis.get("/uapi/overseas-stock/v1/trading/inquire-present-balance", params, "CTRP6504R")

def _buy_tr_id(exchange: str, is_paper: bool) -> str:
    """거래소별 매수 TR ID"""
    base = {
        "NAS": "JTTT1002U",
        "NYS": "JTTT1002U",
        "AMS": "JTTT1002U",
        "HKS": "TTTS1002U",
        "SHS": "TTTS0202U",
        "SZS": "TTTS0305U",
        "TSE": "TTTS0308U",
    }
    tr = base.get(exchange, "JTTT1002U")
    # 모의투자는 TR ID 다름
    if is_paper:
        tr = tr.replace("T", "V", 1) if tr.startswith("TT") else tr
    return tr

def _sell_tr_id(exchange: str, is_paper: bool) -> str:
    """거래소별 매도 TR ID"""
    base = {
        "NAS": "JTTT1006U",
        "NYS": "JTTT1006U",
        "AMS": "JTTT1006U",
        "HKS": "TTTS1001U",
        "SHS": "TTTS1005U",
        "SZS": "TTTS0304U",
        "TSE": "TTTS0307U",
    }
    tr = base.get(exchange, "JTTT1006U")
    if is_paper:
        tr = tr.replace("T", "V", 1) if tr.startswith("TT") else tr
    return tr
```

### 사용 예시
```python
from kis import KIS, overseas

kis = KIS(app_key, app_secret, account, env="paper")

# 애플 현재가
p = overseas.price(kis, "AAPL", "NAS")
print(f"AAPL: ${p['last']}")

# 매수 (지정가)
order = overseas.buy(kis, "AAPL", "NAS", qty=1, price=150.00)

# 매수 (시장가)
order = overseas.buy(kis, "AAPL", "NAS", qty=1)

# 잔고 조회 (전체)
bal = overseas.balance(kis)
```

## 6.3 테스트

```python
# tests/test_overseas.py
import pytest
from kis import overseas

@pytest.fixture
def price_fixture():
    return {
        "rsym": "DNASAAPL",
        "last": "150.25",
        "diff": "2.50",
        "rate": "1.69",
    }

def test_price(kis, price_fixture, httpx_mock):
    httpx_mock.add_response(json={"rt_cd": "0", "output": price_fixture})

    result = overseas.price(kis, "AAPL", "NAS")

    assert result["last"] == "150.25"

def test_buy_limit_order(kis, httpx_mock):
    httpx_mock.add_response(json={"rt_cd": "0", "output": {"ODNO": "123"}})

    result = overseas.buy(kis, "AAPL", "NAS", qty=1, price=150.0)

    request = httpx_mock.get_request()
    body = request.json()
    assert body["ORD_DVSN"] == "00"  # 지정가
    assert body["OVRS_ORD_UNPR"] == "150.0"

def test_buy_market_order(kis, httpx_mock):
    httpx_mock.add_response(json={"rt_cd": "0", "output": {"ODNO": "123"}})

    result = overseas.buy(kis, "AAPL", "NAS", qty=1)  # price=None

    request = httpx_mock.get_request()
    body = request.json()
    assert body["ORD_DVSN"] == "01"  # 시장가

def test_buy_tr_id_for_nasdaq():
    tr = overseas._buy_tr_id("NAS", is_paper=False)
    assert tr == "JTTT1002U"

    tr = overseas._buy_tr_id("NAS", is_paper=True)
    # 모의투자도 동일 (미국주식)
    assert tr == "JTTT1002U"
```

## 6.4 주의사항

### 시장가 주문 지원
- 미국: 지원 (NAS, NYS, AMS)
- 홍콩: 미지원
- 중국: 미지원
- 일본: 미지원

### 주문 시간
- 미국: 23:30 ~ 06:00 (서머타임 22:30 ~ 05:00)
- 홍콩: 10:30 ~ 17:00
- 일본: 09:00 ~ 15:00

### 소수점 처리
- 미국: 소수점 2자리 (0.01 단위)
- 기타: 거래소별 상이

## 완료 조건
- [ ] test_overseas.py 작성/통과
- [ ] overseas.py 구현
- [ ] 미국주식 시세/주문 테스트
- [ ] 거래소별 TR ID 매핑 검증
- [ ] 환율 조회 테스트

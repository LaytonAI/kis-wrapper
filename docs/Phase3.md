# Phase 3: 국내주식 API

## 목표
- 시세 조회 함수
- 주문 함수 (매수/매도/정정/취소)
- 계좌 조회 함수

## 설계 원칙
- 순수 함수 (KIS 인스턴스를 첫 번째 인자로)
- dict 반환 (과도한 모델링 자제)
- 필수 파라미터만 노출

## 3.1 시세 조회

### 인터페이스
```python
# kis/domestic.py
from kis.client import KIS

def price(kis: KIS, symbol: str) -> dict:
    """현재가 조회

    Args:
        kis: KIS 클라이언트
        symbol: 종목코드 (예: "005930")

    Returns:
        {
            "stck_prpr": "70000",      # 현재가
            "prdy_vrss": "-1000",      # 전일대비
            "prdy_ctrt": "-1.41",      # 전일대비율
            "acml_vol": "12345678",    # 거래량
            ...
        }
    """
    return kis.get(
        "/uapi/domestic-stock/v1/quotations/inquire-price",
        {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": symbol},
        "FHKST01010100"
    )

def orderbook(kis: KIS, symbol: str) -> dict:
    """호가 조회"""
    return kis.get(
        "/uapi/domestic-stock/v1/quotations/inquire-asking-price-exp-ccn",
        {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": symbol},
        "FHKST01010200"
    )

def daily(kis: KIS, symbol: str, period: str = "D", count: int = 30) -> list[dict]:
    """일/주/월봉 조회

    Args:
        period: "D" (일), "W" (주), "M" (월)
        count: 조회 개수
    """
    return kis.get(
        "/uapi/domestic-stock/v1/quotations/inquire-daily-price",
        {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": symbol,
            "FID_PERIOD_DIV_CODE": period,
            "FID_ORG_ADJ_PRC": "0",
        },
        "FHKST01010400"
    )
```

### 테스트
```python
# tests/test_domestic.py
import pytest
from kis import domestic

@pytest.fixture
def price_response():
    """tests/fixtures/domestic_price.json 로드"""
    ...

def test_price_returns_required_fields(kis, price_response, httpx_mock):
    httpx_mock.add_response(json={"rt_cd": "0", "output": price_response})

    result = domestic.price(kis, "005930")

    assert "stck_prpr" in result
    assert "prdy_vrss" in result
    assert "acml_vol" in result

def test_price_with_invalid_symbol(kis, httpx_mock):
    httpx_mock.add_response(json={"rt_cd": "1", "msg1": "종목코드 오류"})

    with pytest.raises(APIError):
        domestic.price(kis, "INVALID")
```

## 3.2 주문

### 인터페이스
```python
def buy(
    kis: KIS,
    symbol: str,
    qty: int,
    price: int | None = None,
    order_type: str = "00"  # 00: 지정가, 01: 시장가
) -> dict:
    """매수 주문

    Args:
        price: None이면 시장가

    Returns:
        {"ODNO": "0000123456", "ORD_TMD": "092500", ...}
    """
    if price is None:
        order_type = "01"
        price = 0

    body = {
        "CANO": kis.account[:8],
        "ACNT_PRDT_CD": kis.account[9:11],
        "PDNO": symbol,
        "ORD_DVSN": order_type,
        "ORD_QTY": str(qty),
        "ORD_UNPR": str(price),
    }

    tr_id = "TTTC0802U" if kis.is_paper else "TTTC0802U"
    return kis.post("/uapi/domestic-stock/v1/trading/order-cash", body, tr_id)

def sell(
    kis: KIS,
    symbol: str,
    qty: int,
    price: int | None = None,
    order_type: str = "00"
) -> dict:
    """매도 주문"""
    if price is None:
        order_type = "01"
        price = 0

    body = {
        "CANO": kis.account[:8],
        "ACNT_PRDT_CD": kis.account[9:11],
        "PDNO": symbol,
        "ORD_DVSN": order_type,
        "ORD_QTY": str(qty),
        "ORD_UNPR": str(price),
    }

    tr_id = "TTTC0801U" if kis.is_paper else "TTTC0801U"
    return kis.post("/uapi/domestic-stock/v1/trading/order-cash", body, tr_id)

def cancel(kis: KIS, order_no: str, qty: int) -> dict:
    """주문 취소"""
    body = {
        "CANO": kis.account[:8],
        "ACNT_PRDT_CD": kis.account[9:11],
        "KRX_FWDG_ORD_ORGNO": "",
        "ORGN_ODNO": order_no,
        "ORD_DVSN": "00",
        "RVSE_CNCL_DVSN_CD": "02",  # 취소
        "ORD_QTY": str(qty),
        "ORD_UNPR": "0",
    }
    return kis.post("/uapi/domestic-stock/v1/trading/order-rvsecncl", body, "TTTC0803U")

def modify(kis: KIS, order_no: str, qty: int, price: int) -> dict:
    """주문 정정"""
    body = {
        "CANO": kis.account[:8],
        "ACNT_PRDT_CD": kis.account[9:11],
        "KRX_FWDG_ORD_ORGNO": "",
        "ORGN_ODNO": order_no,
        "ORD_DVSN": "00",
        "RVSE_CNCL_DVSN_CD": "01",  # 정정
        "ORD_QTY": str(qty),
        "ORD_UNPR": str(price),
    }
    return kis.post("/uapi/domestic-stock/v1/trading/order-rvsecncl", body, "TTTC0803U")
```

### 테스트
```python
def test_buy_market_order(kis, httpx_mock):
    httpx_mock.add_response(json={"rt_cd": "0", "output": {"ODNO": "123"}})

    result = domestic.buy(kis, "005930", qty=10)  # price=None = 시장가

    # 요청 body 검증
    request = httpx_mock.get_request()
    body = request.json()
    assert body["ORD_DVSN"] == "01"  # 시장가

def test_buy_limit_order(kis, httpx_mock):
    httpx_mock.add_response(json={"rt_cd": "0", "output": {"ODNO": "123"}})

    result = domestic.buy(kis, "005930", qty=10, price=70000)

    request = httpx_mock.get_request()
    body = request.json()
    assert body["ORD_DVSN"] == "00"  # 지정가
    assert body["ORD_UNPR"] == "70000"
```

## 3.3 계좌 조회

### 인터페이스
```python
def balance(kis: KIS) -> dict:
    """예수금 조회"""
    params = {
        "CANO": kis.account[:8],
        "ACNT_PRDT_CD": kis.account[9:11],
        "AFHR_FLPR_YN": "N",
        "OFL_YN": "",
        "INQR_DVSN": "02",
        "UNPR_DVSN": "01",
        "FUND_STTL_ICLD_YN": "N",
        "FNCG_AMT_AUTO_RDPT_YN": "N",
        "PRCS_DVSN": "00",
        "CTX_AREA_FK100": "",
        "CTX_AREA_NK100": "",
    }
    return kis.get("/uapi/domestic-stock/v1/trading/inquire-balance", params, "TTTC8434R")

def positions(kis: KIS) -> list[dict]:
    """보유종목 조회"""
    result = balance(kis)
    # output1이 보유종목 리스트
    return result if isinstance(result, list) else []

def orders(kis: KIS, start_date: str = "", end_date: str = "") -> list[dict]:
    """주문내역 조회"""
    from datetime import date
    today = date.today().strftime("%Y%m%d")

    params = {
        "CANO": kis.account[:8],
        "ACNT_PRDT_CD": kis.account[9:11],
        "INQR_STRT_DT": start_date or today,
        "INQR_END_DT": end_date or today,
        "SLL_BUY_DVSN_CD": "00",
        "INQR_DVSN": "00",
        "PDNO": "",
        "CCLD_DVSN": "00",
        "ORD_GNO_BRNO": "",
        "ODNO": "",
        "INQR_DVSN_3": "00",
        "INQR_DVSN_1": "",
        "CTX_AREA_FK100": "",
        "CTX_AREA_NK100": "",
    }
    return kis.get("/uapi/domestic-stock/v1/trading/inquire-daily-ccld", params, "TTTC8001R")

def pending_orders(kis: KIS) -> list[dict]:
    """미체결 주문 조회"""
    params = {
        "CANO": kis.account[:8],
        "ACNT_PRDT_CD": kis.account[9:11],
        "INQR_DVSN_1": "0",
        "INQR_DVSN_2": "0",
        "CTX_AREA_FK100": "",
        "CTX_AREA_NK100": "",
    }
    return kis.get("/uapi/domestic-stock/v1/trading/inquire-psbl-rvsecncl", params, "TTTC8036R")
```

## 완료 조건
- [x] test_domestic.py 시세 테스트 작성/통과
- [x] price(), orderbook(), daily() 구현
- [x] test_domestic.py 주문 테스트 작성/통과
- [x] buy(), sell(), cancel(), modify() 구현
- [x] test_domestic.py 계좌 테스트 작성/통과
- [x] balance(), positions(), orders(), pending_orders() 구현
- [ ] 모의투자에서 전체 플로우 테스트

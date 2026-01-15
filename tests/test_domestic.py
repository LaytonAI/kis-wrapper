import json
from pathlib import Path
from unittest.mock import patch

import pytest

from kis import domestic
from kis.client import APIError

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str):
    return json.loads((FIXTURES / name).read_text())


@pytest.fixture(autouse=True)
def mock_token():
    with patch("kis.client.get_token", return_value="test_token"):
        yield


# === 시세 조회 테스트 ===


def test_price_returns_required_fields(kis, httpx_mock):
    httpx_mock.add_response(json={"rt_cd": "0", "output": load_fixture("domestic_price.json")})

    result = domestic.price(kis, "005930")

    assert result["stck_prpr"] == "70000"
    assert result["prdy_vrss"] == "-1000"
    assert result["acml_vol"] == "12345678"


def test_price_with_invalid_symbol_raises_error(kis, httpx_mock):
    httpx_mock.add_response(json={"rt_cd": "1", "msg1": "종목코드 오류"})

    with pytest.raises(APIError, match="종목코드 오류"):
        domestic.price(kis, "INVALID")


def test_orderbook_returns_bid_ask(kis, httpx_mock):
    httpx_mock.add_response(json={"rt_cd": "0", "output": load_fixture("domestic_orderbook.json")})

    result = domestic.orderbook(kis, "005930")

    assert result["askp1"] == "70100"
    assert result["bidp1"] == "70000"


def test_daily_returns_list(kis, httpx_mock):
    httpx_mock.add_response(json={"rt_cd": "0", "output": load_fixture("domestic_daily.json")})

    result = domestic.daily(kis, "005930")

    assert len(result) == 2
    assert result[0]["stck_clpr"] == "70000"


def test_daily_returns_empty_list_on_non_list_output(kis, httpx_mock):
    httpx_mock.add_response(json={"rt_cd": "0", "output": {}})

    result = domestic.daily(kis, "005930")

    assert result == []


# === 주문 테스트 ===


def test_buy_market_order(kis, httpx_mock):
    httpx_mock.add_response(json={"rt_cd": "0", "output": load_fixture("domestic_order.json")})

    result = domestic.buy(kis, "005930", qty=10)

    body = json.loads(httpx_mock.get_request().content)
    assert body["ORD_DVSN"] == "01"  # 시장가
    assert body["ORD_QTY"] == "10"
    assert result["ODNO"] == "0000123456"


def test_buy_limit_order(kis, httpx_mock):
    httpx_mock.add_response(json={"rt_cd": "0", "output": load_fixture("domestic_order.json")})

    domestic.buy(kis, "005930", qty=10, price=70000)

    body = json.loads(httpx_mock.get_request().content)
    assert body["ORD_DVSN"] == "00"  # 지정가
    assert body["ORD_UNPR"] == "70000"


def test_sell_market_order(kis, httpx_mock):
    httpx_mock.add_response(json={"rt_cd": "0", "output": load_fixture("domestic_order.json")})

    domestic.sell(kis, "005930", qty=10)

    body = json.loads(httpx_mock.get_request().content)
    assert body["ORD_DVSN"] == "01"


def test_sell_limit_order(kis, httpx_mock):
    httpx_mock.add_response(json={"rt_cd": "0", "output": load_fixture("domestic_order.json")})

    domestic.sell(kis, "005930", qty=10, price=71000)

    body = json.loads(httpx_mock.get_request().content)
    assert body["ORD_DVSN"] == "00"
    assert body["ORD_UNPR"] == "71000"


def test_cancel_order(kis, httpx_mock):
    httpx_mock.add_response(json={"rt_cd": "0", "output": load_fixture("domestic_order.json")})

    domestic.cancel(kis, "0000123456", qty=10)

    body = json.loads(httpx_mock.get_request().content)
    assert body["ORGN_ODNO"] == "0000123456"
    assert body["RVSE_CNCL_DVSN_CD"] == "02"  # 취소


def test_modify_order(kis, httpx_mock):
    httpx_mock.add_response(json={"rt_cd": "0", "output": load_fixture("domestic_order.json")})

    domestic.modify(kis, "0000123456", qty=5, price=69000)

    body = json.loads(httpx_mock.get_request().content)
    assert body["ORGN_ODNO"] == "0000123456"
    assert body["RVSE_CNCL_DVSN_CD"] == "01"  # 정정
    assert body["ORD_QTY"] == "5"
    assert body["ORD_UNPR"] == "69000"


def test_buy_uses_paper_tr_id(kis, httpx_mock):
    httpx_mock.add_response(json={"rt_cd": "0", "output": load_fixture("domestic_order.json")})

    domestic.buy(kis, "005930", qty=10)

    assert httpx_mock.get_request().headers["tr_id"] == "VTTC0802U"  # 모의투자


def test_sell_uses_paper_tr_id(kis, httpx_mock):
    httpx_mock.add_response(json={"rt_cd": "0", "output": load_fixture("domestic_order.json")})

    domestic.sell(kis, "005930", qty=10)

    assert httpx_mock.get_request().headers["tr_id"] == "VTTC0801U"


# === 계좌 조회 테스트 ===


def test_balance_returns_account_info(kis, httpx_mock):
    httpx_mock.add_response(json={"rt_cd": "0", "output": load_fixture("domestic_balance.json")})

    result = domestic.balance(kis)

    assert "output1" in result
    assert "output2" in result


def test_positions_returns_holdings(kis, httpx_mock):
    httpx_mock.add_response(json={"rt_cd": "0", "output": load_fixture("domestic_balance.json")})

    result = domestic.positions(kis)

    assert len(result) == 1
    assert result[0]["pdno"] == "005930"
    assert result[0]["hldg_qty"] == "100"


def test_positions_returns_empty_on_no_holdings(kis, httpx_mock):
    httpx_mock.add_response(json={"rt_cd": "0", "output": {"output1": [], "output2": []}})

    result = domestic.positions(kis)

    assert result == []


def test_orders_returns_order_history(kis, httpx_mock):
    httpx_mock.add_response(json={"rt_cd": "0", "output": load_fixture("domestic_orders.json")})

    result = domestic.orders(kis)

    assert len(result) == 1
    assert result[0]["odno"] == "0000123456"


def test_pending_orders_returns_unfilled(kis, httpx_mock):
    httpx_mock.add_response(json={"rt_cd": "0", "output": load_fixture("domestic_pending.json")})

    result = domestic.pending_orders(kis)

    assert len(result) == 1
    assert result[0]["psbl_qty"] == "20"


def test_balance_uses_paper_tr_id(kis, httpx_mock):
    httpx_mock.add_response(json={"rt_cd": "0", "output": load_fixture("domestic_balance.json")})

    domestic.balance(kis)

    assert httpx_mock.get_request().headers["tr_id"] == "VTTC8434R"

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from kis import overseas
from kis.client import APIError

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str):
    return json.loads((FIXTURES / name).read_text())


@pytest.fixture(autouse=True)
def mock_token():
    with patch("kis.client.get_token", return_value="test_token"):
        yield


# === TR ID 매핑 테스트 ===


def test_buy_tr_id_for_nasdaq():
    assert overseas._tr_id("buy", "NAS", False) == "JTTT1002U"
    assert overseas._tr_id("buy", "NAS", True) == "JTTT1002U"  # 미국은 동일


def test_buy_tr_id_for_hongkong():
    assert overseas._tr_id("buy", "HKS", False) == "TTTS1002U"
    assert overseas._tr_id("buy", "HKS", True) == "VTTS1002U"  # 모의투자


def test_sell_tr_id_for_nasdaq():
    assert overseas._tr_id("sell", "NAS", False) == "JTTT1006U"
    assert overseas._tr_id("sell", "NAS", True) == "JTTT1006U"


def test_sell_tr_id_for_tokyo():
    assert overseas._tr_id("sell", "TSE", False) == "TTTS0307U"
    assert overseas._tr_id("sell", "TSE", True) == "VTTS0307U"


# === 시세 조회 테스트 ===


def test_price_returns_required_fields(kis, httpx_mock):
    httpx_mock.add_response(json={"rt_cd": "0", "output": load_fixture("overseas_price.json")})

    result = overseas.price(kis, "AAPL", "NAS")

    assert result["last"] == "150.25"
    assert result["diff"] == "2.50"
    assert result["rate"] == "1.69"


def test_price_sends_correct_params(kis, httpx_mock):
    httpx_mock.add_response(json={"rt_cd": "0", "output": load_fixture("overseas_price.json")})

    overseas.price(kis, "TSLA", "NAS")

    request = httpx_mock.get_request()
    assert "SYMB=TSLA" in str(request.url)
    assert "EXCD=NAS" in str(request.url)


def test_price_with_invalid_symbol_raises_error(kis, httpx_mock):
    httpx_mock.add_response(json={"rt_cd": "1", "msg1": "종목코드 오류"})

    with pytest.raises(APIError, match="종목코드 오류"):
        overseas.price(kis, "INVALID", "NAS")


def test_daily_returns_list(kis, httpx_mock):
    httpx_mock.add_response(json={"rt_cd": "0", "output": load_fixture("overseas_daily.json")})

    result = overseas.daily(kis, "AAPL", "NAS")

    assert len(result) == 2
    assert result[0]["clos"] == "150.25"


def test_daily_returns_empty_list_on_non_list_output(kis, httpx_mock):
    httpx_mock.add_response(json={"rt_cd": "0", "output": {}})

    result = overseas.daily(kis, "AAPL", "NAS")

    assert result == []


# === 주문 테스트 ===


def test_buy_market_order(kis, httpx_mock):
    httpx_mock.add_response(json={"rt_cd": "0", "output": load_fixture("overseas_order.json")})

    result = overseas.buy(kis, "AAPL", "NAS", qty=10)

    body = json.loads(httpx_mock.get_request().content)
    assert body["ORD_DVSN"] == "01"  # 시장가
    assert body["ORD_QTY"] == "10"
    assert body["OVRS_ORD_UNPR"] == "0"
    assert result["ODNO"] == "0000123456"


def test_buy_limit_order(kis, httpx_mock):
    httpx_mock.add_response(json={"rt_cd": "0", "output": load_fixture("overseas_order.json")})

    overseas.buy(kis, "AAPL", "NAS", qty=10, price=150.0)

    body = json.loads(httpx_mock.get_request().content)
    assert body["ORD_DVSN"] == "00"  # 지정가
    assert body["OVRS_ORD_UNPR"] == "150.0"


def test_buy_sends_exchange_code(kis, httpx_mock):
    httpx_mock.add_response(json={"rt_cd": "0", "output": load_fixture("overseas_order.json")})

    overseas.buy(kis, "AAPL", "NAS", qty=1, price=150.0)

    body = json.loads(httpx_mock.get_request().content)
    assert body["OVRS_EXCG_CD"] == "NAS"
    assert body["PDNO"] == "AAPL"


def test_sell_market_order(kis, httpx_mock):
    httpx_mock.add_response(json={"rt_cd": "0", "output": load_fixture("overseas_order.json")})

    overseas.sell(kis, "AAPL", "NAS", qty=10)

    body = json.loads(httpx_mock.get_request().content)
    assert body["ORD_DVSN"] == "01"
    assert body["SLL_TYPE"] == "00"


def test_sell_limit_order(kis, httpx_mock):
    httpx_mock.add_response(json={"rt_cd": "0", "output": load_fixture("overseas_order.json")})

    overseas.sell(kis, "AAPL", "NAS", qty=10, price=155.0)

    body = json.loads(httpx_mock.get_request().content)
    assert body["ORD_DVSN"] == "00"
    assert body["OVRS_ORD_UNPR"] == "155.0"


def test_cancel_order(kis, httpx_mock):
    httpx_mock.add_response(json={"rt_cd": "0", "output": load_fixture("overseas_order.json")})

    overseas.cancel(kis, "NAS", "0000123456", qty=10)

    body = json.loads(httpx_mock.get_request().content)
    assert body["ORGN_ODNO"] == "0000123456"
    assert body["RVSE_CNCL_DVSN_CD"] == "02"
    assert body["ORD_QTY"] == "10"


# === 계좌 조회 테스트 ===


def test_balance_returns_holdings(kis, httpx_mock):
    httpx_mock.add_response(json={"rt_cd": "0", "output": load_fixture("overseas_balance.json")})

    result = overseas.balance(kis)

    assert "output1" in result
    assert len(result["output1"]) == 1
    assert result["output1"][0]["ovrs_pdno"] == "AAPL"


def test_balance_with_exchange_filter(kis, httpx_mock):
    httpx_mock.add_response(json={"rt_cd": "0", "output": load_fixture("overseas_balance.json")})

    overseas.balance(kis, exchange="NAS")

    request = httpx_mock.get_request()
    assert "OVRS_EXCG_CD=NAS" in str(request.url)


def test_balance_uses_paper_tr_id(kis, httpx_mock):
    httpx_mock.add_response(json={"rt_cd": "0", "output": load_fixture("overseas_balance.json")})

    overseas.balance(kis)

    assert httpx_mock.get_request().headers["tr_id"] == "VTTS3012R"


def test_exchange_rate_returns_rate(kis, httpx_mock):
    httpx_mock.add_response(json={"rt_cd": "0", "output": load_fixture("overseas_exchange_rate.json")})

    result = overseas.exchange_rate(kis)

    assert "output2" in result
    assert result["output2"][0]["crcy_cd"] == "USD"
    assert result["output2"][0]["exrt"] == "1350.00"


def test_exchange_rate_uses_paper_tr_id(kis, httpx_mock):
    httpx_mock.add_response(json={"rt_cd": "0", "output": load_fixture("overseas_exchange_rate.json")})

    overseas.exchange_rate(kis)

    assert httpx_mock.get_request().headers["tr_id"] == "VTRP6504R"

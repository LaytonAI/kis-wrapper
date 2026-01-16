import json
from pathlib import Path
from unittest.mock import patch

import pytest

from kis import overseas
from kis.errors import KISError

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str):
    return json.loads((FIXTURES / name).read_text())


@pytest.fixture(autouse=True)
def mock_token():
    with patch("kis.client.get_token", return_value="test_token"):
        yield


# === TR ID 매핑 테스트 ===


def test_buy_tr_id_for_nasdaq():
    assert overseas._tr("buy", "NAS", False) == "JTTT1002U"
    assert overseas._tr("buy", "NAS", True) == "JTTT1002U"  # 미국은 동일


def test_buy_tr_id_for_hongkong():
    assert overseas._tr("buy", "HKS", False) == "TTTS1002U"
    assert overseas._tr("buy", "HKS", True) == "VTTS1002U"  # 모의투자


def test_sell_tr_id_for_nasdaq():
    assert overseas._tr("sell", "NAS", False) == "JTTT1006U"
    assert overseas._tr("sell", "NAS", True) == "JTTT1006U"


def test_sell_tr_id_for_tokyo():
    assert overseas._tr("sell", "TSE", False) == "TTTS0307U"
    assert overseas._tr("sell", "TSE", True) == "VTTS0307U"


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
    httpx_mock.add_response(json={"rt_cd": "1", "msg_cd": "APBK0013", "msg1": "종목코드 오류"})

    with pytest.raises(KISError, match="종목코드 오류"):
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


# === 호가 조회 테스트 ===


def test_orderbook_returns_data(kis, httpx_mock):
    httpx_mock.add_response(json={"rt_cd": "0", "output": {"askp1": "150.30", "bidp1": "150.20"}})

    result = overseas.orderbook(kis, "AAPL", "NAS")

    assert result["askp1"] == "150.30"
    request = httpx_mock.get_request()
    assert "SYMB=AAPL" in str(request.url)
    assert request.headers["tr_id"] == "HHDFS76200200"


# === 주문 정정 테스트 ===


def test_modify_order(kis, httpx_mock):
    httpx_mock.add_response(json={"rt_cd": "0", "output": load_fixture("overseas_order.json")})

    overseas.modify(kis, "NAS", "0000123456", qty=5, price=160.0)

    body = json.loads(httpx_mock.get_request().content)
    assert body["ORGN_ODNO"] == "0000123456"
    assert body["RVSE_CNCL_DVSN_CD"] == "01"  # 정정
    assert body["ORD_QTY"] == "5"
    assert body["OVRS_ORD_UNPR"] == "160.0"


def test_modify_uses_paper_tr_id(kis, httpx_mock):
    httpx_mock.add_response(json={"rt_cd": "0", "output": load_fixture("overseas_order.json")})

    overseas.modify(kis, "NAS", "0000123456", qty=5, price=160.0)

    assert httpx_mock.get_request().headers["tr_id"] == "VTTT1004U"


# === 체결내역/미체결 테스트 ===


def test_orders_returns_list(kis, httpx_mock):
    httpx_mock.add_response(json={"rt_cd": "0", "output": [{"odno": "123"}, {"odno": "456"}]})

    result = overseas.orders(kis)

    assert len(result) == 2
    assert httpx_mock.get_request().headers["tr_id"] == "VTTS3035R"


def test_orders_returns_empty_on_dict_output(kis, httpx_mock):
    httpx_mock.add_response(json={"rt_cd": "0", "output": {"output": []}})

    result = overseas.orders(kis)

    assert result == []


def test_pending_orders_returns_list(kis, httpx_mock):
    httpx_mock.add_response(json={"rt_cd": "0", "output": [{"odno": "789"}]})

    result = overseas.pending_orders(kis, exchange="NAS")

    assert len(result) == 1
    assert httpx_mock.get_request().headers["tr_id"] == "VTTS3018R"


# === 포지션 관리 테스트 ===


def test_positions_returns_list(kis, httpx_mock):
    httpx_mock.add_response(json={"rt_cd": "0", "output": load_fixture("overseas_balance.json")})

    result = overseas.positions(kis)

    assert len(result) == 1
    assert result[0]["ovrs_pdno"] == "AAPL"


def test_position_returns_matching(kis, httpx_mock):
    httpx_mock.add_response(json={"rt_cd": "0", "output": load_fixture("overseas_balance.json")})

    result = overseas.position(kis, "AAPL", "NAS")

    assert result["ovrs_pdno"] == "AAPL"


def test_position_returns_none_for_no_match(kis, httpx_mock):
    httpx_mock.add_response(json={"rt_cd": "0", "output": load_fixture("overseas_balance.json")})

    result = overseas.position(kis, "TSLA", "NAS")

    assert result is None


def test_sell_all_sells_full_qty(kis, httpx_mock):
    httpx_mock.add_response(json={"rt_cd": "0", "output": load_fixture("overseas_balance.json")})
    httpx_mock.add_response(json={"rt_cd": "0", "output": load_fixture("overseas_order.json")})

    result = overseas.sell_all(kis, "AAPL", "NAS")

    assert result is not None
    body = json.loads(httpx_mock.get_requests()[-1].content)
    assert body["ORD_QTY"] == "10"  # from fixture: ovrs_cblc_qty


def test_sell_all_returns_none_if_no_position(kis, httpx_mock):
    httpx_mock.add_response(json={"rt_cd": "0", "output": load_fixture("overseas_balance.json")})

    result = overseas.sell_all(kis, "TSLA", "NAS")

    assert result is None

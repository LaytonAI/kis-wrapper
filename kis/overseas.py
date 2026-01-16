"""해외주식 API"""

from kis.client import KIS
from kis.types import Exchange


_TR_IDS = {
    "buy": {
        "NAS": "JTTT1002U",
        "NYS": "JTTT1002U",
        "AMS": "JTTT1002U",
        "HKS": "TTTS1002U",
        "SHS": "TTTS0202U",
        "SZS": "TTTS0305U",
        "TSE": "TTTS0308U",
        "HNX": "TTTS0311U",
        "HSX": "TTTS0311U",
    },
    "sell": {
        "NAS": "JTTT1006U",
        "NYS": "JTTT1006U",
        "AMS": "JTTT1006U",
        "HKS": "TTTS1001U",
        "SHS": "TTTS1005U",
        "SZS": "TTTS0304U",
        "TSE": "TTTS0307U",
        "HNX": "TTTS0310U",
        "HSX": "TTTS0310U",
    },
}


def _tr_id(side: str, exchange: str, is_paper: bool) -> str:
    default = "JTTT1002U" if side == "buy" else "JTTT1006U"
    tr = _TR_IDS[side].get(exchange, default)
    return "VT" + tr[2:] if is_paper and tr.startswith("TT") else tr


# === 시세 조회 ===


def price(kis: KIS, symbol: str, exchange: Exchange) -> dict:
    """해외주식 현재가 조회"""
    return kis.get(
        "/uapi/overseas-price/v1/quotations/price",
        {"AUTH": "", "EXCD": exchange, "SYMB": symbol},
        "HHDFS00000300",
    )


def daily(kis: KIS, symbol: str, exchange: Exchange, period: str = "D", count: int = 30) -> list:
    """해외주식 기간별 시세 (period: D=일, W=주, M=월)"""
    result = kis.get(
        "/uapi/overseas-price/v1/quotations/dailyprice",
        {
            "AUTH": "",
            "EXCD": exchange,
            "SYMB": symbol,
            "GUBN": {"D": "0", "W": "1", "M": "2"}.get(period, "0"),
            "BYMD": "",
            "MODP": "1",
        },
        "HHDFS76240000",
    )
    return result if isinstance(result, list) else []


# === 주문 ===


def _order(
    kis: KIS, side: str, symbol: str, exchange: Exchange, qty: int, price: float | None
) -> dict:
    body = {
        **kis.account_params,
        "OVRS_EXCG_CD": exchange,
        "PDNO": symbol,
        "ORD_QTY": str(qty),
        "OVRS_ORD_UNPR": str(price or 0),
        "ORD_SVR_DVSN_CD": "0",
        "ORD_DVSN": "00" if price else "01",
    }
    if side == "sell":
        body["SLL_TYPE"] = "00"
    return kis.post(
        "/uapi/overseas-stock/v1/trading/order", body, _tr_id(side, exchange, kis.is_paper)
    )


def buy(kis: KIS, symbol: str, exchange: Exchange, qty: int, price: float | None = None) -> dict:
    """해외주식 매수 (price=None이면 시장가, 미국만 지원)"""
    return _order(kis, "buy", symbol, exchange, qty, price)


def sell(kis: KIS, symbol: str, exchange: Exchange, qty: int, price: float | None = None) -> dict:
    """해외주식 매도 (price=None이면 시장가, 미국만 지원)"""
    return _order(kis, "sell", symbol, exchange, qty, price)


def cancel(kis: KIS, exchange: Exchange, order_no: str, qty: int) -> dict:
    """해외주식 주문 취소"""
    body = {
        **kis.account_params,
        "OVRS_EXCG_CD": exchange,
        "ORGN_ODNO": order_no,
        "RVSE_CNCL_DVSN_CD": "02",
        "ORD_QTY": str(qty),
        "OVRS_ORD_UNPR": "0",
    }
    return kis.post("/uapi/overseas-stock/v1/trading/order-rvsecncl", body, "TTTT1004U")


# === 계좌 조회 ===


def balance(kis: KIS, exchange: Exchange | None = None) -> dict:
    """해외주식 잔고 조회 (exchange=None이면 전체)"""
    params = {
        **kis.account_params,
        "OVRS_EXCG_CD": exchange or "",
        "TR_CRCY_CD": "",
        "CTX_AREA_FK200": "",
        "CTX_AREA_NK200": "",
    }
    tr_id = "VTTS3012R" if kis.is_paper else "TTTS3012R"
    return kis.get("/uapi/overseas-stock/v1/trading/inquire-balance", params, tr_id)


def exchange_rate(kis: KIS) -> dict:
    """환율 조회"""
    params = {**kis.account_params}
    tr_id = "VTRP6504R" if kis.is_paper else "CTRP6504R"
    return kis.get("/uapi/overseas-stock/v1/trading/inquire-present-balance", params, tr_id)


def orderbook(kis: KIS, symbol: str, exchange: Exchange) -> dict:
    """해외주식 호가 조회"""
    return kis.get(
        "/uapi/overseas-price/v1/quotations/inquire-asking-price",
        {"AUTH": "", "EXCD": exchange, "SYMB": symbol},
        "HHDFS76200200",
    )


def modify(kis: KIS, exchange: Exchange, order_no: str, qty: int, price: float) -> dict:
    """해외주식 주문 정정"""
    body = {
        **kis.account_params,
        "OVRS_EXCG_CD": exchange,
        "ORGN_ODNO": order_no,
        "RVSE_CNCL_DVSN_CD": "01",  # 정정
        "ORD_QTY": str(qty),
        "OVRS_ORD_UNPR": str(price),
    }
    tr_id = "VTTT1004U" if kis.is_paper else "TTTT1004U"
    return kis.post("/uapi/overseas-stock/v1/trading/order-rvsecncl", body, tr_id)


def orders(kis: KIS, exchange: Exchange | None = None) -> list:
    """해외주식 체결내역 조회"""
    params = {
        **kis.account_params,
        "OVRS_EXCG_CD": exchange or "",
        "SORT_SQN": "DS",
        "CTX_AREA_FK200": "",
        "CTX_AREA_NK200": "",
    }
    tr_id = "VTTS3035R" if kis.is_paper else "TTTS3035R"
    result = kis.get("/uapi/overseas-stock/v1/trading/inquire-ccnl", params, tr_id)
    return result if isinstance(result, list) else result.get("output", [])


def pending_orders(kis: KIS, exchange: Exchange | None = None) -> list:
    """해외주식 미체결 조회"""
    params = {
        **kis.account_params,
        "OVRS_EXCG_CD": exchange or "",
        "SORT_SQN": "DS",
        "CTX_AREA_FK200": "",
        "CTX_AREA_NK200": "",
    }
    tr_id = "VTTS3018R" if kis.is_paper else "TTTS3018R"
    result = kis.get("/uapi/overseas-stock/v1/trading/inquire-nccs", params, tr_id)
    return result if isinstance(result, list) else result.get("output", [])


# === 포지션 관리 ===


def positions(kis: KIS, exchange: Exchange | None = None) -> list:
    """보유종목 리스트"""
    result = balance(kis, exchange)
    return result.get("output1", []) if isinstance(result, dict) else []


def position(kis: KIS, symbol: str, exchange: Exchange) -> dict | None:
    """특정 종목 포지션"""
    for p in positions(kis, exchange):
        if p.get("ovrs_pdno") == symbol:
            return p
    return None


def sell_all(kis: KIS, symbol: str, exchange: Exchange) -> dict | None:
    """전량 매도"""
    pos = position(kis, symbol, exchange)
    if not pos: return None
    qty = int(pos.get("ovrs_cblc_qty", 0))
    if qty <= 0: return None
    return sell(kis, symbol, exchange, qty)

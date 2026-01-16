from kis.client import KIS
from kis.types import Exchange
from kis.utils import ensure_list

_TR_BUY = {
    "NAS": "JTTT1002U",
    "NYS": "JTTT1002U",
    "AMS": "JTTT1002U",
    "HKS": "TTTS1002U",
    "SHS": "TTTS0202U",
    "SZS": "TTTS0305U",
    "TSE": "TTTS0308U",
    "HNX": "TTTS0311U",
    "HSX": "TTTS0311U",
}
_TR_SELL = {
    "NAS": "JTTT1006U",
    "NYS": "JTTT1006U",
    "AMS": "JTTT1006U",
    "HKS": "TTTS1001U",
    "SHS": "TTTS1005U",
    "SZS": "TTTS0304U",
    "TSE": "TTTS0307U",
    "HNX": "TTTS0310U",
    "HSX": "TTTS0310U",
}


def _tr(side: str, exchange: str, is_paper: bool) -> str:
    trs = _TR_BUY if side == "buy" else _TR_SELL
    tr = trs.get(exchange, "JTTT1002U" if side == "buy" else "JTTT1006U")
    return "VT" + tr[2:] if is_paper and tr.startswith("TT") else tr


def _rvsecncl(
    kis: KIS, exchange: Exchange, order_no: str, qty: int, price: float, dvsn: str, tr: str
) -> dict:
    return kis.post(
        "/uapi/overseas-stock/v1/trading/order-rvsecncl",
        {
            **kis.account_params,
            "OVRS_EXCG_CD": exchange,
            "ORGN_ODNO": order_no,
            "RVSE_CNCL_DVSN_CD": dvsn,
            "ORD_QTY": str(qty),
            "OVRS_ORD_UNPR": str(price),
        },
        tr,
    )


def _output_list(result: object) -> list:
    return ensure_list(result) or ensure_list(result, "output")


def price(kis: KIS, symbol: str, exchange: Exchange) -> dict:
    return kis.get(
        "/uapi/overseas-price/v1/quotations/price",
        {"AUTH": "", "EXCD": exchange, "SYMB": symbol},
        "HHDFS00000300",
    )


def daily(kis: KIS, symbol: str, exchange: Exchange, period: str = "D", count: int = 30) -> list:
    return ensure_list(
        kis.get(
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
    )


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
        "/uapi/overseas-stock/v1/trading/order", body, _tr(side, exchange, kis.is_paper)
    )


def buy(kis: KIS, symbol: str, exchange: Exchange, qty: int, price: float | None = None) -> dict:
    return _order(kis, "buy", symbol, exchange, qty, price)


def sell(kis: KIS, symbol: str, exchange: Exchange, qty: int, price: float | None = None) -> dict:
    return _order(kis, "sell", symbol, exchange, qty, price)


def cancel(kis: KIS, exchange: Exchange, order_no: str, qty: int) -> dict:
    return _rvsecncl(kis, exchange, order_no, qty, 0, "02", "TTTT1004U")


def balance(kis: KIS, exchange: Exchange | None = None) -> dict:
    return kis.get(
        "/uapi/overseas-stock/v1/trading/inquire-balance",
        {
            **kis.account_params,
            "OVRS_EXCG_CD": exchange or "",
            "TR_CRCY_CD": "",
            "CTX_AREA_FK200": "",
            "CTX_AREA_NK200": "",
        },
        "VTTS3012R" if kis.is_paper else "TTTS3012R",
    )


def exchange_rate(kis: KIS) -> dict:
    return kis.get(
        "/uapi/overseas-stock/v1/trading/inquire-present-balance",
        {**kis.account_params},
        "VTRP6504R" if kis.is_paper else "CTRP6504R",
    )


def orderbook(kis: KIS, symbol: str, exchange: Exchange) -> dict:
    return kis.get(
        "/uapi/overseas-price/v1/quotations/inquire-asking-price",
        {"AUTH": "", "EXCD": exchange, "SYMB": symbol},
        "HHDFS76200200",
    )


def modify(kis: KIS, exchange: Exchange, order_no: str, qty: int, price: float) -> dict:
    return _rvsecncl(
        kis, exchange, order_no, qty, price, "01", "VTTT1004U" if kis.is_paper else "TTTT1004U"
    )


def orders(kis: KIS, exchange: Exchange | None = None) -> list:
    return _output_list(
        kis.get(
            "/uapi/overseas-stock/v1/trading/inquire-ccnl",
            {
                **kis.account_params,
                "OVRS_EXCG_CD": exchange or "",
                "SORT_SQN": "DS",
                "CTX_AREA_FK200": "",
                "CTX_AREA_NK200": "",
            },
            "VTTS3035R" if kis.is_paper else "TTTS3035R",
        )
    )


def pending_orders(kis: KIS, exchange: Exchange | None = None) -> list:
    return _output_list(
        kis.get(
            "/uapi/overseas-stock/v1/trading/inquire-nccs",
            {
                **kis.account_params,
                "OVRS_EXCG_CD": exchange or "",
                "SORT_SQN": "DS",
                "CTX_AREA_FK200": "",
                "CTX_AREA_NK200": "",
            },
            "VTTS3018R" if kis.is_paper else "TTTS3018R",
        )
    )


def positions(kis: KIS, exchange: Exchange | None = None) -> list:
    return ensure_list(balance(kis, exchange), "output1")


def position(kis: KIS, symbol: str, exchange: Exchange) -> dict | None:
    return next((p for p in positions(kis, exchange) if p.get("ovrs_pdno") == symbol), None)


def sell_all(kis: KIS, symbol: str, exchange: Exchange) -> dict | None:
    pos = position(kis, symbol, exchange)
    if not pos or (qty := int(pos.get("ovrs_cblc_qty", 0))) <= 0:
        return None
    return sell(kis, symbol, exchange, qty)

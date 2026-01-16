from datetime import date

from kis.client import KIS
from kis.utils import ensure_list


def _tr(kis: KIS, paper: str, real: str) -> str:
    return paper if kis.is_paper else real


def price(kis: KIS, symbol: str) -> dict:
    return kis.get(
        "/uapi/domestic-stock/v1/quotations/inquire-price",
        {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": symbol},
        "FHKST01010100",
    )


def orderbook(kis: KIS, symbol: str) -> dict:
    return kis.get(
        "/uapi/domestic-stock/v1/quotations/inquire-asking-price-exp-ccn",
        {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": symbol},
        "FHKST01010200",
    )


def daily(kis: KIS, symbol: str, period: str = "D") -> list[dict]:
    return ensure_list(
        kis.get(
            "/uapi/domestic-stock/v1/quotations/inquire-daily-price",
            {
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": symbol,
                "FID_PERIOD_DIV_CODE": period,
                "FID_ORG_ADJ_PRC": "0",
            },
            "FHKST01010400",
        )
    )


def _order(kis: KIS, symbol: str, qty: int, price: int | None, tr_paper: str, tr_real: str) -> dict:
    return kis.post(
        "/uapi/domestic-stock/v1/trading/order-cash",
        {
            **kis.account_params,
            "PDNO": symbol,
            "ORD_DVSN": "01" if price is None else "00",
            "ORD_QTY": str(qty),
            "ORD_UNPR": str(price or 0),
        },
        _tr(kis, tr_paper, tr_real),
    )


def buy(kis: KIS, symbol: str, qty: int, price: int | None = None) -> dict:
    return _order(kis, symbol, qty, price, "VTTC0802U", "TTTC0802U")


def sell(kis: KIS, symbol: str, qty: int, price: int | None = None) -> dict:
    return _order(kis, symbol, qty, price, "VTTC0801U", "TTTC0801U")


def _rvsecncl(
    kis: KIS, order_no: str, qty: int, price: int, dvsn: str, all_qty: bool = False
) -> dict:
    return kis.post(
        "/uapi/domestic-stock/v1/trading/order-rvsecncl",
        {
            **kis.account_params,
            "KRX_FWDG_ORD_ORGNO": "",
            "ORGN_ODNO": order_no,
            "ORD_DVSN": "00",
            "RVSE_CNCL_DVSN_CD": dvsn,
            "ORD_QTY": "0" if all_qty else str(qty),
            "ORD_UNPR": "0" if all_qty else str(price),
            "QTY_ALL_ORD_YN": "Y" if all_qty else "N",
        },
        _tr(kis, "VTTC0803U", "TTTC0803U"),
    )


def cancel(kis: KIS, order_no: str, qty: int) -> dict:
    return _rvsecncl(kis, order_no, qty, 0, "02")


def modify(kis: KIS, order_no: str, qty: int, price: int) -> dict:
    return _rvsecncl(kis, order_no, qty, price, "01")


def balance(kis: KIS) -> dict:
    return kis.get(
        "/uapi/domestic-stock/v1/trading/inquire-balance",
        {
            **kis.account_params,
            "AFHR_FLPR_YN": "N",
            "OFL_YN": "",
            "INQR_DVSN": "02",
            "UNPR_DVSN": "01",
            "FUND_STTL_ICLD_YN": "N",
            "FNCG_AMT_AUTO_RDPT_YN": "N",
            "PRCS_DVSN": "00",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": "",
        },
        _tr(kis, "VTTC8434R", "TTTC8434R"),
    )


def positions(kis: KIS) -> list[dict]:
    return ensure_list(balance(kis), "output1")


def orders(kis: KIS, start_date: str = "", end_date: str = "") -> list[dict]:
    today = date.today().strftime("%Y%m%d")
    return ensure_list(
        kis.get(
            "/uapi/domestic-stock/v1/trading/inquire-daily-ccld",
            {
                **kis.account_params,
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
            },
            _tr(kis, "VTTC8001R", "TTTC8001R"),
        )
    )


def pending_orders(kis: KIS) -> list[dict]:
    return ensure_list(
        kis.get(
            "/uapi/domestic-stock/v1/trading/inquire-psbl-rvsecncl",
            {
                **kis.account_params,
                "INQR_DVSN_1": "0",
                "INQR_DVSN_2": "0",
                "CTX_AREA_FK100": "",
                "CTX_AREA_NK100": "",
            },
            _tr(kis, "VTTC8036R", "TTTC8036R"),
        )
    )


def position(kis: KIS, symbol: str) -> dict | None:
    p = next((p for p in positions(kis) if p["pdno"] == symbol), None)
    if not p:
        return None
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


def sell_all(kis: KIS, symbol: str) -> dict:
    p = position(kis, symbol)
    if not p or p["qty"] == 0:
        raise ValueError(f"No position for {symbol}")
    return sell(kis, symbol, qty=p["qty"])


def cancel_remaining(kis: KIS, order_no: str) -> dict:
    return _rvsecncl(kis, order_no, 0, 0, "02", all_qty=True)

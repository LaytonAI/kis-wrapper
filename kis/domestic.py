"""국내주식 API"""

from datetime import date

from kis.client import KIS


def _tr_id(kis: KIS, paper: str, real: str) -> str:
    return paper if kis.is_paper else real


def _account_params(kis: KIS) -> dict:
    return {"CANO": kis.account[:8], "ACNT_PRDT_CD": kis.account[9:11]}


# === 시세 조회 ===


def price(kis: KIS, symbol: str) -> dict:
    """현재가 조회"""
    return kis.get(
        "/uapi/domestic-stock/v1/quotations/inquire-price",
        {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": symbol},
        "FHKST01010100",
    )


def orderbook(kis: KIS, symbol: str) -> dict:
    """호가 조회"""
    return kis.get(
        "/uapi/domestic-stock/v1/quotations/inquire-asking-price-exp-ccn",
        {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": symbol},
        "FHKST01010200",
    )


def daily(kis: KIS, symbol: str, period: str = "D") -> list[dict]:
    """일/주/월봉 조회 (period: D=일, W=주, M=월)"""
    result = kis.get(
        "/uapi/domestic-stock/v1/quotations/inquire-daily-price",
        {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": symbol,
            "FID_PERIOD_DIV_CODE": period,
            "FID_ORG_ADJ_PRC": "0",
        },
        "FHKST01010400",
    )
    return result if isinstance(result, list) else []


# === 주문 ===


def _order(kis: KIS, symbol: str, qty: int, price: int | None, tr_paper: str, tr_real: str) -> dict:
    """공통 주문 처리"""
    return kis.post(
        "/uapi/domestic-stock/v1/trading/order-cash",
        {
            **_account_params(kis),
            "PDNO": symbol,
            "ORD_DVSN": "01" if price is None else "00",
            "ORD_QTY": str(qty),
            "ORD_UNPR": str(price or 0),
        },
        _tr_id(kis, tr_paper, tr_real),
    )


def buy(kis: KIS, symbol: str, qty: int, price: int | None = None) -> dict:
    """매수 주문 (price=None이면 시장가)"""
    return _order(kis, symbol, qty, price, "VTTC0802U", "TTTC0802U")


def sell(kis: KIS, symbol: str, qty: int, price: int | None = None) -> dict:
    """매도 주문 (price=None이면 시장가)"""
    return _order(kis, symbol, qty, price, "VTTC0801U", "TTTC0801U")


def _revise_cancel(kis: KIS, order_no: str, qty: int, price: int, dvsn_cd: str) -> dict:
    """공통 정정/취소 처리"""
    return kis.post(
        "/uapi/domestic-stock/v1/trading/order-rvsecncl",
        {
            **_account_params(kis),
            "KRX_FWDG_ORD_ORGNO": "",
            "ORGN_ODNO": order_no,
            "ORD_DVSN": "00",
            "RVSE_CNCL_DVSN_CD": dvsn_cd,
            "ORD_QTY": str(qty),
            "ORD_UNPR": str(price),
            "QTY_ALL_ORD_YN": "N",
        },
        _tr_id(kis, "VTTC0803U", "TTTC0803U"),
    )


def cancel(kis: KIS, order_no: str, qty: int) -> dict:
    """주문 취소"""
    return _revise_cancel(kis, order_no, qty, 0, "02")


def modify(kis: KIS, order_no: str, qty: int, price: int) -> dict:
    """주문 정정"""
    return _revise_cancel(kis, order_no, qty, price, "01")


# === 계좌 조회 ===


def balance(kis: KIS) -> dict:
    """잔고 조회 (예수금 + 보유종목)"""
    return kis.get(
        "/uapi/domestic-stock/v1/trading/inquire-balance",
        {
            **_account_params(kis),
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
        _tr_id(kis, "VTTC8434R", "TTTC8434R"),
    )


def positions(kis: KIS) -> list[dict]:
    """보유종목 조회"""
    result = balance(kis)
    return result.get("output1", []) if isinstance(result, dict) else []


def orders(kis: KIS, start_date: str = "", end_date: str = "") -> list[dict]:
    """주문내역 조회"""
    today = date.today().strftime("%Y%m%d")
    result = kis.get(
        "/uapi/domestic-stock/v1/trading/inquire-daily-ccld",
        {
            **_account_params(kis),
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
        _tr_id(kis, "VTTC8001R", "TTTC8001R"),
    )
    return result if isinstance(result, list) else []


def pending_orders(kis: KIS) -> list[dict]:
    """미체결 주문 조회"""
    result = kis.get(
        "/uapi/domestic-stock/v1/trading/inquire-psbl-rvsecncl",
        {
            **_account_params(kis),
            "INQR_DVSN_1": "0",
            "INQR_DVSN_2": "0",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": "",
        },
        _tr_id(kis, "VTTC8036R", "TTTC8036R"),
    )
    return result if isinstance(result, list) else []


# === 포지션 관리 ===


def position(kis: KIS, symbol: str) -> dict | None:
    """종목별 포지션 조회 (미보유 시 None)"""
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
    """종목 전량 매도 (시장가)"""
    p = next((p for p in positions(kis) if p["pdno"] == symbol), None)
    if not p or int(p["hldg_qty"]) == 0:
        raise ValueError(f"No position for {symbol}")
    return sell(kis, symbol, qty=int(p["hldg_qty"]))


def cancel_remaining(kis: KIS, order_no: str) -> dict:
    """미체결 잔량 전부 취소"""
    return kis.post(
        "/uapi/domestic-stock/v1/trading/order-rvsecncl",
        {
            **_account_params(kis),
            "KRX_FWDG_ORD_ORGNO": "",
            "ORGN_ODNO": order_no,
            "ORD_DVSN": "00",
            "RVSE_CNCL_DVSN_CD": "02",
            "ORD_QTY": "0",
            "ORD_UNPR": "0",
            "QTY_ALL_ORD_YN": "Y",
        },
        _tr_id(kis, "VTTC0803U", "TTTC0803U"),
    )

"""계산 검증 유틸리티"""

from decimal import Decimal


def profit_rate(buy_price: int, current_price: int) -> Decimal:
    """수익률 계산 (예: 0.1 = 10%)"""
    if buy_price == 0:
        return Decimal(0)
    return (Decimal(current_price) - Decimal(buy_price)) / Decimal(buy_price)


def profit_amount(buy_price: int, current_price: int, qty: int) -> int:
    """수익금 계산"""
    return (current_price - buy_price) * qty


def avg_price(orders: list[dict]) -> int:
    """평균단가 계산 (orders: [{"price": 70000, "qty": 10}, ...])"""
    total_amount = sum(o["price"] * o["qty"] for o in orders)
    total_qty = sum(o["qty"] for o in orders)
    if total_qty == 0:
        return 0
    return int(total_amount / total_qty)


def total_value(positions: list[dict]) -> int:
    """총 평가금액 계산"""
    return sum(int(p.get("evlu_amt", 0)) for p in positions)


def total_profit(positions: list[dict]) -> int:
    """총 수익금 계산"""
    return sum(int(p.get("evlu_pfls_amt", 0)) for p in positions)


def verify_balance(balance: dict, positions: list[dict]) -> bool:
    """잔고 데이터 검증 (API값 vs 계산값)"""
    api_total = int(balance.get("tot_evlu_amt", 0))
    calc_total = total_value(positions)
    return abs(api_total - calc_total) < 1

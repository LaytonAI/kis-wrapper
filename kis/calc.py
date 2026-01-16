from decimal import Decimal


def profit_rate(buy_price: int, current_price: int) -> Decimal:
    if buy_price == 0:
        return Decimal(0)
    return (Decimal(current_price) - Decimal(buy_price)) / Decimal(buy_price)


def profit_amount(buy_price: int, current_price: int, qty: int) -> int:
    return (current_price - buy_price) * qty


def avg_price(orders: list[dict]) -> int:
    total_amount = sum(o["price"] * o["qty"] for o in orders)
    total_qty = sum(o["qty"] for o in orders)
    return int(total_amount / total_qty) if total_qty else 0


def total_value(positions: list[dict]) -> int:
    return sum(int(p.get("evlu_amt", 0)) for p in positions)


def total_profit(positions: list[dict]) -> int:
    return sum(int(p.get("evlu_pfls_amt", 0)) for p in positions)


def verify_balance(balance: dict, positions: list[dict]) -> bool:
    return abs(int(balance.get("tot_evlu_amt", 0)) - total_value(positions)) < 1

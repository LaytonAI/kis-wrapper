_TICK_TABLE = [(2000, 1), (5000, 5), (20000, 10), (50000, 50), (200000, 100), (500000, 500)]


def tick_size(price: int) -> int:
    for limit, tick in _TICK_TABLE:
        if price < limit:
            return tick
    return 1000


def round_price(price: int, direction: str = "down") -> int:
    tick = tick_size(price)
    if direction == "down":
        return (price // tick) * tick
    if direction == "up":
        return -(-price // tick) * tick
    return round(price / tick) * tick


def calc_cost(amount: int, rate: float) -> int:
    return int(amount * rate)


def order_status(order: dict) -> str:
    ord_qty = int(order.get("ord_qty", 0))
    ccld_qty = int(order.get("tot_ccld_qty", 0))
    if ccld_qty == 0:
        return "pending"
    return "filled" if ccld_qty >= ord_qty else "partial"


def ensure_list(value: object, key: str | None = None) -> list:
    if isinstance(value, list):
        return value
    if isinstance(value, dict) and key:
        return value.get(key, []) if isinstance(value.get(key), list) else []
    return []

"""유틸리티 함수"""

# (가격 상한, 호가단위) 테이블
_TICK_TABLE = [(2000, 1), (5000, 5), (20000, 10), (50000, 50), (200000, 100), (500000, 500)]


def tick_size(price: int) -> int:
    """가격대별 호가단위 반환"""
    for limit, tick in _TICK_TABLE:
        if price < limit:
            return tick
    return 1000


def round_price(price: int, direction: str = "down") -> int:
    """호가단위에 맞게 가격 조정 (direction: down/up/nearest)"""
    tick = tick_size(price)
    if direction == "down":
        return (price // tick) * tick
    if direction == "up":
        return -(-price // tick) * tick  # ceiling division
    return round(price / tick) * tick


def calc_cost(amount: int, rate: float) -> int:
    """비용 계산 (수수료/세금 공통)"""
    return int(amount * rate)


def order_status(order: dict) -> str:
    """주문 체결 상태 반환 (filled/partial/pending)"""
    ord_qty = int(order.get("ord_qty", 0))
    ccld_qty = int(order.get("tot_ccld_qty", 0))
    if ccld_qty == 0:
        return "pending"
    return "filled" if ccld_qty >= ord_qty else "partial"

"""calc.py 테스트"""

from decimal import Decimal

from kis import calc


def test_profit_rate():
    assert calc.profit_rate(70000, 77000) == Decimal("0.1")
    assert calc.profit_rate(70000, 63000) == Decimal("-0.1")


def test_profit_rate_zero_division():
    assert calc.profit_rate(0, 100) == Decimal(0)


def test_profit_amount():
    assert calc.profit_amount(70000, 77000, 10) == 70000
    assert calc.profit_amount(70000, 63000, 10) == -70000


def test_avg_price():
    orders = [
        {"price": 70000, "qty": 10},
        {"price": 72000, "qty": 10},
    ]
    assert calc.avg_price(orders) == 71000


def test_avg_price_weighted():
    orders = [
        {"price": 70000, "qty": 10},  # 700,000
        {"price": 80000, "qty": 5},  # 400,000
    ]
    # (700000 + 400000) / 15 = 73333.33...
    assert calc.avg_price(orders) == 73333


def test_avg_price_empty():
    assert calc.avg_price([]) == 0


def test_total_value():
    positions = [
        {"evlu_amt": "1000000"},
        {"evlu_amt": "500000"},
    ]
    assert calc.total_value(positions) == 1500000


def test_total_profit():
    positions = [
        {"evlu_pfls_amt": "100000"},
        {"evlu_pfls_amt": "-50000"},
    ]
    assert calc.total_profit(positions) == 50000


def test_verify_balance_valid():
    balance = {"tot_evlu_amt": "1500000"}
    positions = [
        {"evlu_amt": "1000000"},
        {"evlu_amt": "500000"},
    ]
    assert calc.verify_balance(balance, positions)


def test_verify_balance_mismatch():
    balance = {"tot_evlu_amt": "2000000"}
    positions = [
        {"evlu_amt": "1000000"},
        {"evlu_amt": "500000"},
    ]
    assert not calc.verify_balance(balance, positions)

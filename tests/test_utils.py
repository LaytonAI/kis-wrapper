"""utils.py 테스트"""

from kis.utils import calc_cost, order_status, round_price, tick_size


class TestTickSize:
    def test_under_2000(self):
        assert tick_size(1500) == 1
        assert tick_size(1999) == 1

    def test_2000_to_5000(self):
        assert tick_size(2000) == 5
        assert tick_size(3000) == 5
        assert tick_size(4999) == 5

    def test_5000_to_20000(self):
        assert tick_size(5000) == 10
        assert tick_size(15000) == 10
        assert tick_size(19999) == 10

    def test_20000_to_50000(self):
        assert tick_size(20000) == 50
        assert tick_size(30000) == 50
        assert tick_size(49999) == 50

    def test_50000_to_200000(self):
        assert tick_size(50000) == 100
        assert tick_size(70000) == 100
        assert tick_size(199999) == 100

    def test_200000_to_500000(self):
        assert tick_size(200000) == 500
        assert tick_size(300000) == 500
        assert tick_size(499999) == 500

    def test_over_500000(self):
        assert tick_size(500000) == 1000
        assert tick_size(1000000) == 1000


class TestRoundPrice:
    def test_round_down(self):
        assert round_price(70050, "down") == 70000
        assert round_price(70099, "down") == 70000
        assert round_price(70100, "down") == 70100

    def test_round_up(self):
        assert round_price(70001, "up") == 70100
        assert round_price(70100, "up") == 70100
        assert round_price(70000, "up") == 70000

    def test_round_nearest(self):
        assert round_price(70049, "nearest") == 70000
        assert round_price(70051, "nearest") == 70100

    def test_default_is_down(self):
        assert round_price(70050) == 70000


class TestCalcCost:
    def test_fee(self):
        # 0.015% = 0.00015
        assert calc_cost(10_000_000, 0.00015) in (1499, 1500)

    def test_tax(self):
        # 0.18% = 0.0018
        assert calc_cost(10_000_000, 0.0018) == 18000

    def test_overseas_fee(self):
        # 0.25% = 0.0025
        assert calc_cost(10_000_000, 0.0025) == 25000


class TestOrderStatus:
    def test_filled(self):
        assert order_status({"ord_qty": "100", "tot_ccld_qty": "100"}) == "filled"
        assert order_status({"ord_qty": "100", "tot_ccld_qty": "150"}) == "filled"

    def test_partial(self):
        assert order_status({"ord_qty": "100", "tot_ccld_qty": "50"}) == "partial"
        assert order_status({"ord_qty": "100", "tot_ccld_qty": "1"}) == "partial"

    def test_pending(self):
        assert order_status({"ord_qty": "100", "tot_ccld_qty": "0"}) == "pending"
        assert order_status({}) == "pending"

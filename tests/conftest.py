import json
from pathlib import Path

import pytest

from kis.client import KIS

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def kis():
    return KIS("test_key", "test_secret", "12345678-01")


@pytest.fixture
def price_fixture():
    with open(FIXTURES / "domestic/price_005930.json") as f:
        return json.load(f)


@pytest.fixture
def orderbook_fixture():
    with open(FIXTURES / "domestic/orderbook_005930.json") as f:
        return json.load(f)


@pytest.fixture
def balance_fixture():
    with open(FIXTURES / "domestic/balance.json") as f:
        return json.load(f)

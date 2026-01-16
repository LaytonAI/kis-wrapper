import json
from pathlib import Path

import pytest

from kis.async_client import AsyncKIS
from kis.client import KIS

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def kis():
    return KIS("test_key", "test_secret", "12345678-01")


@pytest.fixture
def async_kis():
    return AsyncKIS("test_key", "test_secret", "12345678-01")


@pytest.fixture
def price_fixture():
    return json.loads((FIXTURES / "domestic/price_005930.json").read_text())


@pytest.fixture
def orderbook_fixture():
    return json.loads((FIXTURES / "domestic/orderbook_005930.json").read_text())


@pytest.fixture
def balance_fixture():
    return json.loads((FIXTURES / "domestic/balance.json").read_text())

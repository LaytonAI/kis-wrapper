import pytest

from kis.client import KIS


@pytest.fixture
def kis():
    return KIS("test_key", "test_secret", "12345678-01")

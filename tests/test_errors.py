"""에러 처리 테스트"""

import pytest

from kis.errors import (
    ERROR_MAP,
    AccessDeniedError,
    AuthError,
    GatewayError,
    InsufficientBalanceError,
    KISError,
    MarketClosedError,
    OrderError,
    RateLimitError,
    SubscribeError,
    SymbolError,
    TokenExpiredError,
    WebSocketError,
    raise_for_code,
)


def test_kis_error_attributes():
    err = KISError("TEST001", "테스트 에러")
    assert err.code == "TEST001"
    assert err.message == "테스트 에러"
    assert "[TEST001] 테스트 에러" in str(err)


def test_error_inheritance():
    """에러 계층 구조"""
    # Gateway (EGW)
    assert issubclass(GatewayError, KISError)
    assert issubclass(AuthError, GatewayError)
    assert issubclass(TokenExpiredError, AuthError)
    assert issubclass(RateLimitError, GatewayError)
    assert issubclass(AccessDeniedError, GatewayError)
    # Business (APBK)
    assert issubclass(OrderError, KISError)
    assert issubclass(SymbolError, KISError)
    assert issubclass(MarketClosedError, KISError)
    assert issubclass(InsufficientBalanceError, KISError)
    # WebSocket (OPSP)
    assert issubclass(WebSocketError, KISError)
    assert issubclass(SubscribeError, WebSocketError)


@pytest.mark.parametrize("code,error_class", [
    ("EGW00123", TokenExpiredError),
    ("EGW00201", RateLimitError),
    ("EGW00003", AccessDeniedError),
    ("APBK0919", OrderError),
    ("APBK0656", InsufficientBalanceError),
    ("APBK0013", SymbolError),
    ("APBK1058", MarketClosedError),
    ("OPSP0008", SubscribeError),
])
def test_raise_for_code(code, error_class):
    with pytest.raises(error_class) as exc:
        raise_for_code(code, "test")
    assert exc.value.code == code


def test_raise_for_code_unknown():
    with pytest.raises(KISError) as exc:
        raise_for_code("UNKNOWN", "알 수 없는 에러")
    assert exc.value.code == "UNKNOWN"
    assert type(exc.value) is KISError


def test_error_map_coverage():
    expected = ["EGW00123", "EGW00201", "EGW00003", "APBK0656", "APBK0013", "OPSP0008", "OPSP8991"]
    for code in expected:
        assert code in ERROR_MAP

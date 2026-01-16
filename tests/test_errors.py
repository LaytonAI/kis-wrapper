"""에러 처리 테스트"""

import pytest

from kis.errors import (
    ERROR_MAP,
    AuthError,
    InsufficientBalanceError,
    KISError,
    MarketClosedError,
    OrderError,
    RateLimitError,
    SymbolError,
    TokenExpiredError,
    raise_for_code,
)


def test_kis_error_attributes():
    err = KISError("TEST001", "테스트 에러")
    assert err.code == "TEST001"
    assert err.message == "테스트 에러"
    assert "[TEST001] 테스트 에러" in str(err)


def test_kis_error_inheritance():
    assert issubclass(RateLimitError, KISError)
    assert issubclass(AuthError, KISError)
    assert issubclass(TokenExpiredError, AuthError)
    assert issubclass(OrderError, KISError)
    assert issubclass(SymbolError, KISError)
    assert issubclass(MarketClosedError, KISError)
    assert issubclass(InsufficientBalanceError, KISError)


def test_raise_for_code_known_error():
    with pytest.raises(TokenExpiredError) as exc:
        raise_for_code("EGW00123", "토큰 만료")
    assert exc.value.code == "EGW00123"
    assert exc.value.message == "토큰 만료"


def test_raise_for_code_order_error():
    with pytest.raises(OrderError):
        raise_for_code("APBK0919", "주문수량 초과")


def test_raise_for_code_insufficient_balance():
    with pytest.raises(InsufficientBalanceError):
        raise_for_code("APBK0656", "매수가능금액 부족")


def test_raise_for_code_symbol_error():
    with pytest.raises(SymbolError):
        raise_for_code("APBK0013", "종목코드 오류")


def test_raise_for_code_market_closed():
    with pytest.raises(MarketClosedError):
        raise_for_code("APBK1058", "주문가능시간 아님")


def test_raise_for_code_unknown_error():
    with pytest.raises(KISError) as exc:
        raise_for_code("UNKNOWN", "알 수 없는 에러")
    assert exc.value.code == "UNKNOWN"
    assert type(exc.value) is KISError


def test_error_map_has_expected_codes():
    assert "EGW00123" in ERROR_MAP
    assert "APBK0656" in ERROR_MAP
    assert "APBK0013" in ERROR_MAP


def test_rate_limit_error():
    err = RateLimitError("429", "API 호출 한도 초과")
    assert err.code == "429"
    assert "429" in str(err)

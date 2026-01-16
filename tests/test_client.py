from unittest.mock import patch

import httpx
import pytest

from kis.client import KIS
from kis.errors import CircuitBreakerError, KISError, NetworkError, RateLimitError


def test_init_and_switch():
    kis = KIS("key", "secret", "12345678-01")
    assert kis.is_paper
    assert kis.max_retries == 3
    assert kis.retry_delay == 1.0
    assert kis.throttle_rate == 20
    assert kis.cb_threshold == 5
    assert kis.cb_recovery_time == 30.0

    prod = kis.switch("prod")
    assert not prod.is_paper
    assert prod.app_key == kis.app_key
    assert prod.max_retries == kis.max_retries
    assert prod.throttle_rate == kis.throttle_rate
    assert kis.is_paper  # original unchanged


@patch("kis.client.get_token", return_value="test_token")
def test_headers(_, kis):
    headers = kis._headers("TR001")

    assert headers["authorization"] == "Bearer test_token"
    assert headers["appkey"] == "test_key"
    assert headers["tr_id"] == "TR001"


@patch("kis.client.get_token", return_value="test_token")
def test_get_success(_, kis, httpx_mock):
    httpx_mock.add_response(json={"rt_cd": "0", "output": {"price": "70000"}})
    assert kis.get("/test", {}, "TR001") == {"price": "70000"}


@patch("kis.client.get_token", return_value="test_token")
def test_post_success(_, kis, httpx_mock):
    httpx_mock.add_response(json={"rt_cd": "0", "output": {"order_no": "123"}})
    assert kis.post("/order", {"qty": 10}, "TR002") == {"order_no": "123"}


@patch("kis.client.get_token", return_value="test_token")
def test_api_error(_, kis, httpx_mock):
    httpx_mock.add_response(json={"rt_cd": "1", "msg_cd": "UNKNOWN", "msg1": "Invalid request"})

    with pytest.raises(KISError, match="Invalid request"):
        kis.get("/test", {}, "TR001")


def test_context_manager():
    with KIS("key", "secret", "12345678-01") as kis:
        assert kis.app_key == "key"


# === 429 Rate Limit Tests ===


@patch("kis.client.get_token", return_value="test_token")
@patch("kis.client.sleep")
def test_retry_on_429_then_success(mock_sleep, _, kis, httpx_mock):
    """429 후 재시도하여 성공"""
    httpx_mock.add_response(status_code=429, headers={"Retry-After": "0.1"})
    httpx_mock.add_response(json={"rt_cd": "0", "output": {"price": "70000"}})

    result = kis.get("/test", {}, "TR001")

    assert result == {"price": "70000"}
    mock_sleep.assert_called_once_with(0.1)


@patch("kis.client.get_token", return_value="test_token")
@patch("kis.client.sleep")
def test_retry_on_429_exponential_backoff(mock_sleep, _, httpx_mock):
    """429 지수 백오프"""
    kis = KIS("key", "secret", "12345678-01", max_retries=2, retry_delay=1.0)
    httpx_mock.add_response(status_code=429)  # no Retry-After
    httpx_mock.add_response(status_code=429)
    httpx_mock.add_response(json={"rt_cd": "0", "output": {}})

    kis.get("/test", {}, "TR001")

    # 1.0 * 2^0 = 1.0, 1.0 * 2^1 = 2.0
    calls = mock_sleep.call_args_list
    assert calls[0][0][0] == 1.0
    assert calls[1][0][0] == 2.0


@patch("kis.client.get_token", return_value="test_token")
@patch("kis.client.sleep")
def test_retry_on_429_max_retries_exceeded(mock_sleep, _, httpx_mock):
    """429 최대 재시도 초과"""
    kis = KIS("key", "secret", "12345678-01", max_retries=2)
    httpx_mock.add_response(status_code=429)
    httpx_mock.add_response(status_code=429)
    httpx_mock.add_response(status_code=429)  # 3rd = fail

    with pytest.raises(RateLimitError):
        kis.get("/test", {}, "TR001")

    assert mock_sleep.call_count == 2


# === Network Error Tests ===


@patch("kis.client.get_token", return_value="test_token")
@patch("kis.client.sleep")
def test_network_error_retry(mock_sleep, _, httpx_mock):
    """네트워크 에러 재시도"""
    kis = KIS("key", "secret", "12345678-01", max_retries=1, cb_threshold=0)
    httpx_mock.add_exception(httpx.ConnectError("Connection refused"))
    httpx_mock.add_response(json={"rt_cd": "0", "output": {"price": "70000"}})

    result = kis.get("/test", {}, "TR001")
    assert result == {"price": "70000"}
    assert mock_sleep.call_count == 1


@patch("kis.client.get_token", return_value="test_token")
@patch("kis.client.sleep")
def test_network_error_max_retries(mock_sleep, _, httpx_mock):
    """네트워크 에러 최대 재시도 초과"""
    kis = KIS("key", "secret", "12345678-01", max_retries=1, cb_threshold=0)
    httpx_mock.add_exception(httpx.ConnectError("Connection refused"))
    httpx_mock.add_exception(httpx.ConnectError("Connection refused"))

    with pytest.raises(NetworkError):
        kis.get("/test", {}, "TR001")


# === Circuit Breaker Tests ===


@patch("kis.client.get_token", return_value="test_token")
@patch("kis.client.sleep")
def test_circuit_breaker_opens(mock_sleep, _, httpx_mock):
    """Circuit breaker 열림"""
    kis = KIS("key", "secret", "12345678-01", max_retries=0, cb_threshold=2, cb_recovery_time=60.0)
    httpx_mock.add_exception(httpx.ConnectError("fail"))
    httpx_mock.add_exception(httpx.ConnectError("fail"))

    with pytest.raises(NetworkError):
        kis.get("/test", {}, "TR001")
    with pytest.raises(NetworkError):
        kis.get("/test", {}, "TR001")
    with pytest.raises(CircuitBreakerError):
        kis.get("/test", {}, "TR001")


@patch("kis.client.get_token", return_value="test_token")
def test_circuit_breaker_resets_on_success(_, httpx_mock):
    """성공 시 circuit breaker 리셋"""
    kis = KIS("key", "secret", "12345678-01", cb_threshold=3, throttle_rate=0)
    kis._cb_failures = 2  # 임계값 직전

    httpx_mock.add_response(json={"rt_cd": "0", "output": {}})
    kis.get("/test", {}, "TR001")

    assert kis._cb_failures == 0


# === Throttle Tests ===


@patch("kis.client.get_token", return_value="test_token")
@patch("kis.client.sleep")
@patch("kis.client.time", return_value=1000.0)
def test_throttle_delays_request(mock_time, mock_sleep, _, httpx_mock):
    """Throttle 대기"""
    kis = KIS("key", "secret", "12345678-01", throttle_rate=2, cb_threshold=0)
    httpx_mock.add_response(json={"rt_cd": "0", "output": {}})
    httpx_mock.add_response(json={"rt_cd": "0", "output": {}})
    httpx_mock.add_response(json={"rt_cd": "0", "output": {}})

    for _ in range(3):
        kis.get("/test", {}, "TR001")

    # 3번째 요청에서 throttle 대기 발생
    assert any(call[0][0] > 0 for call in mock_sleep.call_args_list)

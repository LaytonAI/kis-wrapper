"""비동기 클라이언트 테스트"""

from unittest.mock import AsyncMock, patch

import pytest

from kis.async_client import AsyncKIS
from kis.errors import KISError, RateLimitError


def test_init_and_switch():
    kis = AsyncKIS("key", "secret", "12345678-01")
    assert kis.is_paper and kis.max_retries == 3 and kis.retry_delay == 1.0
    assert kis.throttle_rate == 20 and kis.cb_threshold == 5
    prod = kis.switch("prod")
    assert not prod.is_paper and prod.app_key == kis.app_key
    assert prod.throttle_rate == kis.throttle_rate


@pytest.mark.asyncio
@patch("kis.async_client.get_token_async", new_callable=AsyncMock, return_value="test_token")
async def test_headers(_, async_kis):
    headers = await async_kis._headers("TR001")
    assert headers["authorization"] == "Bearer test_token"
    assert headers["appkey"] == "test_key" and headers["tr_id"] == "TR001"


@pytest.mark.asyncio
@patch("kis.async_client.get_token_async", new_callable=AsyncMock, return_value="test_token")
async def test_get_success(_, async_kis, httpx_mock):
    httpx_mock.add_response(json={"rt_cd": "0", "output": {"price": "70000"}})
    assert await async_kis.get("/test", {}, "TR001") == {"price": "70000"}


@pytest.mark.asyncio
@patch("kis.async_client.get_token_async", new_callable=AsyncMock, return_value="test_token")
async def test_post_success(_, async_kis, httpx_mock):
    httpx_mock.add_response(json={"rt_cd": "0", "output": {"order_no": "123"}})
    assert await async_kis.post("/order", {"qty": 10}, "TR002") == {"order_no": "123"}


@pytest.mark.asyncio
@patch("kis.async_client.get_token_async", new_callable=AsyncMock, return_value="test_token")
async def test_api_error(_, async_kis, httpx_mock):
    httpx_mock.add_response(json={"rt_cd": "1", "msg_cd": "UNKNOWN", "msg1": "Invalid request"})

    with pytest.raises(KISError, match="Invalid request"):
        await async_kis.get("/test", {}, "TR001")


@pytest.mark.asyncio
async def test_context_manager():
    async with AsyncKIS("key", "secret", "12345678-01") as kis:
        assert kis.app_key == "key"


# === 429 Rate Limit Tests ===


@pytest.mark.asyncio
@patch("kis.async_client.get_token_async", new_callable=AsyncMock, return_value="test_token")
@patch("kis.async_client.asyncio.sleep", new_callable=AsyncMock)
async def test_retry_on_429_then_success(mock_sleep, _, async_kis, httpx_mock):
    """429 후 재시도하여 성공"""
    httpx_mock.add_response(status_code=429, headers={"Retry-After": "0.1"})
    httpx_mock.add_response(json={"rt_cd": "0", "output": {"price": "70000"}})
    assert await async_kis.get("/test", {}, "TR001") == {"price": "70000"}
    mock_sleep.assert_called_once_with(0.1)


@pytest.mark.asyncio
@patch("kis.async_client.get_token_async", new_callable=AsyncMock, return_value="test_token")
@patch("kis.async_client.asyncio.sleep", new_callable=AsyncMock)
async def test_retry_on_429_exponential_backoff(mock_sleep, _, httpx_mock):
    """429 지수 백오프"""
    kis = AsyncKIS("key", "secret", "12345678-01", max_retries=2, retry_delay=1.0)
    httpx_mock.add_response(status_code=429)
    httpx_mock.add_response(status_code=429)
    httpx_mock.add_response(json={"rt_cd": "0", "output": {}})
    await kis.get("/test", {}, "TR001")
    assert [c[0][0] for c in mock_sleep.call_args_list] == [1.0, 2.0]


@pytest.mark.asyncio
@patch("kis.async_client.get_token_async", new_callable=AsyncMock, return_value="test_token")
@patch("kis.async_client.asyncio.sleep", new_callable=AsyncMock)
async def test_retry_on_429_max_retries_exceeded(mock_sleep, _, httpx_mock):
    """429 최대 재시도 초과"""
    kis = AsyncKIS("key", "secret", "12345678-01", max_retries=2)
    httpx_mock.add_response(status_code=429)
    httpx_mock.add_response(status_code=429)
    httpx_mock.add_response(status_code=429)

    with pytest.raises(RateLimitError):
        await kis.get("/test", {}, "TR001")

    assert mock_sleep.call_count == 2


# === domestic/overseas 모듈 연동 테스트 ===


@pytest.mark.asyncio
@patch("kis.async_client.get_token_async", new_callable=AsyncMock, return_value="test_token")
async def test_domestic_price_via_async_kis(_, httpx_mock):
    """domestic.price가 AsyncKIS와 연동되는지 테스트"""
    from kis import domestic
    httpx_mock.add_response(json={"rt_cd": "0", "output": {"stck_prpr": "70000"}})
    async with AsyncKIS("key", "secret", "12345678-01") as kis:
        assert (await domestic.price(kis, "005930"))["stck_prpr"] == "70000"


@pytest.mark.asyncio
@patch("kis.async_client.get_token_async", new_callable=AsyncMock, return_value="test_token")
async def test_overseas_price_via_async_kis(_, httpx_mock):
    """overseas.price가 AsyncKIS와 연동되는지 테스트"""
    from kis import overseas
    httpx_mock.add_response(json={"rt_cd": "0", "output": {"last": "150.00"}})
    async with AsyncKIS("key", "secret", "12345678-01") as kis:
        assert (await overseas.price(kis, "AAPL", "NAS"))["last"] == "150.00"

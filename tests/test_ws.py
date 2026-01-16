import base64
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from kis.ws import WSClient


@pytest.fixture
def mock_kis():
    kis = MagicMock()
    kis.app_key = "test_key"
    kis.app_secret = "test_secret"
    kis.env = "paper"
    return kis


@pytest.fixture
def ws_client(mock_kis):
    return WSClient(mock_kis)


class TestWSUrl:
    def test_paper_env_uses_port_31000(self, ws_client):
        assert "31000" in ws_client._ws_url

    def test_prod_env_uses_port_21000(self):
        kis = MagicMock()
        kis.env = "prod"
        ws = WSClient(kis)
        assert "21000" in ws._ws_url


class TestSubscription:
    async def test_subscribe_adds_symbol_to_subscriptions(self, ws_client):
        ws_client._ws = AsyncMock()
        callback = MagicMock()

        await ws_client.subscribe("H0STCNT0", ["005930"], callback)

        assert "H0STCNT0" in ws_client._subscriptions
        assert "005930" in ws_client._subscriptions["H0STCNT0"]
        assert ws_client._callbacks["H0STCNT0"] == callback

    async def test_subscribe_multiple_symbols(self, ws_client):
        ws_client._ws = AsyncMock()
        callback = MagicMock()

        await ws_client.subscribe("H0STCNT0", ["005930", "000660"], callback)

        assert "005930" in ws_client._subscriptions["H0STCNT0"]
        assert "000660" in ws_client._subscriptions["H0STCNT0"]
        assert ws_client._ws.send.call_count == 2

    async def test_subscribe_same_symbol_twice_sends_once(self, ws_client):
        ws_client._ws = AsyncMock()
        callback = MagicMock()

        await ws_client.subscribe("H0STCNT0", ["005930"], callback)
        await ws_client.subscribe("H0STCNT0", ["005930"], callback)

        assert ws_client._ws.send.call_count == 1

    async def test_unsubscribe_removes_symbol(self, ws_client):
        ws_client._ws = AsyncMock()
        ws_client._subscriptions["H0STCNT0"] = {"005930", "000660"}

        await ws_client.unsubscribe("H0STCNT0", ["005930"])

        assert "005930" not in ws_client._subscriptions["H0STCNT0"]
        assert "000660" in ws_client._subscriptions["H0STCNT0"]

    async def test_unsubscribe_nonexistent_does_nothing(self, ws_client):
        ws_client._ws = AsyncMock()
        await ws_client.unsubscribe("H0STCNT0", ["005930"])
        assert ws_client._ws.send.call_count == 0


class TestParseData:
    def test_parse_h0stcnt0_realtime_price(self, ws_client):
        # 종목코드^시간^현재가^전일대비^전일대비부호^전일대비율^...^거래량
        raw = "005930^092500^70000^-1000^0^-1.41^0^0^0^0^0^0^12345"
        result = ws_client._parse_data("H0STCNT0", raw)

        assert result["symbol"] == "005930"
        assert result["time"] == "092500"
        assert result["price"] == 70000
        assert result["change"] == -1000
        assert result["volume"] == 12345

    def test_parse_h0stasp0_orderbook(self, ws_client):
        # 호가 데이터
        raw = "005930^092500^70100^70000^69900^70200^70300^70400"
        result = ws_client._parse_data("H0STASP0", raw)

        assert result["symbol"] == "005930"
        assert "ask1" in result
        assert "bid1" in result

    def test_parse_unknown_tr_returns_raw(self, ws_client):
        raw = "some^unknown^data"
        result = ws_client._parse_data("UNKNOWN", raw)
        assert result["raw"] == raw


class TestMessageHandling:
    async def test_handle_json_response_stores_iv_key(self, ws_client):
        # 접속 응답에서 IV, Key 저장
        iv = base64.b64encode(b"1234567890123456").decode()
        key = base64.b64encode(b"12345678901234567890123456789012").decode()
        resp = {
            "header": {"tr_id": "PINGPONG"},
            "body": {"output": {"iv": iv, "key": key}},
        }

        await ws_client._handle_message(json.dumps(resp))

        assert ws_client._iv == b"1234567890123456"
        assert ws_client._key == b"12345678901234567890123456789012"

    async def test_handle_unencrypted_data_calls_callback(self, ws_client):
        callback = AsyncMock()
        ws_client._callbacks["H0STCNT0"] = callback
        raw = "0|H0STCNT0|005930^092500^70000^-1000^0^0^0^0^0^0^0^0^12345"

        await ws_client._handle_message(raw)

        callback.assert_called_once()
        data = callback.call_args[0][0]
        assert data["symbol"] == "005930"
        assert data["price"] == 70000

    async def test_handle_sync_callback(self, ws_client):
        callback = MagicMock()
        ws_client._callbacks["H0STCNT0"] = callback
        raw = "0|H0STCNT0|005930^092500^70000^-1000^0^0^0^0^0^0^0^0^12345"

        await ws_client._handle_message(raw)

        callback.assert_called_once()


class TestAESDecryption:
    def test_decrypt_valid_data(self, ws_client):
        from Crypto.Cipher import AES
        from Crypto.Util.Padding import pad

        ws_client._key = b"12345678901234567890123456789012"  # 32 bytes
        ws_client._iv = b"1234567890123456"  # 16 bytes

        plaintext = "005930^092500^70000^-1000"
        cipher = AES.new(ws_client._key, AES.MODE_CBC, ws_client._iv)
        encrypted = base64.b64encode(cipher.encrypt(pad(plaintext.encode(), AES.block_size)))

        result = ws_client._decrypt(encrypted.decode())
        assert result == plaintext


class TestReconnection:
    async def test_reconnect_increments_retry_count(self, ws_client):
        ws_client._running = True
        ws_client._retry_count = 0

        with patch("asyncio.sleep", new_callable=AsyncMock):
            await ws_client._reconnect()

        assert ws_client._retry_count == 1
        assert ws_client._ws is None

    async def test_reconnect_uses_exponential_backoff(self, ws_client):
        ws_client._running = True
        ws_client.retry_delay = 1.0

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            ws_client._retry_count = 0
            await ws_client._reconnect()
            mock_sleep.assert_called_with(1.0)

            ws_client._retry_count = 1
            await ws_client._reconnect()
            mock_sleep.assert_called_with(2.0)

            ws_client._retry_count = 2
            await ws_client._reconnect()
            mock_sleep.assert_called_with(4.0)

    async def test_reconnect_raises_after_max_retries(self, ws_client):
        ws_client._running = True
        ws_client._retry_count = 5
        ws_client.max_retries = 5

        with pytest.raises(ConnectionError, match="Max retries"):
            await ws_client._reconnect()

        assert ws_client._running is False


class TestRestoreSubscriptions:
    async def test_restore_sends_subscribe_for_all(self, ws_client):
        ws_client._ws = AsyncMock()
        ws_client._subscriptions = {
            "H0STCNT0": {"005930", "000660"},
            "H0STASP0": {"005930"},
        }

        await ws_client._restore_subscriptions()

        assert ws_client._ws.send.call_count == 3


class TestClose:
    async def test_close_stops_running_and_closes_ws(self, ws_client):
        ws_client._running = True
        ws_client._ws = AsyncMock()

        await ws_client.close()

        assert ws_client._running is False
        ws_client._ws.close.assert_called_once()

    async def test_close_without_ws_does_not_fail(self, ws_client):
        ws_client._running = True
        ws_client._ws = None

        await ws_client.close()  # should not raise

        assert ws_client._running is False

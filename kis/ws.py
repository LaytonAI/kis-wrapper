import asyncio
import base64
import json
from collections.abc import Awaitable, Callable

import websockets
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

from kis.auth import get_ws_key
from kis.client import KIS

Callback = Callable[[dict], Awaitable[None]] | Callable[[dict], None]


class WSClient:
    __slots__ = (
        "kis",
        "max_retries",
        "retry_delay",
        "_ws",
        "_subscriptions",
        "_callbacks",
        "_running",
        "_retry_count",
        "_iv",
        "_key",
    )

    def __init__(self, kis: KIS, max_retries: int = 5, retry_delay: float = 1.0):
        self.kis, self.max_retries, self.retry_delay = kis, max_retries, retry_delay
        self._ws, self._iv, self._key = None, None, None
        self._subscriptions: dict[str, set[str]] = {}
        self._callbacks: dict[str, Callback] = {}
        self._running, self._retry_count = False, 0

    @property
    def _ws_url(self) -> str:
        return f"ws://ops.koreainvestment.com:{'31000' if self.kis.env == 'paper' else '21000'}"

    async def connect(self) -> None:
        self._ws = await websockets.connect(self._ws_url)
        self._running, self._retry_count = True, 0
        await self._send(
            {
                "header": {
                    "approval_key": get_ws_key(self.kis.app_key, self.kis.app_secret, self.kis.env),
                    "tr_type": "1",
                    "content-type": "utf-8",
                },
                "body": {"input": {}},
            }
        )

    async def subscribe(self, tr_id: str, symbols: list[str], callback: Callback) -> None:
        """Subscribe to real-time data (H0STCNT0: price, H0STASP0: orderbook, H0STCNI0: fills)."""
        self._subscriptions.setdefault(tr_id, set())
        self._callbacks[tr_id] = callback
        for symbol in symbols:
            if symbol not in self._subscriptions[tr_id]:
                self._subscriptions[tr_id].add(symbol)
                await self._send_sub(tr_id, symbol, "1")

    async def unsubscribe(self, tr_id: str, symbols: list[str]) -> None:
        if tr_id not in self._subscriptions:
            return
        for symbol in symbols:
            if symbol in self._subscriptions[tr_id]:
                self._subscriptions[tr_id].remove(symbol)
                await self._send_sub(tr_id, symbol, "2")

    async def _send_sub(self, tr_id: str, symbol: str, tr_type: str) -> None:
        await self._send(
            {
                "header": {"tr_type": tr_type, "tr_id": tr_id, "content-type": "utf-8"},
                "body": {"input": {"tr_id": tr_id, "tr_key": symbol}},
            }
        )

    async def _send(self, msg: dict) -> None:
        if self._ws:
            await self._ws.send(json.dumps(msg))

    async def run(self) -> None:
        while self._running:
            try:
                if not self._ws:
                    await self.connect()
                    await self._restore_subscriptions()
                async for message in self._ws:
                    await self._handle_message(message)
            except Exception:
                await self._reconnect()

    async def _handle_message(self, raw: str) -> None:
        if not (raw.startswith("0|") or raw.startswith("1|")):
            out = json.loads(raw).get("body", {}).get("output", {})
            if "iv" in out:
                self._iv = base64.b64decode(out["iv"])
            if "key" in out:
                self._key = base64.b64decode(out["key"])
            return
        parts = raw.split("|")
        tr_id, data_str = (parts[1] if len(parts) > 1 else None), parts[-1]
        if raw.startswith("1|") and self._key and self._iv:
            data_str = self._decrypt(data_str)
        if tr_id and tr_id in self._callbacks:
            cb, data = self._callbacks[tr_id], self._parse_data(tr_id, data_str)
            await cb(data) if asyncio.iscoroutinefunction(cb) else cb(data)

    def _decrypt(self, data: str) -> str:
        cipher = AES.new(self._key, AES.MODE_CBC, self._iv)
        return unpad(cipher.decrypt(base64.b64decode(data)), AES.block_size).decode()

    def _parse_data(self, tr_id: str | None, data: str) -> dict:
        f = data.split("^")
        if tr_id == "H0STCNT0":
            return {
                "symbol": f[0],
                "time": f[1],
                "price": int(f[2]),
                "change": int(f[3]),
                "volume": int(f[12]),
            }
        if tr_id == "H0STASP0":
            return {
                "symbol": f[0],
                "time": f[1],
                "ask1": int(f[2]) if len(f) > 2 else 0,
                "bid1": int(f[3]) if len(f) > 3 else 0,
            }
        return {"raw": data}

    async def _reconnect(self) -> None:
        if self._retry_count >= self.max_retries:
            self._running = False
            raise ConnectionError(f"Max retries ({self.max_retries}) exceeded")
        self._retry_count += 1
        await asyncio.sleep(self.retry_delay * (2 ** (self._retry_count - 1)))
        self._ws = None

    async def _restore_subscriptions(self) -> None:
        for tr_id, symbols in self._subscriptions.items():
            for symbol in symbols:
                await self._send_sub(tr_id, symbol, "1")

    async def close(self) -> None:
        self._running = False
        if self._ws:
            await self._ws.close()

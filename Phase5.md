# Phase 5: WebSocket (실시간)

## 목표
- 실시간 시세 구독
- 자동 재연결
- 체결통보 수신

## 설계 원칙
- 상태 관리 필요 → 클래스 사용
- 콜백 기반 인터페이스
- 견고한 재연결 로직

## 5.1 WebSocket 클라이언트

### 인터페이스
```python
# kis/ws.py
import asyncio
import json
from collections.abc import Callable, Awaitable
from typing import Any
import websockets
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import base64

from kis.client import KIS
from kis.auth import get_ws_key

# 콜백 타입
Callback = Callable[[dict], Awaitable[None]] | Callable[[dict], None]

class WSClient:
    """WebSocket 실시간 클라이언트"""

    def __init__(
        self,
        kis: KIS,
        max_retries: int = 5,
        retry_delay: float = 1.0,
    ):
        self.kis = kis
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        self._ws: websockets.WebSocketClientProtocol | None = None
        self._subscriptions: dict[str, set[str]] = {}  # tr_id -> {symbols}
        self._callbacks: dict[str, Callback] = {}      # tr_id -> callback
        self._running = False
        self._retry_count = 0
        self._iv: bytes | None = None
        self._key: bytes | None = None

    @property
    def _ws_url(self) -> str:
        if self.kis.env == "paper":
            return "ws://ops.koreainvestment.com:31000"
        return "ws://ops.koreainvestment.com:21000"

    async def connect(self) -> None:
        """WebSocket 연결"""
        approval_key = get_ws_key(
            self.kis.app_key,
            self.kis.app_secret,
            self.kis.env
        )
        self._ws = await websockets.connect(self._ws_url)
        self._running = True
        self._retry_count = 0

        # 접속키로 초기 메시지 전송
        await self._send({
            "header": {
                "approval_key": approval_key,
                "tr_type": "1",
                "content-type": "utf-8",
            },
            "body": {"input": {}},
        })

    async def subscribe(
        self,
        tr_id: str,
        symbols: list[str],
        callback: Callback,
    ) -> None:
        """실시간 데이터 구독

        Args:
            tr_id: 거래 ID (예: "H0STCNT0" 국내주식 체결)
            symbols: 종목코드 리스트
            callback: 데이터 수신 콜백

        TR ID 목록:
            - H0STCNT0: 국내주식 실시간체결
            - H0STASP0: 국내주식 실시간호가
            - H0STCNI0: 체결통보 (내 주문 체결)
        """
        if tr_id not in self._subscriptions:
            self._subscriptions[tr_id] = set()

        self._callbacks[tr_id] = callback

        for symbol in symbols:
            if symbol not in self._subscriptions[tr_id]:
                self._subscriptions[tr_id].add(symbol)
                await self._send_subscribe(tr_id, symbol)

    async def unsubscribe(self, tr_id: str, symbols: list[str]) -> None:
        """구독 해제"""
        if tr_id not in self._subscriptions:
            return

        for symbol in symbols:
            if symbol in self._subscriptions[tr_id]:
                self._subscriptions[tr_id].remove(symbol)
                await self._send_unsubscribe(tr_id, symbol)

    async def _send_subscribe(self, tr_id: str, symbol: str) -> None:
        """구독 요청 전송"""
        msg = {
            "header": {
                "tr_type": "1",
                "tr_id": tr_id,
                "content-type": "utf-8",
            },
            "body": {
                "input": {
                    "tr_id": tr_id,
                    "tr_key": symbol,
                }
            }
        }
        await self._send(msg)

    async def _send_unsubscribe(self, tr_id: str, symbol: str) -> None:
        """구독 해제 요청"""
        msg = {
            "header": {
                "tr_type": "2",  # 해제
                "tr_id": tr_id,
            },
            "body": {"input": {"tr_id": tr_id, "tr_key": symbol}}
        }
        await self._send(msg)

    async def _send(self, msg: dict) -> None:
        """메시지 전송"""
        if self._ws:
            await self._ws.send(json.dumps(msg))

    async def run(self) -> None:
        """메인 수신 루프"""
        while self._running:
            try:
                if not self._ws:
                    await self.connect()
                    await self._restore_subscriptions()

                async for message in self._ws:
                    await self._handle_message(message)

            except websockets.ConnectionClosed:
                await self._reconnect()
            except Exception as e:
                print(f"WebSocket error: {e}")
                await self._reconnect()

    async def _handle_message(self, raw: str) -> None:
        """메시지 처리"""
        # 암호화된 메시지인지 확인
        if raw.startswith("0|") or raw.startswith("1|"):
            encrypted = raw.startswith("1|")
            parts = raw.split("|")
            tr_id = parts[1] if len(parts) > 1 else None
            data_str = parts[-1]

            if encrypted and self._key and self._iv:
                data_str = self._decrypt(data_str)

            data = self._parse_data(tr_id, data_str)

            if tr_id and tr_id in self._callbacks:
                cb = self._callbacks[tr_id]
                if asyncio.iscoroutinefunction(cb):
                    await cb(data)
                else:
                    cb(data)
        else:
            # JSON 응답 (접속 확인 등)
            resp = json.loads(raw)
            # IV, Key 저장 (암호화용)
            if "body" in resp and "output" in resp["body"]:
                out = resp["body"]["output"]
                if "iv" in out:
                    self._iv = base64.b64decode(out["iv"])
                if "key" in out:
                    self._key = base64.b64decode(out["key"])

    def _decrypt(self, data: str) -> str:
        """AES 복호화"""
        cipher = AES.new(self._key, AES.MODE_CBC, self._iv)
        decrypted = unpad(cipher.decrypt(base64.b64decode(data)), AES.block_size)
        return decrypted.decode("utf-8")

    def _parse_data(self, tr_id: str, data: str) -> dict:
        """데이터 파싱 (TR별 포맷)"""
        # 실시간 체결 (H0STCNT0)
        if tr_id == "H0STCNT0":
            fields = data.split("^")
            return {
                "symbol": fields[0],
                "time": fields[1],
                "price": int(fields[2]),
                "change": int(fields[3]),
                "volume": int(fields[12]),
            }
        # 기타 TR은 raw dict 반환
        return {"raw": data}

    async def _reconnect(self) -> None:
        """재연결"""
        if self._retry_count >= self.max_retries:
            self._running = False
            raise ConnectionError(f"Max retries ({self.max_retries}) exceeded")

        self._retry_count += 1
        delay = self.retry_delay * (2 ** (self._retry_count - 1))  # 지수 백오프
        print(f"Reconnecting in {delay}s (attempt {self._retry_count})")

        await asyncio.sleep(delay)
        self._ws = None

    async def _restore_subscriptions(self) -> None:
        """재연결 후 구독 복원"""
        for tr_id, symbols in self._subscriptions.items():
            for symbol in symbols:
                await self._send_subscribe(tr_id, symbol)

    async def close(self) -> None:
        """연결 종료"""
        self._running = False
        if self._ws:
            await self._ws.close()
```

### 사용 예시
```python
from kis import KIS
from kis.ws import WSClient

async def main():
    kis = KIS(app_key, app_secret, account, env="paper")
    ws = WSClient(kis)

    # 체결가 수신 콜백
    async def on_price(data: dict):
        print(f"{data['symbol']}: {data['price']:,}원")

    # 구독
    await ws.subscribe("H0STCNT0", ["005930", "000660"], on_price)

    # 실행
    try:
        await ws.run()
    except KeyboardInterrupt:
        await ws.close()

asyncio.run(main())
```

## 5.2 테스트

```python
# tests/test_ws.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from kis.ws import WSClient

@pytest.fixture
def ws_client():
    kis = MagicMock()
    kis.app_key = "key"
    kis.app_secret = "secret"
    kis.env = "paper"
    return WSClient(kis)

def test_ws_url_paper(ws_client):
    assert "31000" in ws_client._ws_url

def test_ws_url_prod():
    kis = MagicMock()
    kis.env = "prod"
    ws = WSClient(kis)
    assert "21000" in ws._ws_url

@pytest.mark.asyncio
async def test_subscribe_adds_to_subscriptions(ws_client):
    ws_client._ws = AsyncMock()
    ws_client._ws.send = AsyncMock()

    callback = MagicMock()
    await ws_client.subscribe("H0STCNT0", ["005930"], callback)

    assert "005930" in ws_client._subscriptions["H0STCNT0"]
    assert ws_client._callbacks["H0STCNT0"] == callback

def test_parse_data_h0stcnt0(ws_client):
    raw = "005930^092500^70000^-1000^0^0^0^0^0^0^0^0^12345"
    result = ws_client._parse_data("H0STCNT0", raw)

    assert result["symbol"] == "005930"
    assert result["price"] == 70000
```

## 5.3 TR ID 목록

| TR ID | 설명 | 비고 |
|-------|------|------|
| H0STCNT0 | 국내주식 실시간체결 | |
| H0STASP0 | 국내주식 실시간호가 | |
| H0STCNI0 | 체결통보 | HTS ID 필요 |
| HDFSCNT0 | 해외주식 실시간체결 | |
| HDFSASP0 | 해외주식 실시간호가 | |

## 완료 조건
- [ ] test_ws.py 작성/통과
- [ ] ws.py 구현
- [ ] 국내주식 실시간체결 테스트
- [ ] 자동 재연결 테스트
- [ ] AES 복호화 테스트

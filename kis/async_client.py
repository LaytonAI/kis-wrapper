import asyncio
from collections import deque
from time import time

import httpx

from kis.auth import Env, _base_url, get_token_async
from kis.client import _parse_response, _split_account
from kis.errors import CircuitBreakerError, NetworkError, RateLimitError
from kis.resilience import CB_OPEN, cb_on_failure, cb_state, throttle_wait


class AsyncKIS:
    __slots__ = (
        "app_key", "app_secret", "account", "env", "max_retries", "retry_delay",
        "throttle_rate", "cb_threshold", "cb_recovery_time",
        "_client", "_throttle_ts", "_cb_failures", "_cb_open_until",
    )

    def __init__(
        self,
        app_key: str,
        app_secret: str,
        account: str,
        env: Env = "paper",
        max_retries: int = 3,
        retry_delay: float = 1.0,
        throttle_rate: int = 20,
        cb_threshold: int = 5,
        cb_recovery_time: float = 30.0,
    ):
        self.app_key, self.app_secret, self.account = app_key, app_secret, account
        self.env, self.max_retries, self.retry_delay = env, max_retries, retry_delay
        self.throttle_rate, self.cb_threshold, self.cb_recovery_time = (
            throttle_rate, cb_threshold, cb_recovery_time
        )
        self._client = httpx.AsyncClient(base_url=_base_url(env), timeout=10.0)
        self._throttle_ts: deque = deque()
        self._cb_failures, self._cb_open_until = 0, 0.0

    @property
    def is_paper(self) -> bool:
        return self.env == "paper"

    @property
    def account_params(self) -> dict:
        return _split_account(self.account)

    def switch(self, env: Env) -> "AsyncKIS":
        return AsyncKIS(
            self.app_key, self.app_secret, self.account, env,
            self.max_retries, self.retry_delay,
            self.throttle_rate, self.cb_threshold, self.cb_recovery_time,
        )

    async def _headers(self, tr_id: str) -> dict:
        return {
            "authorization": f"Bearer {await get_token_async(self.app_key, self.app_secret, self.env)}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": tr_id,
            "content-type": "application/json; charset=utf-8",
        }

    async def _request(self, method: str, path: str, tr_id: str, **kwargs) -> dict:
        for attempt in range(self.max_retries + 1):
            now = time()
            if cb_state(self._cb_failures, self.cb_threshold, self._cb_open_until, now) == CB_OPEN:
                raise CircuitBreakerError("CB_OPEN", "Circuit breaker is open")
            if (wait := throttle_wait(self._throttle_ts, self.throttle_rate, now)) > 0:
                await asyncio.sleep(wait)
            try:
                resp = await getattr(self._client, method)(
                    path, headers=await self._headers(tr_id), **kwargs
                )
            except (httpx.ConnectError, httpx.TimeoutException) as e:
                self._cb_failures, self._cb_open_until = cb_on_failure(
                    self._cb_failures, self.cb_threshold, self.cb_recovery_time, time()
                )
                if attempt == self.max_retries:
                    raise NetworkError("NETWORK", str(e)) from e
                await asyncio.sleep(self.retry_delay * (2 ** attempt))
                continue
            if resp.status_code == 429:
                if attempt == self.max_retries:
                    raise RateLimitError("429", "API 호출 한도 초과")
                await asyncio.sleep(
                    float(resp.headers.get("Retry-After", self.retry_delay * (2 ** attempt)))
                )
                continue
            self._cb_failures = 0
            return _parse_response(resp)
        raise RateLimitError("429", "API 호출 한도 초과")

    async def get(self, path: str, params: dict, tr_id: str) -> dict:
        return await self._request("get", path, tr_id, params=params)

    async def post(self, path: str, body: dict, tr_id: str) -> dict:
        return await self._request("post", path, tr_id, json=body)

    async def close(self):
        await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()

"""비동기 KIS 클라이언트"""

import asyncio

import httpx

from kis.auth import Env, _base_url, get_token_async
from kis.errors import RateLimitError, raise_for_code


class AsyncKIS:
    __slots__ = ("app_key", "app_secret", "account", "env", "max_retries", "retry_delay", "_client")

    def __init__(self, app_key: str, app_secret: str, account: str, env: Env = "paper",
                 max_retries: int = 3, retry_delay: float = 1.0):
        self.app_key, self.app_secret, self.account = app_key, app_secret, account
        self.env, self.max_retries, self.retry_delay = env, max_retries, retry_delay
        self._client = httpx.AsyncClient(base_url=_base_url(env), timeout=10.0)

    @property
    def is_paper(self) -> bool:
        return self.env == "paper"

    @property
    def account_params(self) -> dict:
        return {"CANO": self.account[:8], "ACNT_PRDT_CD": self.account[9:11]}

    def switch(self, env: Env) -> "AsyncKIS":
        return AsyncKIS(self.app_key, self.app_secret, self.account, env, self.max_retries, self.retry_delay)

    async def _headers(self, tr_id: str) -> dict:
        return {
            "authorization": f"Bearer {await get_token_async(self.app_key, self.app_secret, self.env)}",
            "appkey": self.app_key, "appsecret": self.app_secret,
            "tr_id": tr_id, "content-type": "application/json; charset=utf-8",
        }

    async def _request(self, method: str, path: str, tr_id: str, **kwargs) -> dict:
        for attempt in range(self.max_retries + 1):
            resp = await getattr(self._client, method)(path, headers=await self._headers(tr_id), **kwargs)
            if resp.status_code != 429:
                resp.raise_for_status()
                data = resp.json()
                if data.get("rt_cd") != "0":
                    raise_for_code(data.get("msg_cd", "UNKNOWN"), data.get("msg1", "Unknown error"))
                return data.get("output", data)
            if attempt == self.max_retries:
                raise RateLimitError("429", "API 호출 한도 초과")
            await asyncio.sleep(float(resp.headers.get("Retry-After", self.retry_delay * (2**attempt))))
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

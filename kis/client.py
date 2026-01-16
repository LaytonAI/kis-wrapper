import httpx

from kis.auth import Env, _base_url, get_token


class APIError(Exception):
    pass


class KIS:
    __slots__ = ("app_key", "app_secret", "account", "env", "_client")

    def __init__(self, app_key: str, app_secret: str, account: str, env: Env = "paper"):
        self.app_key = app_key
        self.app_secret = app_secret
        self.account = account
        self.env = env
        self._client = httpx.Client(base_url=_base_url(env), timeout=10.0)

    @property
    def is_paper(self) -> bool:
        return self.env == "paper"

    @property
    def account_params(self) -> dict:
        return {"CANO": self.account[:8], "ACNT_PRDT_CD": self.account[9:11]}

    def switch(self, env: Env) -> "KIS":
        return KIS(self.app_key, self.app_secret, self.account, env)

    def _headers(self, tr_id: str) -> dict:
        return {
            "authorization": f"Bearer {get_token(self.app_key, self.app_secret, self.env)}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": tr_id,
            "content-type": "application/json; charset=utf-8",
        }

    def _request(self, method: str, path: str, tr_id: str, **kwargs) -> dict:
        resp = getattr(self._client, method)(path, headers=self._headers(tr_id), **kwargs)
        resp.raise_for_status()
        data = resp.json()
        if data.get("rt_cd") != "0":
            raise APIError(data.get("msg1", "Unknown error"))
        return data.get("output", data)

    def get(self, path: str, params: dict, tr_id: str) -> dict:
        return self._request("get", path, tr_id, params=params)

    def post(self, path: str, body: dict, tr_id: str) -> dict:
        return self._request("post", path, tr_id, json=body)

    def close(self):
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

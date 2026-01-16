import time
from typing import Literal

import httpx

Env = Literal["prod", "paper"]
_tokens: dict[tuple[str, str], tuple[str, float]] = {}
_async_client: httpx.AsyncClient | None = None

_URLS = {
    "prod": "https://openapi.koreainvestment.com:9443",
    "paper": "https://openapivts.koreainvestment.com:29443",
}


def _base_url(env: Env) -> str:
    return _URLS[env]


def _issue_token(app_key: str, app_secret: str, env: Env) -> tuple[str, float]:
    resp = httpx.post(
        f"{_base_url(env)}/oauth2/tokenP",
        json={"grant_type": "client_credentials", "appkey": app_key, "appsecret": app_secret},
    )
    data = resp.raise_for_status().json()
    return data["access_token"], time.time() + data["expires_in"] - 60


def get_token(app_key: str, app_secret: str, env: Env = "prod") -> str:
    key = (env, app_key)
    if key in _tokens and _tokens[key][1] > time.time() + 60:
        return _tokens[key][0]
    _tokens[key] = _issue_token(app_key, app_secret, env)
    return _tokens[key][0]


def get_ws_key(app_key: str, app_secret: str, env: Env = "prod") -> str:
    resp = httpx.post(
        f"{_base_url(env)}/oauth2/Approval",
        json={"grant_type": "client_credentials", "appkey": app_key, "secretkey": app_secret},
    )
    return resp.raise_for_status().json()["approval_key"]


async def _get_async_client() -> httpx.AsyncClient:
    global _async_client
    if _async_client is None:
        _async_client = httpx.AsyncClient()
    return _async_client


async def _issue_token_async(app_key: str, app_secret: str, env: Env) -> tuple[str, float]:
    client = await _get_async_client()
    resp = await client.post(
        f"{_base_url(env)}/oauth2/tokenP",
        json={"grant_type": "client_credentials", "appkey": app_key, "appsecret": app_secret},
    )
    data = resp.raise_for_status().json()
    return data["access_token"], time.time() + data["expires_in"] - 60


async def get_token_async(app_key: str, app_secret: str, env: Env = "prod") -> str:
    key = (env, app_key)
    if key in _tokens and _tokens[key][1] > time.time() + 60:
        return _tokens[key][0]
    _tokens[key] = await _issue_token_async(app_key, app_secret, env)
    return _tokens[key][0]


async def get_ws_key_async(app_key: str, app_secret: str, env: Env = "prod") -> str:
    client = await _get_async_client()
    resp = await client.post(
        f"{_base_url(env)}/oauth2/Approval",
        json={"grant_type": "client_credentials", "appkey": app_key, "secretkey": app_secret},
    )
    return resp.raise_for_status().json()["approval_key"]

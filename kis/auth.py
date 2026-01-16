import time
from typing import Literal

import httpx

Env = Literal["prod", "paper"]
_tokens: dict[tuple[str, str], tuple[str, float]] = {}

_URLS = {"prod": "https://openapi.koreainvestment.com:9443", "paper": "https://openapivts.koreainvestment.com:29443"}


def _base_url(env: Env) -> str:
    return _URLS[env]


def _issue_token(app_key: str, app_secret: str, env: Env) -> tuple[str, float]:
    """Issue new access token from KIS API."""
    data = httpx.post(
        f"{_base_url(env)}/oauth2/tokenP",
        json={"grant_type": "client_credentials", "appkey": app_key, "appsecret": app_secret},
    ).raise_for_status().json()
    return data["access_token"], time.time() + data["expires_in"] - 60


def get_token(app_key: str, app_secret: str, env: Env = "prod") -> str:
    """Return cached token or issue new one."""
    key = (env, app_key)
    if key in _tokens and _tokens[key][1] > time.time() + 60:
        return _tokens[key][0]
    _tokens[key] = _issue_token(app_key, app_secret, env)
    return _tokens[key][0]


def get_ws_key(app_key: str, app_secret: str, env: Env = "prod") -> str:
    """Get WebSocket approval key."""
    return httpx.post(
        f"{_base_url(env)}/oauth2/Approval",
        json={"grant_type": "client_credentials", "appkey": app_key, "secretkey": app_secret},
    ).raise_for_status().json()["approval_key"]

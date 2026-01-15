import time
from typing import Literal

import httpx

Env = Literal["prod", "paper"]

_tokens: dict[tuple[str, str], tuple[str, float]] = {}


def _base_url(env: Env) -> str:
    return {
        "prod": "https://openapi.koreainvestment.com:9443",
        "paper": "https://openapivts.koreainvestment.com:29443",
    }[env]


def get_token(app_key: str, app_secret: str, env: Env = "prod") -> str:
    """Return cached token or issue new one."""
    key = (env, app_key)
    if key in _tokens:
        token, expires_at = _tokens[key]
        if expires_at > time.time() + 60:  # 1분 여유
            return token

    token, expires_at = _issue_token(app_key, app_secret, env)
    _tokens[key] = (token, expires_at)
    return token


def _issue_token(app_key: str, app_secret: str, env: Env) -> tuple[str, float]:
    """Issue new access token from KIS API."""
    resp = httpx.post(
        f"{_base_url(env)}/oauth2/tokenP",
        json={
            "grant_type": "client_credentials",
            "appkey": app_key,
            "appsecret": app_secret,
        },
    )
    resp.raise_for_status()
    data = resp.json()
    return data["access_token"], time.time() + data["expires_in"] - 60


def get_ws_key(app_key: str, app_secret: str, env: Env = "prod") -> str:
    """Get WebSocket approval key."""
    resp = httpx.post(
        f"{_base_url(env)}/oauth2/Approval",
        json={"grant_type": "client_credentials", "appkey": app_key, "secretkey": app_secret},
    )
    resp.raise_for_status()
    return resp.json()["approval_key"]

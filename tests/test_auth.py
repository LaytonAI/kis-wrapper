import time
from unittest.mock import patch

import pytest

from kis import auth


@pytest.fixture(autouse=True)
def clear_tokens():
    auth._tokens.clear()


def test_base_url():
    assert auth._base_url("prod") == "https://openapi.koreainvestment.com:9443"
    assert auth._base_url("paper") == "https://openapivts.koreainvestment.com:29443"


def test_get_token_caches():
    with patch.object(auth, "_issue_token", return_value=("token123", time.time() + 3600)) as mock:
        t1 = auth.get_token("key", "secret", "paper")
        t2 = auth.get_token("key", "secret", "paper")

        assert t1 == t2 == "token123"
        assert mock.call_count == 1


def test_get_token_refreshes_expired():
    with patch.object(auth, "_issue_token", return_value=("new_token", time.time() + 3600)) as mock:
        auth._tokens[("paper", "key")] = ("old_token", time.time() - 100)
        assert auth.get_token("key", "secret", "paper") == "new_token"
        mock.assert_called_once()


def test_get_token_different_env():
    with patch.object(auth, "_issue_token") as mock:
        mock.side_effect = [("paper_token", time.time() + 3600), ("prod_token", time.time() + 3600)]

        assert auth.get_token("key", "secret", "paper") == "paper_token"
        assert auth.get_token("key", "secret", "prod") == "prod_token"
        assert mock.call_count == 2


def test_issue_token(httpx_mock):
    httpx_mock.add_response(json={"access_token": "test_token", "expires_in": 86400})
    token, expires_at = auth._issue_token("key", "secret", "paper")

    assert token == "test_token"
    assert expires_at > time.time()


def test_get_ws_key(httpx_mock):
    httpx_mock.add_response(json={"approval_key": "ws_key_123"})
    assert auth.get_ws_key("key", "secret", "paper") == "ws_key_123"

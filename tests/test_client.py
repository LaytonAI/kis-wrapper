from unittest.mock import patch

import pytest

from kis.client import KIS, APIError


def test_init_and_switch():
    kis = KIS("key", "secret", "12345678-01")
    assert kis.is_paper

    prod = kis.switch("prod")
    assert not prod.is_paper
    assert prod.app_key == kis.app_key
    assert kis.is_paper  # original unchanged


@patch("kis.client.get_token", return_value="test_token")
def test_headers(_, kis):
    headers = kis._headers("TR001")

    assert headers["authorization"] == "Bearer test_token"
    assert headers["appkey"] == "test_key"
    assert headers["tr_id"] == "TR001"


@patch("kis.client.get_token", return_value="test_token")
def test_get_success(_, kis, httpx_mock):
    httpx_mock.add_response(json={"rt_cd": "0", "output": {"price": "70000"}})
    assert kis.get("/test", {}, "TR001") == {"price": "70000"}


@patch("kis.client.get_token", return_value="test_token")
def test_post_success(_, kis, httpx_mock):
    httpx_mock.add_response(json={"rt_cd": "0", "output": {"order_no": "123"}})
    assert kis.post("/order", {"qty": 10}, "TR002") == {"order_no": "123"}


@patch("kis.client.get_token", return_value="test_token")
def test_api_error(_, kis, httpx_mock):
    httpx_mock.add_response(json={"rt_cd": "1", "msg1": "Invalid request"})

    with pytest.raises(APIError, match="Invalid request"):
        kis.get("/test", {}, "TR001")


def test_context_manager():
    with KIS("key", "secret", "12345678-01") as kis:
        assert kis.app_key == "key"

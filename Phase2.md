# Phase 2: Core (auth, client)

## 목표
- 토큰 발급/갱신 구현
- HTTP 클라이언트 구현
- 모의/실전 환경 전환

## 2.1 auth.py - 토큰 관리

### 설계 원칙
- 함수 중심 (클래스 없음)
- 모듈 레벨 캐싱
- 자동 갱신

### 인터페이스
```python
# kis/auth.py
from typing import Literal

Env = Literal["prod", "paper"]

# 모듈 레벨 캐시: (env, app_key) -> (token, expires_at)
_tokens: dict[tuple[str, str], tuple[str, float]] = {}

def get_token(app_key: str, app_secret: str, env: Env = "prod") -> str:
    """토큰 반환 (캐시 or 새로 발급)"""
    ...

def _issue_token(app_key: str, app_secret: str, env: Env) -> tuple[str, float]:
    """토큰 발급 API 호출"""
    ...

def get_ws_key(app_key: str, app_secret: str, env: Env = "prod") -> str:
    """WebSocket 접속키 발급"""
    ...

def _base_url(env: Env) -> str:
    """환경별 Base URL"""
    return {
        "prod": "https://openapi.koreainvestment.com:9443",
        "paper": "https://openapivts.koreainvestment.com:29443",
    }[env]
```

### 테스트 먼저 (TDD)
```python
# tests/test_auth.py
import pytest
from unittest.mock import patch
from kis import auth

def test_get_token_caches():
    """토큰이 캐싱되는지 확인"""
    with patch.object(auth, '_issue_token') as mock:
        mock.return_value = ("token123", time.time() + 3600)

        t1 = auth.get_token("key", "secret", "paper")
        t2 = auth.get_token("key", "secret", "paper")

        assert t1 == t2
        assert mock.call_count == 1  # 한 번만 호출

def test_get_token_refreshes_expired():
    """만료된 토큰은 갱신"""
    ...

def test_base_url():
    assert auth._base_url("prod") == "https://openapi.koreainvestment.com:9443"
    assert auth._base_url("paper") == "https://openapivts.koreainvestment.com:29443"
```

## 2.2 client.py - KIS 클래스

### 설계 원칙
- 유일한 상태 클래스
- 간단한 인터페이스
- 환경 전환 용이

### 인터페이스
```python
# kis/client.py
import httpx
from kis.auth import get_token, _base_url, Env

class KIS:
    """KIS API 클라이언트"""

    __slots__ = ("app_key", "app_secret", "account", "env", "_client")

    def __init__(
        self,
        app_key: str,
        app_secret: str,
        account: str,
        env: Env = "paper"
    ):
        self.app_key = app_key
        self.app_secret = app_secret
        self.account = account
        self.env = env
        self._client = httpx.Client(base_url=_base_url(env), timeout=10.0)

    def switch(self, env: Env) -> "KIS":
        """환경 전환 (새 인스턴스)"""
        return KIS(self.app_key, self.app_secret, self.account, env)

    @property
    def is_paper(self) -> bool:
        return self.env == "paper"

    def _headers(self, tr_id: str) -> dict:
        """공통 헤더 생성"""
        token = get_token(self.app_key, self.app_secret, self.env)
        return {
            "authorization": f"Bearer {token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": tr_id,
            "content-type": "application/json; charset=utf-8",
        }

    def get(self, path: str, params: dict, tr_id: str) -> dict:
        """GET 요청"""
        resp = self._client.get(path, params=params, headers=self._headers(tr_id))
        resp.raise_for_status()
        data = resp.json()
        if data.get("rt_cd") != "0":
            raise APIError(data.get("msg1", "Unknown error"))
        return data.get("output", data)

    def post(self, path: str, body: dict, tr_id: str) -> dict:
        """POST 요청"""
        resp = self._client.post(path, json=body, headers=self._headers(tr_id))
        resp.raise_for_status()
        data = resp.json()
        if data.get("rt_cd") != "0":
            raise APIError(data.get("msg1", "Unknown error"))
        return data.get("output", data)

    def close(self):
        """클라이언트 종료"""
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class APIError(Exception):
    """KIS API 에러"""
    pass
```

### 테스트
```python
# tests/test_client.py
import pytest
from kis.client import KIS, APIError

def test_switch_env():
    kis = KIS("key", "secret", "12345678-01", env="paper")
    assert kis.is_paper

    kis_prod = kis.switch("prod")
    assert not kis_prod.is_paper
    assert kis_prod.app_key == kis.app_key

def test_headers():
    kis = KIS("key", "secret", "12345678-01")
    headers = kis._headers("FHKST01010100")

    assert "authorization" in headers
    assert headers["tr_id"] == "FHKST01010100"

@pytest.fixture
def mock_response():
    return {"rt_cd": "0", "output": {"price": "70000"}}

def test_get_success(kis, mock_response, httpx_mock):
    httpx_mock.add_response(json=mock_response)
    result = kis.get("/test", {}, "TR001")
    assert result == {"price": "70000"}
```

## 2.3 types.py - 타입 정의

```python
# kis/types.py
from typing import TypedDict, Literal

class TokenResponse(TypedDict):
    access_token: str
    token_type: str
    expires_in: int

class PriceOutput(TypedDict):
    stck_prpr: str      # 현재가
    prdy_vrss: str      # 전일대비
    prdy_ctrt: str      # 전일대비율
    acml_vol: str       # 누적거래량

OrderSide = Literal["buy", "sell"]
OrderType = Literal["limit", "market"]
```

## 완료 조건
- [x] test_auth.py 작성 및 통과
- [x] auth.py 구현
- [x] test_client.py 작성 및 통과
- [x] client.py 구현
- [x] types.py 기본 타입 정의
- [x] 모의투자 환경에서 토큰 발급 테스트 (mock 테스트로 대체)

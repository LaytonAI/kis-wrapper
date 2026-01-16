__version__ = "0.3.0"

from kis import calc, domestic, overseas, snapshot
from kis.async_client import AsyncKIS
from kis.auth import Env, get_token, get_token_async, get_ws_key, get_ws_key_async
from kis.client import KIS
from kis.errors import (
    AccessDeniedError,
    AuthError,
    CircuitBreakerError,
    GatewayError,
    InsufficientBalanceError,
    KISError,
    MarketClosedError,
    NetworkError,
    OrderError,
    RateLimitError,
    SubscribeError,
    SymbolError,
    TokenExpiredError,
    WebSocketError,
)
from kis.types import Exchange
from kis.ws import WSClient

__all__ = [
    # Core
    "KIS", "AsyncKIS", "Env", "Exchange",
    "get_token", "get_token_async", "get_ws_key", "get_ws_key_async",
    "WSClient",
    # Modules
    "domestic", "overseas", "calc", "snapshot",
    # Errors - Gateway (EGW)
    "KISError", "GatewayError", "AuthError", "TokenExpiredError",
    "RateLimitError", "NetworkError", "CircuitBreakerError", "AccessDeniedError",
    # Errors - Business (APBK)
    "OrderError", "SymbolError", "MarketClosedError", "InsufficientBalanceError",
    # Errors - WebSocket (OPSP)
    "WebSocketError", "SubscribeError",
]

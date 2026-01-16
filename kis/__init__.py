__version__ = "0.2.0"

from kis import calc, domestic, overseas, snapshot
from kis.auth import Env, get_token, get_ws_key
from kis.client import KIS
from kis.errors import (
    AccessDeniedError,
    AuthError,
    GatewayError,
    InsufficientBalanceError,
    KISError,
    MarketClosedError,
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
    "KIS", "Env", "Exchange", "get_token", "get_ws_key", "WSClient",
    # Modules
    "domestic", "overseas", "calc", "snapshot",
    # Errors - Gateway (EGW)
    "KISError", "GatewayError", "AuthError", "TokenExpiredError",
    "RateLimitError", "AccessDeniedError",
    # Errors - Business (APBK)
    "OrderError", "SymbolError", "MarketClosedError", "InsufficientBalanceError",
    # Errors - WebSocket (OPSP)
    "WebSocketError", "SubscribeError",
]

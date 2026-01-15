from typing import Literal, TypedDict


class TokenResponse(TypedDict):
    access_token: str
    token_type: str
    expires_in: int


class PriceOutput(TypedDict):
    stck_prpr: str  # 현재가
    prdy_vrss: str  # 전일대비
    prdy_ctrt: str  # 전일대비율
    acml_vol: str  # 누적거래량


OrderSide = Literal["buy", "sell"]
OrderType = Literal["limit", "market"]

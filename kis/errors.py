"""KIS API 에러 정의"""


class KISError(Exception):
    """KIS API 에러 기본 클래스"""
    def __init__(self, code: str, message: str):
        self.code, self.message = code, message
        super().__init__(f"[{code}] {message}")


class RateLimitError(KISError): pass
class AuthError(KISError): pass
class TokenExpiredError(AuthError): pass
class OrderError(KISError): pass
class SymbolError(KISError): pass
class MarketClosedError(KISError): pass
class InsufficientBalanceError(KISError): pass


# 에러코드 매핑 (KIS API msg_cd -> 에러 클래스)
ERROR_MAP: dict[str, type[KISError]] = {
    # 인증
    "EGW00123": TokenExpiredError,
    "EGW00121": AuthError,
    # 주문
    "APBK0919": OrderError,  # 주문수량 초과
    "APBK0656": InsufficientBalanceError,  # 매수가능금액 부족
    "APBK0918": OrderError,  # 최소주문수량 미달
    "APBK1058": MarketClosedError,  # 주문가능시간 아님
    "APBK1663": OrderError,  # 해당 주문번호 없음
    # 종목
    "APBK0013": SymbolError,  # 종목코드 오류
    "APBK0634": SymbolError,  # 거래정지 종목
    # 기타
    "APBK0101": KISError,  # 시스템 오류
}


def raise_for_code(msg_cd: str, msg: str):
    """에러코드에 맞는 예외 발생"""
    err_class = ERROR_MAP.get(msg_cd, KISError)
    raise err_class(msg_cd, msg)

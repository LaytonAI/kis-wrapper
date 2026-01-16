class KISError(Exception):
    def __init__(self, code: str, message: str):
        self.code, self.message = code, message
        super().__init__(f"[{code}] {message}")


# Gateway 에러 (EGW)
class GatewayError(KISError):
    pass


class AuthError(GatewayError):
    pass


class TokenExpiredError(AuthError):
    pass


class RateLimitError(GatewayError):
    pass


class NetworkError(GatewayError):
    pass


class CircuitBreakerError(GatewayError):
    pass


class AccessDeniedError(GatewayError):
    pass


# 업무 에러 (APBK)
class OrderError(KISError):
    pass


class SymbolError(KISError):
    pass


class MarketClosedError(KISError):
    pass


class InsufficientBalanceError(KISError):
    pass


# WebSocket 에러 (OPSP)
class WebSocketError(KISError):
    pass


class SubscribeError(WebSocketError):
    pass


# 에러코드 매핑 (KIS API msg_cd -> 에러 클래스)
ERROR_MAP: dict[str, type[KISError]] = {
    # === EGW: Gateway 서버 ===
    "EGW00001": GatewayError,  # 일시적 오류
    "EGW00002": GatewayError,  # 서버 에러
    "EGW00003": AccessDeniedError,  # 접근 거부
    "EGW00004": AccessDeniedError,  # 권한 없음
    "EGW00101": GatewayError,  # 유효하지 않은 요청
    "EGW00103": AuthError,  # 유효하지 않은 AppKey
    "EGW00105": AuthError,  # 유효하지 않은 AppSecret
    "EGW00121": AuthError,  # 유효하지 않은 token
    "EGW00122": AuthError,  # token을 찾을 수 없음
    "EGW00123": TokenExpiredError,  # 기간 만료된 token
    "EGW00131": AuthError,  # 유효하지 않은 hashkey
    "EGW00201": RateLimitError,  # 초당 거래건수 초과
    "EGW00206": AccessDeniedError,  # API 사용 권한 없음
    "EGW00301": GatewayError,  # 연결 시간 초과
    "EGW00302": GatewayError,  # 거래 시간 초과
    # === APBK: 업무 처리 ===
    "APBK0013": SymbolError,  # 종목코드 오류
    "APBK0101": KISError,  # 시스템 오류
    "APBK0634": SymbolError,  # 거래정지 종목
    "APBK0656": InsufficientBalanceError,  # 매수가능금액 부족
    "APBK0918": OrderError,  # 최소주문수량 미달
    "APBK0919": OrderError,  # 주문수량 초과
    "APBK1058": MarketClosedError,  # 주문가능시간 아님
    "APBK1663": OrderError,  # 해당 주문번호 없음
    # === OPSP: WebSocket 서버 ===
    "OPSP0007": SubscribeError,  # 구독 내부 오류
    "OPSP0008": SubscribeError,  # 최대 구독 초과
    "OPSP8991": SubscribeError,  # 유효하지 않은 tr_id
    "OPSP8996": WebSocketError,  # 이미 사용 중인 appkey
}


def raise_for_code(msg_cd: str, msg: str):
    raise ERROR_MAP.get(msg_cd, KISError)(msg_cd, msg)

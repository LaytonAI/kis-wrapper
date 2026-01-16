"""국내주식 주문 예제"""

import os

from kis import KIS, domestic

kis = KIS(
    app_key=os.environ["KIS_APP_KEY"],
    app_secret=os.environ["KIS_APP_SECRET"],
    account=os.environ["KIS_ACCOUNT"],
    env="paper",
)

SYMBOL = "005930"  # 삼성전자

# 현재가 확인
price_info = domestic.price(kis, SYMBOL)
current_price = int(price_info["stck_prpr"])
print(f"현재가: {current_price:,}원")

# 매수 (지정가)
buy_price = current_price - 100  # 현재가보다 100원 낮게
order = domestic.buy(kis, SYMBOL, qty=1, price=buy_price)
order_no = order["ODNO"]
print(f"매수 주문: {order_no} ({buy_price:,}원 x 1주)")

# 미체결 확인
pending = domestic.pending_orders(kis)
print(f"미체결 주문: {len(pending)}건")

# 주문 정정 (가격 변경)
new_price = buy_price + 50
domestic.modify(kis, order_no, qty=1, price=new_price)
print(f"정정: {new_price:,}원으로 변경")

# 주문 취소
domestic.cancel(kis, order_no, qty=1)
print(f"취소: {order_no}")

# 시장가 매수 예제 (주석 처리)
# order = domestic.buy(kis, SYMBOL, qty=1)  # price=None이면 시장가
# print(f"시장가 매수: {order['ODNO']}")

# 전량 매도 예제 (보유시)
# try:
#     domestic.sell_all(kis, SYMBOL)
#     print(f"{SYMBOL} 전량 매도 완료")
# except ValueError as e:
#     print(f"매도 실패: {e}")

kis.close()

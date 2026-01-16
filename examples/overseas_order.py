"""해외주식 주문 예제"""

import os

from kis import KIS, overseas

kis = KIS(
    app_key=os.environ["KIS_APP_KEY"],
    app_secret=os.environ["KIS_APP_SECRET"],
    account=os.environ["KIS_ACCOUNT"],
    env="paper",
)

# 애플 현재가 (나스닥)
price_info = overseas.price(kis, "AAPL", "NAS")
print(f"AAPL: ${price_info['last']}")
print(f"전일대비: ${price_info['diff']} ({price_info['rate']}%)")

# 테슬라 일봉
candles = overseas.daily(kis, "TSLA", "NAS", period="D")
print(f"\nTSLA 최근 {len(candles)}일 데이터")
for c in candles[:3]:
    print(f"  {c['xymd']}: ${c['clos']}")

# 환율 조회
rate = overseas.exchange_rate(kis)
print(f"\nUSD 환율: {rate.get('frst_bltn_exrt', 'N/A')}원")

# 잔고 조회
balance = overseas.balance(kis)  # 전체
print(f"\n해외주식 잔고: {balance}")

# 매수 예제 (지정가)
# order = overseas.buy(kis, "AAPL", "NAS", qty=1, price=150.00)
# print(f"매수 주문: {order['ODNO']}")

# 매수 예제 (시장가 - 미국만 지원)
# order = overseas.buy(kis, "AAPL", "NAS", qty=1)
# print(f"시장가 매수: {order['ODNO']}")

# 거래소별 조회
exchanges = ["NAS", "NYS", "HKS", "TSE"]
for exch in exchanges:
    try:
        bal = overseas.balance(kis, exch)
        print(f"{exch}: {len(bal.get('output1', []))}종목")
    except Exception as e:
        print(f"{exch}: 조회 실패 - {e}")

kis.close()

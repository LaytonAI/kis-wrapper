"""기본 사용 예제"""

import os

from kis import KIS, domestic

# 환경변수에서 인증정보 로드
kis = KIS(
    app_key=os.environ["KIS_APP_KEY"],
    app_secret=os.environ["KIS_APP_SECRET"],
    account=os.environ["KIS_ACCOUNT"],
    env="paper",  # 모의투자
)

# 삼성전자 현재가
price = domestic.price(kis, "005930")
print(f"삼성전자 현재가: {price['stck_prpr']}원")
print(f"전일대비: {price['prdy_vrss']}원 ({price['prdy_ctrt']}%)")

# 호가 조회
orderbook = domestic.orderbook(kis, "005930")
print(f"\n매도1호가: {orderbook['askp1']}원")
print(f"매수1호가: {orderbook['bidp1']}원")

# 일봉 데이터
candles = domestic.daily(kis, "005930")
print(f"\n최근 일봉 {len(candles)}개")
for c in candles[:3]:
    print(f"  {c['stck_bsop_date']}: 종가 {c['stck_clpr']}원")

# 잔고 조회
balance = domestic.balance(kis)
print(f"\n예수금: {balance.get('dnca_tot_amt', 0)}원")

# 보유종목
positions = domestic.positions(kis)
if positions:
    print("\n보유종목:")
    for p in positions:
        print(f"  {p['prdt_name']}: {p['hldg_qty']}주")
else:
    print("\n보유종목 없음")

kis.close()

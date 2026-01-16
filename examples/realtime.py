"""실시간 데이터 수신 예제"""

import asyncio
import os

from kis import KIS, WSClient


async def main():
    kis = KIS(
        app_key=os.environ["KIS_APP_KEY"],
        app_secret=os.environ["KIS_APP_SECRET"],
        account=os.environ["KIS_ACCOUNT"],
        env="paper",
    )

    ws = WSClient(kis, max_retries=3)

    # 체결가 콜백
    async def on_price(data: dict):
        print(f"[체결] {data['symbol']}: {data['price']:,}원 (거래량: {data['volume']})")

    # 호가 콜백
    async def on_orderbook(data: dict):
        print(f"[호가] {data['symbol']}: 매도1 {data.get('ask1', 0):,} / 매수1 {data.get('bid1', 0):,}")

    # 구독
    symbols = ["005930", "000660"]  # 삼성전자, SK하이닉스
    await ws.subscribe("H0STCNT0", symbols, on_price)
    await ws.subscribe("H0STASP0", symbols, on_orderbook)
    print(f"구독 시작: {symbols}")

    # 실행 (Ctrl+C로 종료)
    try:
        await ws.run()
    except KeyboardInterrupt:
        print("\n종료...")
    finally:
        await ws.close()


if __name__ == "__main__":
    asyncio.run(main())

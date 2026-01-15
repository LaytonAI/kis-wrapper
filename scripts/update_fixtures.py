#!/usr/bin/env python3
"""모의투자 환경에서 실제 응답을 fixture로 저장

사용법:
    uv run python scripts/update_fixtures.py

환경변수 필요:
    KIS_APP_KEY, KIS_APP_SECRET, KIS_ACCOUNT
"""

import json
import os
from pathlib import Path

from kis import KIS, domestic


def update_fixtures():
    app_key = os.environ.get("KIS_APP_KEY")
    app_secret = os.environ.get("KIS_APP_SECRET")
    account = os.environ.get("KIS_ACCOUNT")

    if not all([app_key, app_secret, account]):
        print("환경변수 필요: KIS_APP_KEY, KIS_APP_SECRET, KIS_ACCOUNT")
        return

    kis = KIS(app_key, app_secret, account, env="paper")
    fixtures = Path(__file__).parent.parent / "tests/fixtures/domestic"
    fixtures.mkdir(parents=True, exist_ok=True)

    symbols = ["005930", "000660", "035720"]

    # 현재가
    for symbol in symbols:
        print(f"Fetching price for {symbol}...")
        data = domestic.price(kis, symbol)
        with open(fixtures / f"price_{symbol}.json", "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    # 호가
    for symbol in symbols:
        print(f"Fetching orderbook for {symbol}...")
        data = domestic.orderbook(kis, symbol)
        with open(fixtures / f"orderbook_{symbol}.json", "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    # 잔고
    print("Fetching balance...")
    data = domestic.balance(kis)
    with open(fixtures / "balance.json", "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print("Done!")


if __name__ == "__main__":
    update_fixtures()

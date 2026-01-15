# Phase 4: 데이터 무결성

## 목표
- 스냅샷 저장/검증 시스템
- 계산 검증 (API vs 자체 계산)
- 테스트 fixture 자동 생성

## 설계 원칙
- 모든 데이터는 검증 가능해야 함
- API 반환값을 맹신하지 않음
- 계산은 우리쪽에서도 수행

## 4.1 스냅샷 시스템

### 인터페이스
```python
# kis/snapshot.py
import hashlib
import json
import time
from pathlib import Path
from typing import Any

def snapshot(kis: "KIS", symbol: str) -> dict:
    """특정 시점의 데이터 스냅샷 생성

    Returns:
        {
            "timestamp": 1234567890.123,
            "symbol": "005930",
            "price": {...},
            "orderbook": {...},
            "balance": {...},
            "checksum": "abc123..."
        }
    """
    from kis import domestic

    data = {
        "timestamp": time.time(),
        "symbol": symbol,
        "price": domestic.price(kis, symbol),
        "orderbook": domestic.orderbook(kis, symbol),
        "balance": domestic.balance(kis),
    }
    data["checksum"] = _checksum(data)
    return data

def _checksum(data: dict) -> str:
    """체크섬 계산 (checksum 필드 제외)"""
    d = {k: v for k, v in data.items() if k != "checksum"}
    raw = json.dumps(d, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]

def verify(snapshot: dict) -> bool:
    """스냅샷 무결성 검증"""
    return snapshot.get("checksum") == _checksum(snapshot)

def save(snapshot: dict, path: Path | str) -> None:
    """스냅샷 파일 저장"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(snapshot, f, indent=2, ensure_ascii=False)

def load(path: Path | str) -> dict:
    """스냅샷 파일 로드"""
    with open(path) as f:
        return json.load(f)
```

### 테스트
```python
# tests/test_snapshot.py
from kis import snapshot

def test_checksum_consistency():
    data = {"a": 1, "b": 2}
    c1 = snapshot._checksum(data)
    c2 = snapshot._checksum(data)
    assert c1 == c2

def test_checksum_changes_on_modification():
    data = {"a": 1}
    c1 = snapshot._checksum(data)
    data["a"] = 2
    c2 = snapshot._checksum(data)
    assert c1 != c2

def test_verify_valid_snapshot():
    data = {"timestamp": 123, "symbol": "005930", "price": {"a": 1}}
    data["checksum"] = snapshot._checksum(data)
    assert snapshot.verify(data)

def test_verify_tampered_snapshot():
    data = {"timestamp": 123, "symbol": "005930", "price": {"a": 1}}
    data["checksum"] = snapshot._checksum(data)
    data["price"]["a"] = 999  # 변조
    assert not snapshot.verify(data)
```

## 4.2 계산 검증

### 인터페이스
```python
# kis/calc.py
from decimal import Decimal, ROUND_DOWN

def profit_rate(buy_price: int, current_price: int) -> Decimal:
    """수익률 계산

    Returns:
        Decimal: 수익률 (예: 0.05 = 5%)
    """
    if buy_price == 0:
        return Decimal(0)
    return (Decimal(current_price) - Decimal(buy_price)) / Decimal(buy_price)

def profit_amount(buy_price: int, current_price: int, qty: int) -> int:
    """수익금 계산"""
    return (current_price - buy_price) * qty

def avg_price(orders: list[dict]) -> int:
    """평균단가 계산

    Args:
        orders: [{"price": 70000, "qty": 10}, {"price": 71000, "qty": 5}]
    """
    total_amount = sum(o["price"] * o["qty"] for o in orders)
    total_qty = sum(o["qty"] for o in orders)
    if total_qty == 0:
        return 0
    return int(total_amount / total_qty)

def total_value(positions: list[dict]) -> int:
    """총 평가금액 계산"""
    return sum(int(p.get("evlu_amt", 0)) for p in positions)

def total_profit(positions: list[dict]) -> int:
    """총 수익금 계산"""
    return sum(int(p.get("evlu_pfls_amt", 0)) for p in positions)

def verify_balance(balance: dict, positions: list[dict]) -> bool:
    """잔고 데이터 검증 (API값 vs 계산값)"""
    api_total = int(balance.get("tot_evlu_amt", 0))
    calc_total = total_value(positions)

    # 1원 미만 오차 허용
    return abs(api_total - calc_total) < 1
```

### 테스트
```python
# tests/test_calc.py
from decimal import Decimal
from kis import calc

def test_profit_rate():
    assert calc.profit_rate(70000, 77000) == Decimal("0.1")
    assert calc.profit_rate(70000, 63000) == Decimal("-0.1")

def test_profit_rate_zero_division():
    assert calc.profit_rate(0, 100) == Decimal(0)

def test_avg_price():
    orders = [
        {"price": 70000, "qty": 10},
        {"price": 72000, "qty": 10},
    ]
    assert calc.avg_price(orders) == 71000

def test_avg_price_weighted():
    orders = [
        {"price": 70000, "qty": 10},  # 700,000
        {"price": 80000, "qty": 5},   # 400,000
    ]
    # (700000 + 400000) / 15 = 73333.33...
    assert calc.avg_price(orders) == 73333
```

## 4.3 테스트 Fixture 관리

### 구조
```
tests/fixtures/
├── domestic/
│   ├── price_005930.json
│   ├── orderbook_005930.json
│   └── balance.json
├── overseas/
│   └── price_AAPL.json
└── snapshots/
    └── 20240101_005930.json
```

### Fixture 자동 생성 스크립트
```python
# scripts/update_fixtures.py
"""모의투자 환경에서 실제 응답을 fixture로 저장"""
import json
from pathlib import Path
from kis import KIS, domestic

def update_fixtures():
    kis = KIS.from_env(env="paper")
    fixtures = Path("tests/fixtures/domestic")
    fixtures.mkdir(parents=True, exist_ok=True)

    # 현재가
    for symbol in ["005930", "000660", "035720"]:
        data = domestic.price(kis, symbol)
        with open(fixtures / f"price_{symbol}.json", "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    # 잔고
    data = domestic.balance(kis)
    with open(fixtures / "balance.json", "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    update_fixtures()
```

### conftest.py
```python
# tests/conftest.py
import json
import pytest
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"

@pytest.fixture
def price_fixture():
    with open(FIXTURES / "domestic/price_005930.json") as f:
        return json.load(f)

@pytest.fixture
def balance_fixture():
    with open(FIXTURES / "domestic/balance.json") as f:
        return json.load(f)

@pytest.fixture
def kis():
    """테스트용 KIS 클라이언트 (mock)"""
    from unittest.mock import MagicMock
    kis = MagicMock()
    kis.account = "12345678-01"
    kis.is_paper = True
    return kis
```

## 완료 조건
- [ ] test_snapshot.py 작성/통과
- [ ] snapshot.py 구현
- [ ] test_calc.py 작성/통과
- [ ] calc.py 구현
- [ ] fixtures 디렉토리 구조 생성
- [ ] update_fixtures.py 스크립트 작성
- [ ] conftest.py fixture 설정

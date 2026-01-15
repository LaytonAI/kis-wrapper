"""스냅샷 저장/검증 시스템"""

import hashlib
import json
import time
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kis.client import KIS


def snapshot(kis: "KIS", symbol: str) -> dict:
    """특정 시점의 데이터 스냅샷 생성"""
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


def verify(data: dict) -> bool:
    """스냅샷 무결성 검증"""
    return data.get("checksum") == _checksum(data)


def save(data: dict, path: Path | str) -> None:
    """스냅샷 파일 저장"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load(path: Path | str) -> dict:
    """스냅샷 파일 로드"""
    with open(path) as f:
        return json.load(f)

import hashlib
import json
import time
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kis.client import KIS


def snapshot(kis: "KIS", symbol: str) -> dict:
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
    d = {k: v for k, v in data.items() if k != "checksum"}
    return hashlib.sha256(json.dumps(d, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[
        :16
    ]


def verify(data: dict) -> bool:
    return data.get("checksum") == _checksum(data)


def save(data: dict, path: Path | str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load(path: Path | str) -> dict:
    with open(path) as f:
        return json.load(f)

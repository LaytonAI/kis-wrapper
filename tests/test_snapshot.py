"""snapshot.py 테스트"""

import tempfile
from pathlib import Path

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


def test_checksum_key_order_independent():
    d1 = {"a": 1, "b": 2}
    d2 = {"b": 2, "a": 1}
    assert snapshot._checksum(d1) == snapshot._checksum(d2)


def test_verify_valid_snapshot():
    data = {"timestamp": 123, "symbol": "005930", "price": {"a": 1}}
    data["checksum"] = snapshot._checksum(data)
    assert snapshot.verify(data)


def test_verify_tampered_snapshot():
    data = {"timestamp": 123, "symbol": "005930", "price": {"a": 1}}
    data["checksum"] = snapshot._checksum(data)
    data["price"]["a"] = 999  # 변조
    assert not snapshot.verify(data)


def test_verify_missing_checksum():
    data = {"timestamp": 123, "symbol": "005930"}
    assert not snapshot.verify(data)


def test_save_and_load():
    data = {"timestamp": 123, "symbol": "005930", "price": {"a": 1}}
    data["checksum"] = snapshot._checksum(data)

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "test.json"
        snapshot.save(data, path)
        loaded = snapshot.load(path)
        assert loaded == data
        assert snapshot.verify(loaded)


def test_save_creates_parent_dirs():
    data = {"a": 1}
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "nested" / "dir" / "test.json"
        snapshot.save(data, path)
        assert path.exists()

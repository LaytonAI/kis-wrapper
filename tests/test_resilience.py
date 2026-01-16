from collections import deque

from kis.resilience import CB_CLOSED, CB_HALF_OPEN, CB_OPEN, cb_on_failure, cb_state, throttle_wait


# === Throttle Tests ===


def test_throttle_under_limit():
    ts = deque()
    assert throttle_wait(ts, 20, 1000.0) == 0.0
    assert len(ts) == 1


def test_throttle_at_limit():
    # 20 requests in last 0.95 seconds (all within 1-sec window)
    ts = deque([999.05 + i * 0.05 for i in range(20)])  # 999.05 ~ 1000.0
    wait = throttle_wait(ts, 20, 1000.0)
    assert wait > 0  # 999.05 + 1.0 - 1000.0 = 0.05
    assert wait < 1.0


def test_throttle_disabled():
    ts = deque()
    assert throttle_wait(ts, 0, 1000.0) == 0.0
    assert len(ts) == 0


def test_throttle_cleans_old_timestamps():
    ts = deque([990.0, 990.5, 999.5])  # 2 old, 1 recent
    assert throttle_wait(ts, 20, 1000.0) == 0.0
    assert len(ts) == 2  # old ones removed, new one added


# === Circuit Breaker Tests ===


def test_cb_state_closed():
    assert cb_state(0, 5, 0.0, 1000.0) == CB_CLOSED
    assert cb_state(4, 5, 0.0, 1000.0) == CB_CLOSED


def test_cb_state_open():
    assert cb_state(5, 5, 1100.0, 1000.0) == CB_OPEN


def test_cb_state_half_open():
    assert cb_state(5, 5, 900.0, 1000.0) == CB_HALF_OPEN


def test_cb_state_disabled():
    assert cb_state(100, 0, 1100.0, 1000.0) == CB_CLOSED


def test_cb_on_failure_under_threshold():
    failures, open_until = cb_on_failure(2, 5, 30.0, 1000.0)
    assert failures == 3
    assert open_until == 0.0


def test_cb_on_failure_at_threshold():
    failures, open_until = cb_on_failure(4, 5, 30.0, 1000.0)
    assert failures == 5
    assert open_until == 1030.0

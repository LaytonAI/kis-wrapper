"""Resilience utilities: throttle & circuit breaker."""

from collections import deque

# Circuit breaker states
CB_CLOSED, CB_OPEN, CB_HALF_OPEN = 0, 1, 2


def throttle_wait(ts: deque, rate: int, now: float) -> float:
    """Return seconds to wait (0 if ok). Mutates ts deque."""
    if rate <= 0:
        return 0.0
    # Remove timestamps outside 1-second window
    cutoff = now - 1.0
    while ts and ts[0] < cutoff:
        ts.popleft()
    if len(ts) < rate:
        ts.append(now)
        return 0.0
    return ts[0] + 1.0 - now


def cb_state(failures: int, threshold: int, open_until: float, now: float) -> int:
    """Return circuit breaker state."""
    if threshold <= 0 or failures < threshold:
        return CB_CLOSED
    return CB_OPEN if now < open_until else CB_HALF_OPEN


def cb_on_failure(failures: int, threshold: int, recovery: float, now: float) -> tuple[int, float]:
    """Record failure. Returns (new_failures, new_open_until)."""
    failures += 1
    return (failures, now + recovery) if failures >= threshold else (failures, 0.0)

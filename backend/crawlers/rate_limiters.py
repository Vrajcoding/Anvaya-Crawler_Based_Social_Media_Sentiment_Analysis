"""
rate_limiters.py — Token-bucket rate limiters for each social platform.
Prevents bans by honouring conservative per-platform request ceilings.
"""
from __future__ import annotations
import asyncio
import time
from typing import Dict


class TokenBucketRateLimiter:
    """
    Classic token-bucket implementation.
    Tokens refill at `rate` per second up to `capacity`.
    Each call to `acquire()` consumes one token; if empty it waits.
    """

    def __init__(self, rate: float, capacity: float):
        """
        Args:
            rate:     Tokens added per second  (e.g. 5.0 → 300 RPM)
            capacity: Max burst size (tokens)
        """
        self._rate = rate
        self._capacity = capacity
        self._tokens = capacity
        self._last_refill: float = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Block until a token is available, then consume it."""
        async with self._lock:
            self._refill()
            if self._tokens < 1:
                wait_time = (1 - self._tokens) / self._rate
                await asyncio.sleep(wait_time)
                self._refill()
            self._tokens -= 1

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self._capacity, self._tokens + elapsed * self._rate)
        self._last_refill = now


# ── Platform Rate-Limit Presets (conservative defaults per v2.1 spec) ──────
#  RPM   → tokens per second = RPM / 60
#
#  X:              300 RPM → 5.0 tok/s
#  YouTube:         40 RPM → 0.67 tok/s
#  Instagram:       20 RPM → 0.33 tok/s
#  GoogleSuggest:  100 RPM → 1.67 tok/s
#  Web:             60 RPM → 1.0 tok/s

_PLATFORM_CONFIGS: Dict[str, Dict[str, float]] = {
    "X":             {"rate": 5.0,  "capacity": 10.0},
    "YouTube":       {"rate": 0.67, "capacity": 4.0},
    "Instagram":     {"rate": 0.33, "capacity": 3.0},
    "GoogleSuggest": {"rate": 1.67, "capacity": 8.0},
    "Web":           {"rate": 1.0,  "capacity": 5.0},
}

_limiters: Dict[str, TokenBucketRateLimiter] = {}


def get_limiter(platform: str) -> TokenBucketRateLimiter:
    """Return the shared rate-limiter instance for a given platform (lazy init)."""
    global _limiters
    if platform not in _limiters:
        cfg = _PLATFORM_CONFIGS.get(platform, {"rate": 1.0, "capacity": 5.0})
        _limiters[platform] = TokenBucketRateLimiter(**cfg)
    return _limiters[platform]

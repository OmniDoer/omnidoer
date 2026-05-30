"""Small rate limiter for pairing and session endpoints."""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class RateLimitBucket:
    attempts: list[float] = field(default_factory=list)
    locked_until: float = 0.0


class RateLimiter:
    def __init__(self, *, max_attempts: int = 5, window_seconds: int = 60, lockout_seconds: int = 300):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.lockout_seconds = lockout_seconds
        self._buckets: dict[str, RateLimitBucket] = {}

    def check(self, key: str, now: float | None = None) -> None:
        now = now or time.time()
        bucket = self._buckets.setdefault(key, RateLimitBucket())
        if bucket.locked_until > now:
            raise PermissionError("rate limit locked")
        bucket.attempts = [item for item in bucket.attempts if item >= now - self.window_seconds]
        if len(bucket.attempts) >= self.max_attempts:
            bucket.locked_until = now + self.lockout_seconds
            raise PermissionError("rate limit exceeded")

    def record_failure(self, key: str, now: float | None = None) -> None:
        now = now or time.time()
        bucket = self._buckets.setdefault(key, RateLimitBucket())
        bucket.attempts = [item for item in bucket.attempts if item >= now - self.window_seconds]
        bucket.attempts.append(now)

    def clear(self, key: str) -> None:
        self._buckets.pop(key, None)

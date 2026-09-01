from __future__ import annotations

import time
from collections import defaultdict
from threading import Lock


class TestProbeRateLimitError(Exception):
    pass


class TestProbeRateLimiter:
    def __init__(self, *, max_requests_per_minute: int = 10) -> None:
        self._max = max(1, max_requests_per_minute)
        self._hits: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()

    def check(self, user_key: str) -> None:
        if not user_key:
            user_key = "anonymous"
        now = time.monotonic()
        with self._lock:
            window = [stamp for stamp in self._hits[user_key] if now - stamp < 60.0]
            if len(window) >= self._max:
                raise TestProbeRateLimitError(
                    "Limite de testes de conexão atingido (10 por minuto)."
                )
            window.append(now)
            self._hits[user_key] = window

    def reset_for_tests(self) -> None:
        with self._lock:
            self._hits.clear()


_default_limiter = TestProbeRateLimiter()


def get_test_probe_rate_limiter() -> TestProbeRateLimiter:
    return _default_limiter

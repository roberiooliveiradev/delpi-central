"""Shared rate-limit backends for external-data-api (X0 §7 freeze).

Dimensions: ``consumer`` (authenticated S2S client_id), ``cnpj``
(SHA-256 of the queried tax id — never stored raw) and ``global``
(aggregate cap protecting the community endpoint). ``acquire_many``
checks every dimension before recording any hit, so a denied dimension
never leaves partial quota consumption.

Strategies (``EXTERNAL_DATA_RATE_LIMIT_STRATEGY``):

- ``process_local`` — in-memory per-worker counters; only accepted when
  ``EXTERNAL_DATA_PROCESS_LOCAL_ALLOWED=true`` explicitly marks the
  deployment as single-worker/test.
- ``distributed`` — Redis fixed-window counters shared by all workers and
  replicas. One Lua script makes check-and-increment atomic; keys are
  namespaced and always carry a TTL. Redis failure or missing URL →
  ``LimiterUnavailableError`` (fail-closed, never queries upstream).

Any other strategy value resolves to the unavailable limiter — an
unknown value is never silently mapped to memory.
"""

from __future__ import annotations

import threading
import time
from collections import deque
from typing import Any, Callable, Iterable, Mapping

from app.application.contracts import LimiterUnavailableError, RateLimitedError
from app.infrastructure.config.settings import Settings

LimitEntry = tuple[str, str]

_RATE_LIMITED = 1

_ACQUIRE_LUA = """
local denied = -1
for i, k in ipairs(KEYS) do
  local cur = tonumber(redis.call('GET', k) or '0')
  if cur >= tonumber(ARGV[i]) then
    denied = i
    break
  end
end
if denied ~= -1 then
  local pttl = redis.call('PTTL', KEYS[denied])
  return {1, pttl}
end
for i, k in ipairs(KEYS) do
  local n = redis.call('INCR', k)
  if n == 1 then
    redis.call('PEXPIRE', k, tonumber(ARGV[#ARGV]))
  end
end
return {0, 0}
"""


def _default_limits() -> dict[str, int]:
    per_min = max(
        1, int(getattr(Settings, "EXTERNAL_DATA_MAX_QUERIES_PER_MINUTE", 10))
    )
    return {
        "consumer": per_min,
        "cnpj": per_min,
        "global": max(
            1,
            int(
                getattr(
                    Settings,
                    "EXTERNAL_DATA_GLOBAL_MAX_QUERIES_PER_MINUTE",
                    30,
                )
            ),
        ),
    }


class InMemoryRateLimiter:
    """Per-key fixed-window cap (process-local — single-worker only)."""

    def __init__(
        self,
        *,
        limit_per_minute: int | None = None,
        limits: Mapping[str, int] | None = None,
        window_seconds: float = 60.0,
        clock: Callable[[], float] | None = None,
    ):
        if limits is None:
            per_min = max(1, int(limit_per_minute or 10))
            limits = {"consumer": per_min, "cnpj": per_min, "global": per_min * 3}
        self._limits = {k: max(1, int(v)) for k, v in limits.items()}
        self._window = float(window_seconds)
        self._clock = clock or time.monotonic
        self._hits: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def acquire(self, dimension: str, ident: str) -> None:
        self.acquire_many([(dimension, ident)])

    def acquire_many(self, entries: Iterable[LimitEntry]) -> None:
        entries = list(entries)
        now = self._clock()
        with self._lock:
            states = []
            for dimension, ident in entries:
                key = f"{dimension}:{ident}"
                hits = self._hits.setdefault(key, deque())
                while hits and now - hits[0] >= self._window:
                    hits.popleft()
                states.append((hits, self._limits.get(dimension, 1)))
            for hits, limit in states:
                if len(hits) >= limit:
                    retry_after = int(self._window - (now - hits[0])) + 1
                    raise RateLimitedError(
                        "external data query limit reached",
                        retry_after=retry_after,
                    )
            for hits, _ in states:
                hits.append(now)


class RedisRateLimiter:
    """Distributed fixed-window limiter backed by the shared Redis URL.

    Atomicity: one Lua script checks all dimensions and only then
    increments — no GET→INCR→EXPIRE race, no partial quota consumption
    and no key ever lacks a TTL.
    """

    def __init__(
        self,
        *,
        redis_url: str,
        limits: Mapping[str, int] | None = None,
        window_seconds: float = 60.0,
        key_prefix: str | None = None,
        timeout_seconds: float | None = None,
        client: Any | None = None,
    ) -> None:
        self._limits = dict(limits or _default_limits())
        self._window_ms = max(1, int(float(window_seconds) * 1000))
        self._prefix = key_prefix or getattr(
            Settings,
            "EXTERNAL_DATA_RATE_LIMIT_PREFIX",
            "external-data:rate-limit:",
        )
        if client is not None:
            self._client = client
        else:
            if not redis_url:
                raise LimiterUnavailableError(
                    "distributed rate limiter configured but REDIS_URL is missing"
                )
            try:
                import redis
            except ImportError as exc:
                raise LimiterUnavailableError(
                    "redis client is not installed"
                ) from exc
            timeout = timeout_seconds or float(
                getattr(Settings, "EXTERNAL_DATA_REDIS_TIMEOUT_SECONDS", 1.5)
            )
            self._client = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_timeout=timeout,
                socket_connect_timeout=timeout,
            )
            try:
                self._client.ping()
            except Exception as exc:
                raise LimiterUnavailableError(
                    "distributed rate limiter backend unreachable"
                ) from exc

    def acquire(self, dimension: str, ident: str) -> None:
        self.acquire_many([(dimension, ident)])

    def acquire_many(self, entries: Iterable[LimitEntry]) -> None:
        entries = list(entries)
        keys = [f"{self._prefix}{dimension}:{ident}" for dimension, ident in entries]
        args = [self._limits.get(dimension, 1) for dimension, _ in entries]
        args.append(self._window_ms)
        try:
            result = self._client.eval(_ACQUIRE_LUA, len(keys), *keys, *args)
        except Exception as exc:
            raise LimiterUnavailableError(
                "distributed rate limiter backend error"
            ) from exc
        if int(result[0]) == _RATE_LIMITED:
            pttl = int(result[1] or 0)
            if pttl > 0:
                retry_after = pttl // 1000 + (1 if pttl % 1000 else 0)
            else:
                retry_after = int(self._window_ms / 1000)
            raise RateLimitedError(
                "external data query limit reached",
                retry_after=max(1, retry_after),
            )


class UnavailableRateLimiter:
    """Fail-closed limiter — raises on every check, no external query."""

    def __init__(self, reason: str) -> None:
        self._reason = reason

    def acquire(self, dimension: str, ident: str) -> None:
        raise LimiterUnavailableError(self._reason)

    def acquire_many(self, entries: Iterable[LimitEntry]) -> None:
        raise LimiterUnavailableError(self._reason)


def build_rate_limiter() -> Any:
    """Resolve the configured rate-limit backend (config-safety gate)."""
    strategy = getattr(
        Settings, "EXTERNAL_DATA_RATE_LIMIT_STRATEGY", "process_local"
    )
    if strategy == "distributed":
        try:
            return RedisRateLimiter(
                redis_url=getattr(Settings, "REDIS_URL", "")
            )
        except LimiterUnavailableError as exc:
            return UnavailableRateLimiter(str(exc))
        except Exception as exc:
            return UnavailableRateLimiter(
                f"distributed rate limiter init failed: {exc}"
            )
    if strategy == "process_local":
        if (
            getattr(Settings, "EXTERNAL_DATA_CNPJ_PROVIDER", "unavailable")
            == "brasilapi"
            and not getattr(
                Settings, "EXTERNAL_DATA_PROCESS_LOCAL_ALLOWED", False
            )
        ):
            return UnavailableRateLimiter(
                "brasilapi with process_local rate limiting requires an "
                "explicit single-worker opt-in "
                "(EXTERNAL_DATA_PROCESS_LOCAL_ALLOWED)"
            )
        return InMemoryRateLimiter(limits=_default_limits())
    return UnavailableRateLimiter(
        f"unknown external-data rate-limit strategy: {strategy}"
    )


_shared_limiter: Any = None
_shared_limiter_lock = threading.Lock()


def rate_limiter() -> Any:
    """Process-wide shared limiter — survives per-request instances."""
    global _shared_limiter
    if _shared_limiter is None:
        with _shared_limiter_lock:
            if _shared_limiter is None:
                _shared_limiter = build_rate_limiter()
    return _shared_limiter


def reset_rate_limiter() -> None:
    """Test hook — drop the cached limiter so config changes apply."""
    global _shared_limiter
    with _shared_limiter_lock:
        _shared_limiter = None

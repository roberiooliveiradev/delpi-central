"""Shared rate-limit backends for the company-registry provider (S3.2).

Dimensions: ``actor`` (per EffectiveUser.id), ``cnpj`` (per queried tax id —
hashed before storage) and ``global`` (aggregate service cap protecting the
community endpoint). All limiter implementations expose ``acquire`` /
``acquire_many``; ``acquire_many`` checks every dimension before recording
any hit so a denied dimension never leaves partial quota consumption
behind.

Strategies (``COMPANY_REGISTRY_RATE_LIMIT_STRATEGY``):

- ``process_local`` — in-memory per-worker counters; only safe for
  single-worker/test deployments.
- ``distributed`` — Redis fixed-window counters shared by all workers and
  replicas. A single Lua script makes check-and-increment atomic; keys are
  namespaced and always carry a TTL. Redis failure or missing URL →
  ``RegistryLimiterUnavailableError`` (fail-closed, never queries upstream).
"""

from __future__ import annotations

import threading
import time
from collections import deque
from typing import Any, Callable, Iterable, Mapping

from app.application.services.supplier_enrichment.contracts import (
    RegistryLimiterUnavailableError,
    RegistryRateLimitedError,
)
from app.infrastructure.config.settings import Settings

# (dimension, identifier) pair — e.g. ("actor", uuid), ("cnpj", sha256[:20])
LimitEntry = tuple[str, str]

_RATE_LIMITED = 1
_ALLOWED = 0

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
        1, int(getattr(Settings, "COMPANY_REGISTRY_MAX_QUERIES_PER_MINUTE", 10))
    )
    return {
        "actor": per_min,
        "cnpj": per_min,
        "global": max(
            1,
            int(
                getattr(
                    Settings, "COMPANY_REGISTRY_GLOBAL_MAX_QUERIES_PER_MINUTE", 30
                )
            ),
        ),
    }


class InMemoryRegistryRateLimiter:
    """Per-key fixed-window query cap (process-local).

    Limitation: state lives in this process — protection is not shared
    across workers/replicas. Use ``distributed`` strategy for multiworker.
    """

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
            limits = {"actor": per_min, "cnpj": per_min, "global": per_min * 3}
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
                    raise RegistryRateLimitedError(
                        "company registry query limit reached",
                        retry_after=retry_after,
                    )
            for hits, _ in states:
                hits.append(now)

    # Backwards-compatible single-key API (kept for existing call sites).
    def check(self, key: str) -> None:
        dimension, _, ident = key.partition(":")
        self.acquire(dimension, ident)


class RedisRegistryRateLimiter:
    """Distributed fixed-window limiter backed by the shared Redis URL.

    Atomicity: one Lua script checks all dimensions and only then
    increments — no GET→INCR→EXPIRE race, no partial quota consumption and
    no key ever lacks a TTL.
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
            Settings, "COMPANY_REGISTRY_RATE_LIMIT_PREFIX",
            "supplies:registry-rate-limit:",
        )
        if client is not None:
            self._client = client
        else:
            if not redis_url:
                raise RegistryLimiterUnavailableError(
                    "distributed rate limiter configured but REDIS_URL is missing"
                )
            try:
                import redis
            except ImportError as exc:
                raise RegistryLimiterUnavailableError(
                    "redis client is not installed"
                ) from exc
            self._client = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_timeout=timeout_seconds
                or float(
                    getattr(Settings, "COMPANY_REGISTRY_REDIS_TIMEOUT_SECONDS", 1.5)
                ),
                socket_connect_timeout=timeout_seconds
                or float(
                    getattr(Settings, "COMPANY_REGISTRY_REDIS_TIMEOUT_SECONDS", 1.5)
                ),
            )
            try:
                self._client.ping()
            except Exception as exc:
                raise RegistryLimiterUnavailableError(
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
            raise RegistryLimiterUnavailableError(
                "distributed rate limiter backend error"
            ) from exc
        if int(result[0]) == _RATE_LIMITED:
            pttl = int(result[1] or 0)
            retry_after = max(1, pttl // 1000 + (1 if pttl % 1000 else 0)) if pttl > 0 else int(self._window_ms / 1000)
            raise RegistryRateLimitedError(
                "company registry query limit reached",
                retry_after=retry_after,
            )

    def check(self, key: str) -> None:
        dimension, _, ident = key.partition(":")
        self.acquire(dimension, ident)


class UnavailableRegistryRateLimiter:
    """Fail-closed limiter — raises on every check, no external query."""

    def __init__(self, reason: str) -> None:
        self._reason = reason

    def acquire(self, dimension: str, ident: str) -> None:
        raise RegistryLimiterUnavailableError(self._reason)

    def acquire_many(self, entries: Iterable[LimitEntry]) -> None:
        raise RegistryLimiterUnavailableError(self._reason)

    def check(self, key: str) -> None:
        raise RegistryLimiterUnavailableError(self._reason)


def build_registry_rate_limiter() -> Any:
    """Resolve the configured rate-limit backend.

    ``process_local`` → shared in-memory limiter (single-worker only).
    ``distributed`` → Redis limiter; any construction failure degrades to
    ``UnavailableRegistryRateLimiter`` so an enabled BrasilAPI can never
    leak past an unavailable limiter.
    """
    strategy = getattr(Settings, "COMPANY_REGISTRY_RATE_LIMIT_STRATEGY", "process_local")
    if strategy == "distributed":
        try:
            return RedisRegistryRateLimiter(redis_url=getattr(Settings, "REDIS_URL", ""))
        except RegistryLimiterUnavailableError as exc:
            return UnavailableRegistryRateLimiter(str(exc))
        except Exception as exc:
            return UnavailableRegistryRateLimiter(
                f"distributed rate limiter init failed: {exc}"
            )
    return InMemoryRegistryRateLimiter(limits=_default_limits())

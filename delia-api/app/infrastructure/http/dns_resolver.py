"""Bounded DNS resolver for governed outbound HTTP.

C3-INTELLIGENCE-LOOP-03R2A-R5 — ARCHITECTURE_DECISION_DNS_DEADLINE =
APPROVED, DNS_STRATEGY = BOUNDED_RESOLVER_EXECUTOR, owner DÉLIA
Infrastructure.

``socket.getaddrinfo`` is a single blocking libc call that cannot be
interrupted inside the caller's thread. The approved exception — and
the ONLY detached work allowed in this stack — submits exactly that
one lookup to a process-scoped bounded worker pool while the caller
waits at most its own remaining absolute deadline.

Hard invariants:

* The worker receives ONLY (host, port, family, socktype) — never
  tokens, headers, bodies, payloads or business identifiers.
* The worker NEVER connects — it can only produce address
  candidates for the caller.
* A result arriving after the caller deadline is DISCARDED: zero
  TCP connect, zero TLS, zero HTTP, zero PREPARE/ACT — the caller
  already returned a truthful timeout.
* Capacity is structurally bounded: fixed worker count + an
  admission semaphore covering running + queued jobs. Saturation
  fails fast — never enqueue forever, never spawn more threads.

Capacity constants: 4 workers / 8 outstanding jobs covers the
governed fan-out profile (a handful of concurrent provider calls
per turn, each resolving once) with margin, while keeping a DNS
storm strictly finite. They are infrastructure constants, not
operational config — the Abstraction Gate does not justify a new
setting for this phase.

Shutdown: ``ThreadPoolExecutor`` registers its own atexit join, so
process shutdown waits for in-flight resolutions — in practice
bounded by OS resolver behavior, but an absolute process-shutdown
bound is NOT_PROVEN (recorded residual); queued jobs are cancelled
best-effort via ``cancel_futures`` on shutdown. ``future.cancel()``
only stops jobs that have not started; a running ``getaddrinfo``
finishes and its result is discarded (real semantics, not
pretended).
"""

from __future__ import annotations

import socket
import threading
import time
from concurrent.futures import (
    CancelledError,
    ThreadPoolExecutor,
    TimeoutError as FutureTimeoutError,
)

MAX_DNS_RESOLVER_WORKERS = 4
# running + queued must never exceed this cap
MAX_DNS_RESOLVER_OUTSTANDING = 8


class DnsResolverSaturatedError(Exception):
    """Resolver capacity exhausted — fail closed, never enqueue."""


class BoundedDnsResolver:
    """Process-scoped bounded executor exclusively for getaddrinfo."""

    def __init__(
        self,
        max_workers: int = MAX_DNS_RESOLVER_WORKERS,
        max_outstanding: int = MAX_DNS_RESOLVER_OUTSTANDING,
    ) -> None:
        if max_workers <= 0 or max_outstanding <= 0:
            raise ValueError("resolver limits must be positive")
        self._pool = ThreadPoolExecutor(
            max_workers=max_workers, thread_name_prefix="delia-dns"
        )
        # Admission gate: one slot per outstanding job — released by
        # the future's done callback so running + queued <= capacity
        # even after the caller has given up on a slow lookup.
        self._slots = threading.BoundedSemaphore(max_outstanding)

    def resolve(
        self,
        host: str,
        port: int,
        family: int,
        socktype: int,
        deadline: float,
    ) -> list:
        """Resolve under the caller's remaining absolute deadline.

        Raises ``socket.timeout`` on deadline expiry (the caller's
        own budget — a timed-out lookup never retries with a fresh
        window) and ``DnsResolverSaturatedError`` when capacity is
        exhausted. ``gaierror`` propagates unchanged so the caller's
        NameResolutionError mapping stays truthful.
        """
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise socket.timeout("dns resolution deadline exceeded")
        if not self._slots.acquire(blocking=False):
            raise DnsResolverSaturatedError("dns resolver saturated")
        try:
            future = self._pool.submit(
                socket.getaddrinfo, host, port, family, socktype
            )
        except BaseException:
            self._slots.release()
            raise
        future.add_done_callback(lambda _f: self._slots.release())
        try:
            return future.result(timeout=remaining)
        except FutureTimeoutError as exc:
            # Queued-but-not-started jobs are cancelled; a running
            # getaddrinfo cannot be killed and is allowed to finish
            # — its late result is simply discarded here.
            future.cancel()
            raise socket.timeout(
                "dns resolution deadline exceeded"
            ) from exc
        except CancelledError as exc:  # pragma: no cover
            raise socket.timeout("dns resolution cancelled") from exc


_RESOLVER: BoundedDnsResolver | None = None
_RESOLVER_LOCK = threading.Lock()


def dns_resolver() -> BoundedDnsResolver:
    """ONE process-scoped resolver — never one per request."""
    global _RESOLVER
    if _RESOLVER is None:
        with _RESOLVER_LOCK:
            if _RESOLVER is None:
                _RESOLVER = BoundedDnsResolver()
    return _RESOLVER

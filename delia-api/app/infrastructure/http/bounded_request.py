"""Total wall-clock bound for one HTTP request.

C3-INTELLIGENCE-LOOP-03R2A-R2: ``requests`` applies a scalar
``timeout`` per socket recv — a server that trickles bytes keeps the
call alive past any configured timeout. This primitive enforces a
TOTAL wall-clock duration: the response body is streamed and a
monotonic deadline is re-checked between reads, with the in-flight
socket timeout tightened to the remaining budget so a mid-body stall
cannot outlive the deadline by more than one read slice.

LOOP-03R2A-R3: the absolute deadline is also installed via
``deadline_scope`` so that status-line/header parsing (which happens
inside ``send``) cannot renew the window — see
``app/infrastructure/http/deadline_transport.py`` for the socket-level
enforcement that makes the deadline TRULY absolute pre-body.

Provider-neutral infrastructure only — callers map the bounded
errors to their own truthful semantics. No secrets, payloads or
argument values are logged here.
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

import requests

from app.infrastructure.http.deadline_transport import deadline_scope

# One recv slice bounds how long a single socket read can stall while
# the chunked drain enforces the total deadline.
_READ_SLICE_SECONDS = 0.5
_BODY_CHUNK_BYTES = 65536
DEFAULT_MAX_BODY_BYTES = 4 * 1024 * 1024


class BoundedHttpTimeout(Exception):
    """The request could not complete inside the granted budget."""


class BoundedHttpTransportError(Exception):
    """The request failed below the deadline (unreachable, reset)."""


class BoundedHttpTooLarge(Exception):
    """The response exceeded the caller's bounded size limit."""


@dataclass(frozen=True, slots=True)
class BoundedHttpResponse:
    """Materialized response: status + bounded body, already drained."""

    status_code: int
    content: bytes
    headers: Mapping[str, str]

    @property
    def text(self) -> str:
        return self.content.decode("utf-8", errors="replace")

    def json(self) -> Any:
        return json.loads(self.content)


def bounded_request(
    send: Callable[..., Any],
    url: str,
    *,
    timeout_seconds: float,
    max_body_bytes: int = DEFAULT_MAX_BODY_BYTES,
    clock: Callable[[], float] = time.monotonic,
    **send_kwargs: Any,
) -> BoundedHttpResponse:
    """Issue one request bounded by a TOTAL wall-clock deadline.

    ``send`` is the transport callable — ``requests.get``/``post`` in
    production, an injected stub in tests — invoked as
    ``send(url, timeout=(connect, read_slice), stream=True, ...)``.
    ``timeout_seconds <= 0`` fails fast with zero wire calls — an
    explicit non-positive bound never opens a fresh window.
    """
    timeout = float(timeout_seconds)
    if timeout <= 0:
        raise BoundedHttpTimeout("no request budget remains")
    deadline = clock() + timeout
    response = None
    try:
        # The absolute deadline is bound thread-locally BEFORE send —
        # deadline-wrapped sockets then enforce it during connect,
        # status-line and header parsing, not just body drain.
        with deadline_scope(deadline):
            response = send(
                url,
                timeout=(timeout, min(timeout, _READ_SLICE_SECONDS)),
                stream=True,
                **send_kwargs,
            )
            body = _drain_body(
                response, deadline, max_body_bytes, clock
            )
    except (
        BoundedHttpTimeout,
        BoundedHttpTransportError,
        BoundedHttpTooLarge,
    ):
        raise
    except requests.exceptions.Timeout as exc:
        raise BoundedHttpTimeout(
            "request exceeded its wall-clock deadline"
        ) from exc
    except requests.exceptions.RequestException as exc:
        raise BoundedHttpTransportError(
            "request transport failed"
        ) from exc
    finally:
        close = getattr(response, "close", None)
        if callable(close):
            close()
    if clock() >= deadline:
        raise BoundedHttpTimeout(
            "request exceeded its wall-clock deadline"
        )
    return BoundedHttpResponse(
        status_code=int(getattr(response, "status_code", 0) or 0),
        content=body,
        headers=dict(getattr(response, "headers", None) or {}),
    )


def _drain_body(
    response: Any,
    deadline: float,
    max_body_bytes: int,
    clock: Callable[[], float],
) -> bytes:
    """Drain the streamed body under the absolute deadline."""
    if clock() >= deadline:
        raise BoundedHttpTimeout("no request budget remains")
    raw = getattr(response, "raw", None)
    read1 = getattr(raw, "read1", None)
    if not callable(read1):
        # Test stubs materialize the body already — the deadline
        # check above still bounds the total duration.
        content = getattr(response, "content", None)
        if isinstance(content, (bytes, bytearray)):
            body = bytes(content)
        else:
            body = str(getattr(response, "text", "") or "").encode()
        if len(body) > max_body_bytes:
            raise BoundedHttpTooLarge("response exceeds the size limit")
        return body
    chunks = bytearray()
    while True:
        remaining = deadline - clock()
        if remaining <= 0:
            raise BoundedHttpTimeout(
                "response exceeded its wall-clock deadline"
            )
        _tighten_socket_timeout(response, remaining)
        try:
            chunk = read1(_BODY_CHUNK_BYTES)
        except Exception as exc:
            raise (
                BoundedHttpTimeout(
                    "response exceeded its wall-clock deadline"
                )
                if clock() >= deadline or isinstance(exc, TimeoutError)
                else BoundedHttpTransportError(
                    "response failed mid-body"
                )
            ) from exc
        if not chunk:
            break
        chunks += chunk
        if len(chunks) > max_body_bytes:
            raise BoundedHttpTooLarge(
                "response exceeds the size limit"
            )
    return bytes(chunks)


def _tighten_socket_timeout(response: Any, remaining: float) -> None:
    """Best-effort shrink of the in-flight socket timeout.

    With ``stream=True`` the per-recv timeout was fixed at request
    time; tightening it to the remaining budget makes a stalled recv
    abort exactly at the deadline. Guarded — the socket chain is a
    urllib3 implementation detail and the read-slice bound stands
    regardless.
    """
    try:
        raw = response.raw
        fp = getattr(getattr(raw, "_fp", None), "fp", None)
        sock = getattr(getattr(fp, "raw", None), "_sock", None)
        if sock is None:
            sock = getattr(fp, "_sock", None)
        if sock is not None:
            sock.settimeout(max(0.05, float(remaining)))
    except (AttributeError, OSError, ValueError):
        return

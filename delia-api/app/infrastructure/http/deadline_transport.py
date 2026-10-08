"""Absolute-deadline transport for governed outbound HTTP.

LOOP-03R2A-R3: ``requests``/``urllib3`` timeout semantics are per-recv
INACTIVITY bounds — including ``urllib3.Timeout(total=...)``, which
recomputes the remaining budget only at phase boundaries urllib3
controls. Inside ``http.client`` status-line/header parsing the socket
keeps one fixed timeout per recv, so a server trickling fragments can
renew the window forever and outlive the caller's absolute deadline
(probed: ``Timeout(total=0.4)`` took 3.7s against a 0.1s-fragment
status line).

This module closes the gap WITHOUT threads, detached work, a custom
HTTP stack or a new dependency: a socket proxy re-tightens the real
socket timeout to ``deadline - monotonic()`` before every blocking
operation. The kernel-level recv itself expires at the absolute
deadline inside the caller's own thread — status line, headers and
body are all covered, and nothing survives a timeout detached.

urllib3 connection subclasses install the proxy on the final
transport socket (TLS wrapped or plain), so pooling, proxy env,
redirects and certificate verification stay owned by requests/urllib3.
A contextvar carries the per-request absolute deadline — the send
callables below are drop-in replacements for ``requests.get``/
``requests.post`` at the existing injection seams, with identical
fresh-session semantics (no cross-request cookie state).
"""

from __future__ import annotations

import io
import socket
import time
from contextvars import ContextVar
from typing import Any, Callable

import requests
from requests.adapters import HTTPAdapter
from urllib3.connection import HTTPConnection, HTTPSConnection
from urllib3.connectionpool import (
    HTTPConnectionPool,
    HTTPSConnectionPool,
)
from urllib3.poolmanager import PoolManager

# Smallest positive socket timeout — used when the deadline already
# expired so the next blocking op aborts ~immediately instead of
# becoming a non-blocking error or a fresh full window.
_EPSILON_SECONDS = 0.001

_CURRENT_DEADLINE: ContextVar[float | None] = ContextVar(
    "delia_http_absolute_deadline", default=None
)


def current_deadline() -> float | None:
    """Absolute monotonic deadline governing the in-flight request."""
    return _CURRENT_DEADLINE.get()


class deadline_scope:
    """Bind an absolute monotonic deadline to this thread's request."""

    def __init__(self, deadline: float | None) -> None:
        self._deadline = deadline
        self._token: Any = None

    def __enter__(self) -> "deadline_scope":
        self._token = _CURRENT_DEADLINE.set(self._deadline)
        return self

    def __exit__(self, *exc: Any) -> None:
        _CURRENT_DEADLINE.reset(self._token)


class _DeadlineSocket:
    """Socket proxy enforcing ONE absolute deadline on every read/write.

    ``http.client`` parses the status line and headers through
    ``sock.makefile`` — each buffered ``recv_into`` here first clamps
    the real socket timeout to the remaining budget, so a fragment
    arriving inside the window still counts against the SAME deadline.
    When the deadline expires the next op raises ``TimeoutError``
    (``socket.timeout``) immediately, inside the caller's thread — the
    request genuinely terminates; the socket is unusable afterwards
    and gets closed by the caller's error path.
    """

    def __init__(
        self,
        sock: socket.socket,
        deadline_getter: Callable[[], float | None],
    ) -> None:
        object.__setattr__(self, "_sock", sock)
        object.__setattr__(self, "_deadline_getter", deadline_getter)
        # socket.SocketIO bookkeeping compatibility: makefile() files
        # ref through the WRAPPER, so close() must defer the real
        # close until they detach — same contract as socket's _io_refs.
        object.__setattr__(self, "_io_refs", 0)
        object.__setattr__(self, "_closed_want", False)

    def _remaining(self) -> float | None:
        deadline = self._deadline_getter()
        if deadline is None:
            return None
        return deadline - time.monotonic()

    def _tighten(self) -> None:
        remaining = self._remaining()
        if remaining is not None:
            self._sock.settimeout(max(remaining, _EPSILON_SECONDS))

    def recv_into(self, buffer: Any, nbytes: int = 0, flags: int = 0) -> int:
        remaining = self._remaining()
        if remaining is not None and remaining <= 0:
            raise TimeoutError("http absolute deadline exceeded")
        self._tighten()
        return self._sock.recv_into(buffer, nbytes, flags)

    def recv(self, bufsize: int, flags: int = 0) -> bytes:
        remaining = self._remaining()
        if remaining is not None and remaining <= 0:
            raise TimeoutError("http absolute deadline exceeded")
        self._tighten()
        return self._sock.recv(bufsize, flags)

    def send(self, data: bytes, flags: int = 0) -> int:
        self._tighten()
        return self._sock.send(data, flags)

    def sendall(self, data: bytes, flags: int = 0) -> None:
        self._tighten()
        return self._sock.sendall(data, flags)

    def makefile(self, mode: str = "r", *args: Any, **kwargs: Any) -> Any:
        """Binary read file whose every recv tightens to the deadline."""
        if "r" not in mode:
            raise ValueError("deadline socket only supports read files")
        raw = socket.SocketIO(self, "r")
        self._io_refs += 1
        buffering = kwargs.get("buffering")
        if buffering == 0:
            return raw
        return io.BufferedReader(raw, io.DEFAULT_BUFFER_SIZE)

    def _decref_socketios(self) -> None:
        self._io_refs -= 1
        if self._io_refs <= 0 and self._closed_want:
            self._sock.close()

    def _check_closed(self) -> None:
        pass

    @property
    def closed(self) -> bool:
        return bool(getattr(self._sock, "_closed", False))

    def close(self) -> None:
        self._closed_want = True
        if self._io_refs <= 0:
            self._sock.close()

    def shutdown(self, how: int) -> None:
        self._sock.shutdown(how)

    def __getattr__(self, name: str) -> Any:
        return getattr(object.__getattribute__(self, "_sock"), name)

    def __setattr__(self, name: str, value: Any) -> None:
        if name in (
            "_sock",
            "_deadline_getter",
            "_io_refs",
            "_closed_want",
        ):
            object.__setattr__(self, name, value)
        else:
            setattr(self._sock, name, value)


def _wrap_deadline_socket(conn: Any) -> None:
    if conn.sock is not None and not isinstance(conn.sock, _DeadlineSocket):
        conn.sock = _DeadlineSocket(conn.sock, current_deadline)


class _DeadlineHTTPConnection(HTTPConnection):
    """HTTPConnection whose transport socket honors the absolute
    deadline contextvar — every recv (status line, headers, body)
    re-tightens to the remaining budget."""

    def connect(self) -> None:
        super().connect()
        _wrap_deadline_socket(self)


class _DeadlineHTTPSConnection(HTTPSConnection):
    """Same deadline enforcement after urllib3's TLS wrap — the proxy
    covers the SSLSocket, so encrypted traffic is equally bounded.
    The TLS handshake itself runs under the connect-phase socket
    timeout (single-op bound; cert verification untouched)."""

    def connect(self) -> None:
        super().connect()
        _wrap_deadline_socket(self)


class _DeadlineHTTPConnectionPool(HTTPConnectionPool):
    ConnectionCls = _DeadlineHTTPConnection


class _DeadlineHTTPSConnectionPool(HTTPSConnectionPool):
    ConnectionCls = _DeadlineHTTPSConnection


class _DeadlinePoolManager(PoolManager):
    """PoolManager whose per-scheme pools yield deadline conns.

    Note: requests ``proxy_manager_for`` builds its own ``ProxyManager``
    for ``http(s)_proxy`` environments — connections routed THROUGH an
    explicit forward proxy are not deadline-wrapped. Governed DÉLIA
    calls reach internal endpoints directly; documented residual.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.pool_classes_by_scheme = {
            "http": _DeadlineHTTPConnectionPool,
            "https": _DeadlineHTTPSConnectionPool,
        }


class _DeadlineHTTPAdapter(HTTPAdapter):
    """requests adapter whose pools yield deadline-wrapped conns."""

    def init_poolmanager(
        self,
        connections: int,
        maxsize: int,
        block: bool = False,
        **pool_kwargs: Any,
    ) -> None:
        self.poolmanager = _DeadlinePoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            **pool_kwargs,
        )


def _deadline_session() -> requests.Session:
    session = requests.Session()
    adapter = _DeadlineHTTPAdapter()
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def deadline_http_get(
    url: str,
    *,
    headers: Any = None,
    timeout: Any = None,
    stream: Any = None,
    **kwargs: Any,
) -> requests.Response:
    """Drop-in for ``requests.get`` honoring the absolute deadline.

    Fresh session per call — identical semantics to ``requests.get``
    (no cookie/connection state carried between requests).
    """
    with _deadline_session() as session:
        return session.get(
            url, headers=headers, timeout=timeout, stream=stream, **kwargs
        )


def deadline_http_post(
    url: str,
    *,
    headers: Any = None,
    data: Any = None,
    timeout: Any = None,
    stream: Any = None,
    **kwargs: Any,
) -> requests.Response:
    """Drop-in for ``requests.post`` honoring the absolute deadline."""
    with _deadline_session() as session:
        return session.post(
            url,
            headers=headers,
            data=data,
            timeout=timeout,
            stream=stream,
            **kwargs,
        )

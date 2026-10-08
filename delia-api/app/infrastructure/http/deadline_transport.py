"""Absolute-deadline transport for governed outbound HTTP.

LOOP-03R2A-R3/R4: ``requests``/``urllib3`` timeout semantics are
per-recv INACTIVITY bounds — including ``urllib3.Timeout(total=...)``,
which recomputes the remaining budget only at phase boundaries
urllib3 controls. Inside ``http.client`` status-line/header parsing
and inside ``socket.create_connection``/TLS handshake the socket
keeps one fixed timeout per operation, so a peer trickling fragments
can renew the window forever and outlive the caller's absolute
deadline (probed: ``Timeout(total=0.4)`` took 3.7s against a
0.1s-fragment status line).

This module closes the gap WITHOUT threads, detached work, a custom
HTTP/TLS/DNS stack or a new dependency:

* ``_DeadlineSocket`` — socket proxy re-tightening the real socket
  timeout to ``deadline - monotonic()`` before every blocking op;
  expired deadline raises ``TimeoutError`` before touching the wire.
* ``_DeadlineHTTPConnection._new_conn`` — TCP connect iterates
  ``getaddrinfo`` results sharing ONE remaining budget across all
  address attempts (urllib3's ``create_connection`` would renew the
  full connect timeout per address).
* ``_DeadlineHTTPSConnection.connect`` — TLS handshake driven in
  non-blocking mode with ``select`` against the absolute deadline,
  so a peer trickling handshake bytes cannot renew inactivity
  windows. The SSLContext is built with urllib3's own helpers and
  certificate verification/matching is preserved verbatim.
* ``deadline_scope`` — contextvar carrying the per-request deadline;
  redirect chains share the same absolute deadline automatically.

urllib3, ``http.client``, TLS record handling, pooling, redirects and
certificate verification stay owned by the existing stack. The
kernel-level op itself expires at the absolute deadline inside the
caller's own thread — a timed-out request genuinely dies and nothing
continues detached.

DNS: ``socket.getaddrinfo`` cannot be interrupted in-thread — R5
routes it through ``dns_resolver``, a process-scoped bounded worker
pool (the one authorized detached-work exception). The caller waits
at most its remaining deadline; a late lookup result is discarded
with zero connect/TLS/HTTP side effects, and resolver capacity
(workers + outstanding) is structurally bounded so saturation fails
closed instead of queueing forever.

Forward proxies are disallowed fail-closed for governed calls:
deadline sessions use ``trust_env=False`` and deadline connections
raise if a proxy is configured — provider endpoints are direct-only
by contract (approved-specialist configuration only;
GOVERNED_HTTP_PROXY_POLICY = DIRECT_ONLY_CURRENT_SCOPE).
"""

from __future__ import annotations

import io
import select
import socket
import ssl
import sys
import time
from collections.abc import Callable
from contextvars import ContextVar
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.connection import (
    HTTPConnection,
    HTTPSConnection,
    _assert_fingerprint,
    _match_hostname,
    is_ipaddress,
)
from urllib3.connectionpool import (
    HTTPConnectionPool,
    HTTPSConnectionPool,
)
from urllib3.exceptions import (
    ConnectTimeoutError,
    LocationParseError,
    NameResolutionError,
    NewConnectionError,
    ProxyError,
)
from urllib3.poolmanager import PoolManager
from urllib3.util.connection import (
    _set_socket_options,
    allowed_gai_family,
)
from urllib3.util.ssl_ import (
    ALPN_PROTOCOLS,
    HAS_NEVER_CHECK_COMMON_NAME,
    IS_PYOPENSSL,
    create_urllib3_context,
    resolve_cert_reqs,
    resolve_ssl_version,
)

from app.infrastructure.http.dns_resolver import (
    DnsResolverSaturatedError,
    dns_resolver,
)

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


class BoundedHttpTransportPolicyError(requests.exceptions.RequestException):
    """A call violated the governed transport contract (e.g. proxy use).

    Subclassing ``RequestException`` keeps the fail-closed rejection on
    the existing transport-error mapping path (``bounded_request`` →
    ``BoundedHttpTransportError``), not an unexpected crash."""


def _remaining(deadline: float | None) -> float | None:
    if deadline is None:
        return None
    return deadline - time.monotonic()


def _raise_if_expired(deadline: float | None) -> None:
    """Fail fast with zero wire work when the budget is gone."""
    if deadline is not None and deadline - time.monotonic() <= 0:
        raise socket.timeout("http absolute deadline exceeded")


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
    ``send``/``sendall`` are symmetrically guarded: an expired
    deadline raises ``TimeoutError`` BEFORE any wire operation —
    fail-closed for future write-class execution too. When the
    deadline expires the next op raises inside the caller's thread;
    the socket is unusable afterwards and gets closed by the caller's
    error path. Nothing continues detached.
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

    def _remaining_budget(self) -> float | None:
        return _remaining(self._deadline_getter())

    def _tighten(self) -> None:
        remaining = self._remaining_budget()
        if remaining is not None:
            self._sock.settimeout(max(remaining, _EPSILON_SECONDS))

    def recv_into(self, buffer: Any, nbytes: int = 0, flags: int = 0) -> int:
        remaining = self._remaining_budget()
        if remaining is not None and remaining <= 0:
            raise TimeoutError("http absolute deadline exceeded")
        self._tighten()
        return self._sock.recv_into(buffer, nbytes, flags)

    def recv(self, bufsize: int, flags: int = 0) -> bytes:
        remaining = self._remaining_budget()
        if remaining is not None and remaining <= 0:
            raise TimeoutError("http absolute deadline exceeded")
        self._tighten()
        return self._sock.recv(bufsize, flags)

    def send(self, data: bytes, flags: int = 0) -> int:
        remaining = self._remaining_budget()
        if remaining is not None and remaining <= 0:
            raise TimeoutError("http absolute deadline exceeded")
        self._tighten()
        return self._sock.send(data, flags)

    def sendall(self, data: bytes, flags: int = 0) -> None:
        remaining = self._remaining_budget()
        if remaining is not None and remaining <= 0:
            raise TimeoutError("http absolute deadline exceeded")
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


class _BoundedConnectMixin:
    """Shared bounded ``_new_conn`` for HTTP and HTTPS deadline conns.

    ``_new_conn`` is a bounded variant of urllib3's
    ``create_connection``: a single ``getaddrinfo`` (post-checked — an
    expired budget yields ZERO connect attempts), then per-address
    ``connect`` with ``min(remaining, configured connect timeout)`` —
    multiple IPs share the caller's remainder instead of each getting
    a fresh window.
    """

    def _new_conn(self) -> socket.socket:
        if current_deadline() is None:
            return super()._new_conn()
        try:
            sock = self._bounded_connect()
        except socket.gaierror as exc:
            raise NameResolutionError(self.host, self, exc) from exc
        except socket.timeout as exc:
            raise ConnectTimeoutError(
                self,
                f"Connection to {self.host} timed out. "
                f"(connect timeout={self.timeout})",
            ) from exc
        except OSError as exc:
            raise NewConnectionError(
                self, f"Failed to establish a new connection: {exc}"
            ) from exc

        sys.audit("http.client.connect", self, self.host, self.port)
        return sock

    def _bounded_connect(self) -> socket.socket:
        """``urllib3.util.connection.create_connection`` under ONE
        absolute deadline shared by all resolved addresses."""
        deadline = current_deadline()
        assert deadline is not None

        host = self._dns_host
        port = self.port
        if host.startswith("["):
            host = host.strip("[]")
        family = allowed_gai_family()

        try:
            host.encode("idna")
        except UnicodeError:
            raise LocationParseError(
                f"'{host}', label empty or too long"
            ) from None

        # DNS resolution runs on the bounded resolver executor
        # (dns_resolver.py — the one authorized detached-work
        # exception): the caller waits at most its remaining deadline;
        # an expired budget yields ZERO connect attempts and the late
        # getaddrinfo result is discarded.
        try:
            resolved = dns_resolver().resolve(
                host, port, family, socket.SOCK_STREAM, deadline
            )
        except DnsResolverSaturatedError as exc:
            # Capacity exhausted — truthful timeout/unavailable, never
            # an unbounded queue.
            raise socket.timeout("dns resolver saturated") from exc
        _raise_if_expired(deadline)

        configured = self.timeout
        connect_cap = getattr(configured, "connect_timeout", configured)

        err: OSError | None = None
        for res in resolved:
            af, socktype, proto, _, sa = res
            sock = None
            try:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    # Expired between attempts — never give the next
                    # address a fresh window.
                    raise socket.timeout("http absolute deadline exceeded")
                sock = socket.socket(af, socktype, proto)
                _set_socket_options(sock, self.socket_options)
                attempt = remaining
                if connect_cap is not None:
                    attempt = min(remaining, float(connect_cap))
                sock.settimeout(attempt)
                if self.source_address:
                    sock.bind(self.source_address)
                sock.connect(sa)
                return sock
            except socket.timeout:
                raise
            except OSError as exc:
                err = exc
                if sock is not None:
                    sock.close()

        if err is not None:
            raise err
        raise OSError("getaddrinfo returns an empty list")


def _bounded_tls_handshake(ssl_sock: ssl.SSLSocket, deadline: float) -> None:
    """Drive a TLS handshake in non-blocking mode so the ABSOLUTE
    deadline applies — a peer trickling handshake bytes gets no
    inactivity renewal. Same thread, stdlib ssl + select only."""
    ssl_sock.settimeout(0.0)
    while True:
        try:
            ssl_sock.do_handshake()
            return
        except ssl.SSLWantReadError:
            events = select.POLLIN
        except ssl.SSLWantWriteError:
            events = select.POLLOUT
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise socket.timeout("http absolute deadline exceeded")
        poller = select.poll()
        poller.register(ssl_sock, events)
        poller.poll(int(remaining * 1000))


def _unwrapped(conn_sock: Any) -> socket.socket:
    return (
        conn_sock._sock if isinstance(conn_sock, _DeadlineSocket) else conn_sock
    )


class _DeadlineHTTPConnection(_BoundedConnectMixin, HTTPConnection):
    """HTTPConnection whose TCP connect and transport socket honor the
    absolute deadline contextvar. Forward-proxy paths are rejected
    fail-closed — governed transports never configure proxies.
    """

    def connect(self) -> None:
        _raise_if_expired(current_deadline())
        if self.proxy is not None:
            raise ProxyError(
                "forward proxies are unsupported on the governed "
                "deadline transport (direct endpoints only)",
                OSError("proxy usage rejected"),
            )
        super().connect()
        _wrap_deadline_socket(self)


class _DeadlineHTTPSConnection(_BoundedConnectMixin, HTTPSConnection):
    """HTTPSConnection whose TCP connect AND TLS handshake run under
    the absolute deadline contextvar.

    urllib3 wraps TLS inside ``connect()`` — so the R3 wrapper,
    installed after ``super().connect()``, never governed handshake
    recvs. This subclass drives ``do_handshake()`` non-blocking under
    the same deadline (loop + ``select``), reusing urllib3's own
    SSLContext construction and hostname/fingerprint verification.
    Forward-proxy paths are rejected fail-closed: governed transports
    never configure proxies (``trust_env=False`` sessions), so an
    unexpected proxy config is loud, never silently unbounded.
    """

    def connect(self) -> None:
        deadline = current_deadline()
        if deadline is None:
            super().connect()
            _wrap_deadline_socket(self)
            return
        if self.proxy is not None:
            raise ProxyError(
                "forward proxies are unsupported on the governed "
                "deadline transport (direct endpoints only)",
                OSError("proxy usage rejected"),
            )
        self._deadline_connect(deadline)

    def _deadline_connect(self, deadline: float) -> None:
        _raise_if_expired(deadline)

        # Bounded TCP connect (deadline shared across addresses; DNS
        # post-check before any connect attempt).
        self.sock = self._new_conn()
        server_hostname = (self.server_hostname or self.host).rstrip(".")

        # TLS context — same construction urllib3 applies in
        # _ssl_wrap_socket_and_match_hostname (verified params only:
        # cert_reqs/ssl version bounds/CA material/client certs/SNI).
        default_context = self.ssl_context is None
        context = self.ssl_context or create_urllib3_context(
            ssl_version=resolve_ssl_version(self.ssl_version),
            ssl_minimum_version=self.ssl_minimum_version,
            ssl_maximum_version=self.ssl_maximum_version,
            cert_reqs=resolve_cert_reqs(self.cert_reqs),
        )
        context.verify_mode = resolve_cert_reqs(self.cert_reqs)
        if (
            self.assert_fingerprint
            or self.assert_hostname
            or self.assert_hostname is False
            or IS_PYOPENSSL
            or not HAS_NEVER_CHECK_COMMON_NAME
        ):
            context.check_hostname = False
        if (
            not self.ca_certs
            and not self.ca_cert_dir
            and not self.ca_cert_data
            and default_context
            and hasattr(context, "load_default_certs")
        ):
            context.load_default_certs()
        if self.ca_certs or self.ca_cert_dir or self.ca_cert_data:
            context.load_verify_locations(
                self.ca_certs, self.ca_cert_dir, self.ca_cert_data
            )
        if self.cert_file:
            context.load_cert_chain(
                self.cert_file, self.key_file, self.key_password
            )
        context.set_alpn_protocols(ALPN_PROTOCOLS)

        normalized = server_hostname.strip("[]")
        if "%" in normalized:
            normalized = normalized[: normalized.rfind("%")]
        if is_ipaddress(normalized):
            server_hostname = normalized

        ssl_sock: ssl.SSLSocket | None = None
        try:
            ssl_sock = context.wrap_socket(
                _unwrapped(self.sock),
                server_hostname=server_hostname,
                do_handshake_on_connect=False,
            )
            _bounded_tls_handshake(ssl_sock, deadline)

            if self.assert_fingerprint:
                _assert_fingerprint(
                    ssl_sock.getpeercert(binary_form=True),
                    self.assert_fingerprint,
                )
            elif (
                context.verify_mode != ssl.CERT_NONE
                and not context.check_hostname
                and self.assert_hostname is not False
            ):
                cert = ssl_sock.getpeercert()
                hostname_checks_common_name = (
                    False
                    if default_context
                    else getattr(
                        context, "hostname_checks_common_name", False
                    )
                    or False
                )
                _match_hostname(
                    cert,
                    self.assert_hostname or server_hostname,
                    hostname_checks_common_name,
                )
        except BaseException:
            if ssl_sock is not None:
                ssl_sock.close()
            elif self.sock is not None:
                _unwrapped(self.sock).close()
            raise

        remaining = deadline - time.monotonic()
        if remaining <= 0:
            ssl_sock.close()
            raise socket.timeout("http absolute deadline exceeded")
        ssl_sock.settimeout(remaining)
        self.sock = _DeadlineSocket(ssl_sock, current_deadline)
        self.is_verified = context.verify_mode == ssl.CERT_REQUIRED or bool(
            self.assert_fingerprint
        )


class _DeadlineHTTPConnectionPool(HTTPConnectionPool):
    ConnectionCls = _DeadlineHTTPConnection


class _DeadlineHTTPSConnectionPool(HTTPSConnectionPool):
    ConnectionCls = _DeadlineHTTPSConnection


class _DeadlinePoolManager(PoolManager):
    """PoolManager whose per-scheme pools yield deadline conns."""

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
    # Governed provider endpoints are direct-only by contract (the
    # approved-specialist configuration owns addresses). trust_env
    # keeps HTTP(S)_PROXY/NO_PROXY/netrc/REQUESTS_CA_BUNDLE env from
    # silently diverting or weakening governed calls — a redirectable
    # proxy path would escape the deadline pools entirely.
    session.trust_env = False
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
    (no cookie/connection state carried between requests). Redirects
    stay enabled but share the request's absolute deadline through the
    contextvar — no per-hop renewal. ``proxies`` is rejected: the
    governed transport is direct-only (a ProxyManager would bypass
    the deadline pools entirely).
    """
    if kwargs.get("proxies"):
        raise BoundedHttpTransportPolicyError(
            "proxies are unsupported on the governed deadline transport"
        )
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
    """Drop-in for ``requests.post`` honoring the absolute deadline.
    ``proxies`` is rejected — see ``deadline_http_get``."""
    if kwargs.get("proxies"):
        raise BoundedHttpTransportPolicyError(
            "proxies are unsupported on the governed deadline transport"
        )
    with _deadline_session() as session:
        return session.post(
            url,
            headers=headers,
            data=data,
            timeout=timeout,
            stream=stream,
            **kwargs,
        )

"""C3-INTELLIGENCE-LOOP-03R2A-R3 — pre-body absolute deadline.

``requests``/urllib3 timeouts are per-recv INACTIVITY bounds — a
server trickling the status line or response headers renews every
recv and can outlive any configured timeout. The R2 primitive only
regained control AFTER ``send()`` returned, so pre-body phases were
not absolutely bounded (probed: ``Timeout(total=0.4)`` took 3.7s).

These tests run a REAL socket server that writes the HTTP wire
manually — trickling the status line, the headers, stalling the first
byte and trickling the body — while the request goes through the real
production transport (``deadline_http_get`` → requests → urllib3 →
deadline-wrapped socket). Elapsed time is asserted near the caller
bound, and termination is observed server-side via BrokenPipe/reset.
"""

import socket
import threading
import time

import pytest

from app.infrastructure.http.bounded_request import (
    BoundedHttpTimeout,
    bounded_request,
)
from app.infrastructure.http.deadline_transport import deadline_http_get

_BOUND = 0.4
_FRAGMENT_INTERVAL = 0.1
# Tolerance: scheduler/read-slice slack. The bound is 0.4; without R3
# these requests ran 3.7s+. <1.0 proves absolute termination.
_ELAPSED_MAX = 1.0


def _read_request(conn):
    """Consume one HTTP request (request line + headers)."""
    buf = b""
    while b"\r\n\r\n" not in buf:
        data = conn.recv(4096)
        if not data:
            return False
        buf += data
    return True


def _serve(writer):
    """Run ``writer(conn, observed)`` for each accepted connection."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", 0))
    server.listen(4)
    stop = threading.Event()
    observed = []

    def loop():
        server.settimeout(0.5)
        while not stop.is_set():
            try:
                conn, _ = server.accept()
            except socket.timeout:
                continue
            except OSError:
                break  # server closed during teardown
            threading.Thread(
                target=writer, args=(conn, observed), daemon=True
            ).start()

    threading.Thread(target=loop, daemon=True).start()
    return server, stop, observed


def _url(server):
    return f"http://127.0.0.1:{server.getsockname()[1]}/x"


def _await_abort(observed):
    for _ in range(40):
        if observed:
            return
        time.sleep(0.05)


def _status_line_trickle(conn, observed):
    """Emit the status line one byte per 0.1s — 1.7s total vs 0.4 bound."""
    try:
        if not _read_request(conn):
            return
        for byte in b"HTTP/1.1 200 OK\r\n":
            conn.sendall(bytes([byte]))
            time.sleep(_FRAGMENT_INTERVAL)
        conn.sendall(b"Content-Length: 1\r\n\r\nx")
    except OSError as exc:
        observed.append(type(exc).__name__)
    finally:
        conn.close()


def _header_trickle(conn, observed):
    """Status line fast; headers trickle one char per 0.1s."""
    try:
        if not _read_request(conn):
            return
        conn.sendall(b"HTTP/1.1 200 OK\r\n")
        headers = b"Content-Type: text/plain\r\nX-A: " + b"y" * 60 + b"\r\n"
        for byte in headers:
            conn.sendall(bytes([byte]))
            time.sleep(_FRAGMENT_INTERVAL)
        conn.sendall(b"Content-Length: 1\r\n\r\nx")
    except OSError as exc:
        observed.append(type(exc).__name__)
    finally:
        conn.close()


def _first_byte_stall(conn, observed):
    """Accept, read the request, emit no response byte. Detect client
    abort via EOF (client closes the socket on timeout)."""
    try:
        if not _read_request(conn):
            return
        conn.settimeout(3.0)
        data = conn.recv(4096)
        if not data:
            observed.append("eof")
            return
        conn.sendall(b"HTTP/1.1 200 OK\r\nContent-Length: 1\r\n\r\nx")
    except OSError as exc:
        observed.append(type(exc).__name__)
    finally:
        conn.close()


def _body_trickle(conn, observed):
    """Valid head, then 1-byte body chunks every 0.05s forever."""
    try:
        if not _read_request(conn):
            return
        conn.sendall(b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\n")
        while True:
            conn.sendall(b"x")
            time.sleep(0.05)
    except OSError as exc:
        observed.append(type(exc).__name__)
    finally:
        conn.close()


def _fast_ok(conn, observed):
    try:
        if not _read_request(conn):
            return
        body = b'{"ok": true}'
        conn.sendall(
            b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n"
            b"Content-Length: " + str(len(body)).encode() + b"\r\n\r\n" + body
        )
    except OSError:
        pass
    finally:
        conn.close()


def test_r3_status_line_trickle_absolute_deadline():
    """A status line trickled below the inactivity slice must abort at
    the absolute deadline — R2's primitive let this run ~9x the bound."""
    server, stop, observed = _serve(_status_line_trickle)
    try:
        started = time.monotonic()
        with pytest.raises(BoundedHttpTimeout):
            bounded_request(
                deadline_http_get, _url(server), timeout_seconds=_BOUND
            )
        elapsed = time.monotonic() - started
        assert elapsed < _ELAPSED_MAX, f"elapsed {elapsed:.2f}s"
        _await_abort(observed)
        assert observed  # server observed the connection die
    finally:
        stop.set()
        server.close()


def test_r3_header_trickle_absolute_deadline():
    """Header bytes trickled below the inactivity slice must abort at
    the absolute deadline before end-of-headers."""
    server, stop, observed = _serve(_header_trickle)
    try:
        started = time.monotonic()
        with pytest.raises(BoundedHttpTimeout):
            bounded_request(
                deadline_http_get, _url(server), timeout_seconds=_BOUND
            )
        elapsed = time.monotonic() - started
        assert elapsed < _ELAPSED_MAX, f"elapsed {elapsed:.2f}s"
        _await_abort(observed)
        assert observed
    finally:
        stop.set()
        server.close()


def test_r3_first_response_byte_stall_absolute_deadline():
    """A server emitting no response byte must hit the absolute
    deadline, not only the configured provider maximum."""
    server, stop, observed = _serve(_first_byte_stall)
    try:
        started = time.monotonic()
        with pytest.raises(BoundedHttpTimeout):
            bounded_request(
                deadline_http_get, _url(server), timeout_seconds=_BOUND
            )
        elapsed = time.monotonic() - started
        assert elapsed < _ELAPSED_MAX, f"elapsed {elapsed:.2f}s"
        _await_abort(observed)
        assert observed
    finally:
        stop.set()
        server.close()


def test_r3_body_trickle_absolute_deadline_regression():
    """R2 body-trickle bound preserved under the socket wrapper."""
    server, stop, observed = _serve(_body_trickle)
    try:
        started = time.monotonic()
        with pytest.raises(BoundedHttpTimeout):
            bounded_request(
                deadline_http_get, _url(server), timeout_seconds=_BOUND
            )
        elapsed = time.monotonic() - started
        assert elapsed < _ELAPSED_MAX, f"elapsed {elapsed:.2f}s"
        _await_abort(observed)
        assert observed
    finally:
        stop.set()
        server.close()


def test_r3_fast_path_unaffected():
    """A fast complete response parses normally through the deadline
    transport — status, headers and JSON body intact."""
    server, stop, _ = _serve(_fast_ok)
    try:
        response = bounded_request(
            deadline_http_get, _url(server), timeout_seconds=2.0
        )
        assert response.status_code == 200
        assert response.json() == {"ok": True}
        assert response.headers.get("Content-Type") == "application/json"
    finally:
        stop.set()
        server.close()


def test_r3_deadline_socket_mapped_to_consumer_timeout():
    """Consumer mapping: pre-body deadline through the real MCP
    transport surfaces as truthful MCP_TIMEOUT, not success."""
    from app.application.specialist_interop.errors import (
        MCP_TIMEOUT,
        SpecialistInteropError,
    )
    from app.infrastructure.interoperability.mcp.transport import (
        DelpiMcpTransport,
    )

    server, stop, observed = _serve(_status_line_trickle)
    try:
        transport = DelpiMcpTransport(
            f"http://127.0.0.1:{server.getsockname()[1]}/mcp",
            timeout_seconds=_BOUND,
            bearer_token="t",
        )
        started = time.monotonic()
        with pytest.raises(SpecialistInteropError) as exc:
            transport.list_tools()
        assert exc.value.code == MCP_TIMEOUT
        assert time.monotonic() - started < 2.0
        _await_abort(observed)
        assert observed
    finally:
        stop.set()
        server.close()


# -------------------------------------------------------------------
# C3-INTELLIGENCE-LOOP-03R2A-R4 — pre-connect / TLS / proxy closure
# -------------------------------------------------------------------

import select  # noqa: E402
import ssl  # noqa: E402

from app.infrastructure.http.bounded_request import (  # noqa: E402
    BoundedHttpTransportError,
)
from app.infrastructure.http.deadline_transport import (  # noqa: E402
    _DeadlineSocket,
    deadline_scope,
)

_R4_BOUND = 0.4
_R4_TOLERANCE = 0.35
# A stalled segment can legitimately overshoot the bound only by
# scheduler slack — never by a renewed window.
_R4_ELAPSED_MAX = _R4_BOUND + _R4_TOLERANCE


class _CountingStubSocket:
    """Stub recording every wire op — proves zero work post-expiry."""

    def __init__(self):
        self.calls = []

    def settimeout(self, value):
        self.calls.append(("settimeout", value))

    def send(self, data, flags=0):
        self.calls.append(("send", len(data)))
        return len(data)

    def sendall(self, data, flags=0):
        self.calls.append(("sendall", len(data)))

    def recv(self, bufsize, flags=0):
        self.calls.append(("recv", bufsize))
        return b""

    def recv_into(self, buffer, nbytes=0, flags=0):
        self.calls.append(("recv_into", nbytes))
        return 0

    def close(self):
        self.calls.append(("close",))


def test_r4_send_expired_fails_before_wire():
    """Expired deadline: send() raises TimeoutError with zero wire ops."""
    stub = _CountingStubSocket()
    wrapper = _DeadlineSocket(stub, lambda: time.monotonic() - 1.0)
    with pytest.raises(TimeoutError):
        wrapper.send(b"x")
    assert ("send", 1) not in stub.calls
    assert [c for c in stub.calls if c[0] == "send"] == []


def test_r4_sendall_expired_fails_before_wire():
    stub = _CountingStubSocket()
    wrapper = _DeadlineSocket(stub, lambda: time.monotonic() - 1.0)
    with pytest.raises(TimeoutError):
        wrapper.sendall(b"xy")
    assert [c for c in stub.calls if c[0] == "sendall"] == []


def test_r4_sendall_live_still_works():
    stub = _CountingStubSocket()
    wrapper = _DeadlineSocket(stub, lambda: time.monotonic() + 10.0)
    wrapper.sendall(b"ok")
    assert ("sendall", 2) in stub.calls


def test_r4_tcp_connect_stall_bounded_or_fails_fast():
    """TCP connect to a non-routable TEST-NET address must end inside
    the caller bound (timeout at deadline) or refuse fast — never a
    renewed per-phase window."""
    # 192.0.2.1 is RFC 5737 documentation space — connect() stalls
    # (SYN blackhole) or refuses immediately on hosts without a route.
    started = time.monotonic()
    with pytest.raises((BoundedHttpTimeout, BoundedHttpTransportError)):
        bounded_request(
            deadline_http_get,
            "http://192.0.2.1:81/x",
            timeout_seconds=_R4_BOUND,
        )
    elapsed = time.monotonic() - started
    # Renewal would put connect near the OS-level TCP timeout (75s+)
    # or the configured connect cap — a bound-honoring abort lands
    # near 0.4s, a fast refusal near 0.
    assert elapsed < 2.0, f"elapsed {elapsed:.2f}s"


def test_r4_multi_address_shared_budget(monkeypatch):
    """getaddrinfo returning several stalled addresses: all attempts
    share ONE remaining budget — attempt timeouts shrink monotonically
    and the total lands near the bound, not N × bound."""
    granted_timeouts = []

    def fake_getaddrinfo(host, port, family, socktype):
        return [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 81))
            for _ in range(4)
        ]

    class StallingSocket:
        """connect() sleeps its granted timeout then times out — each
        attempt WOULD consume its full window if renewed."""

        def __init__(self, *args, **kwargs):
            self._timeout = None

        def settimeout(self, value):
            self._timeout = value

        def setsockopt(self, *args, **kwargs):
            pass

        def bind(self, *args, **kwargs):
            pass

        def connect(self, sa):
            granted_timeouts.append(self._timeout)
            if self._timeout:
                time.sleep(self._timeout)
            raise socket.timeout("stalled connect")

        def close(self):
            pass

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)
    monkeypatch.setattr(socket, "socket", StallingSocket)

    started = time.monotonic()
    with pytest.raises(
        (BoundedHttpTimeout, BoundedHttpTransportError)
    ):
        bounded_request(
            deadline_http_get,
            "http://multi-addr.invalid/x",
            timeout_seconds=_R4_BOUND,
        )
    elapsed = time.monotonic() - started
    # Shared budget: first attempt gets ~0.4, later attempts get
    # only the remainder — total ≈ bound, not 4 × bound.
    assert elapsed < _R4_ELAPSED_MAX, f"elapsed {elapsed:.2f}s"
    assert granted_timeouts, "no connect attempt recorded"
    assert all(
        t <= _R4_BOUND + 0.01 for t in granted_timeouts
    ), granted_timeouts
    assert len(granted_timeouts) <= 2 or all(
        granted_timeouts[i] <= granted_timeouts[0]
        for i in range(len(granted_timeouts))
    )


def _run_dns_connect_probe(monkeypatch):
    """Shared helper — returns (elapsed, connect_attempts, error)."""
    real_getaddrinfo = socket.getaddrinfo
    real_connect = socket.socket.connect
    attempts = []

    def slow_getaddrinfo(host, port, family, socktype):
        time.sleep(0.3)
        return real_getaddrinfo(host, port, family, socktype)

    def counting_connect(self, sa):
        attempts.append(sa)
        return real_connect(self, sa)

    monkeypatch.setattr(socket, "getaddrinfo", slow_getaddrinfo)
    monkeypatch.setattr(socket.socket, "connect", counting_connect)

    server, stop, _ = _serve(_fast_ok)
    try:
        started = time.monotonic()
        try:
            bounded_request(
                deadline_http_get,
                f"http://localhost:{server.getsockname()[1]}/x",
                timeout_seconds=0.1,
            )
            error = None
        except Exception as exc:  # noqa: BLE001
            error = exc
        elapsed = time.monotonic() - started
        return elapsed, attempts, error
    finally:
        stop.set()
        server.close()


def test_r4_dns_zero_connect_after_expiry(monkeypatch):
    """After an over-budget resolver call the transport issues ZERO
    connect attempts — the expired budget is fail-closed, and the
    request truthfully times out."""
    elapsed, attempts, error = _run_dns_connect_probe(monkeypatch)
    assert isinstance(error, BoundedHttpTimeout), repr(error)
    assert attempts == [], f"connect attempts after expiry: {attempts}"
    assert elapsed < 1.0, f"elapsed {elapsed:.2f}s"


def _tls_material(tmp_path):
    """Generate a test-only CA-less leaf: CN/SAN localhost+127.0.0.1."""
    import datetime

    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID

    key = rsa.generate_private_key(
        public_exponent=65537, key_size=2048
    )
    name = x509.Name(
        [x509.NameAttribute(NameOID.COMMON_NAME, "localhost")]
    )
    now = datetime.datetime.now(datetime.timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(1)
        .not_valid_before(now - datetime.timedelta(days=1))
        .not_valid_after(now + datetime.timedelta(days=30))
        .add_extension(
            x509.SubjectAlternativeName(
                [
                    x509.DNSName("localhost"),
                    x509.IPAddress(
                        __import__("ipaddress").IPv4Address("127.0.0.1")
                    ),
                ]
            ),
            critical=False,
        )
        .add_extension(
            x509.BasicConstraints(ca=True, path_length=None),
            critical=True,
        )
        .sign(key, hashes.SHA256())
    )
    cert_path = tmp_path / "test-ca.crt"
    key_path = tmp_path / "test-key.pem"
    cert_path.write_bytes(
        cert.public_bytes(serialization.Encoding.PEM)
    )
    key_path.write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption(),
        )
    )
    return str(cert_path), str(key_path)


def _tls_peer(ctx, conn, trickle=False):
    """Real TLS server via MemoryBIO — bytes emitted by stdlib ssl,
    optionally dripped so the handshake outlives the client bound."""
    in_bio = ssl.MemoryBIO()
    out_bio = ssl.MemoryBIO()
    engine = ctx.wrap_bio(in_bio, out_bio, server_side=True)

    def flush():
        while True:
            chunk = out_bio.read()
            if not chunk:
                return
            if trickle:
                for i in range(0, len(chunk), 40):
                    conn.sendall(chunk[i : i + 40])
                    time.sleep(0.05)
            else:
                conn.sendall(chunk)

    try:
        while True:
            try:
                engine.do_handshake()
                break
            except ssl.SSLWantReadError:
                flush()
                data = conn.recv(4096)
                if not data:
                    return None
                in_bio.write(data)
            except ssl.SSLWantWriteError:
                flush()
        return engine, in_bio, out_bio, flush
    except (OSError, ssl.SSLError):
        return None


def _tls_serve(cert_path, key_path, writer, trickle_handshake=False):
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(certfile=cert_path, keyfile=key_path)
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", 0))
    server.listen(4)
    stop = threading.Event()
    observed = []

    def loop():
        server.settimeout(0.5)
        while not stop.is_set():
            try:
                conn, _ = server.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            threading.Thread(
                target=_tls_conn_handler,
                args=(ctx, conn, writer, trickle_handshake, observed),
                daemon=True,
            ).start()

    threading.Thread(target=loop, daemon=True).start()
    return server, stop, observed


def _tls_conn_handler(ctx, conn, writer, trickle, observed):
    try:
        tls = _tls_peer(ctx, conn, trickle=trickle)
        if tls is None:
            return
        engine, in_bio, out_bio, flush = tls
        writer(engine, in_bio, out_bio, flush, conn, observed)
    except (OSError, ssl.SSLError) as exc:
        observed.append(type(exc).__name__)
    finally:
        conn.close()


def _tls_read_request(engine, in_bio, conn, observed):
    """Read one HTTP request through the TLS engine."""
    buf = b""
    while b"\r\n\r\n" not in buf:
        try:
            data = engine.read(4096)
            if not data:
                return False
            buf += data
        except ssl.SSLWantReadError:
            data = conn.recv(4096)
            if not data:
                return False
            in_bio.write(data)
    return True


def _tls_fast_ok(engine, in_bio, out_bio, flush, conn, observed):
    if not _tls_read_request(engine, in_bio, conn, observed):
        return
    engine.write(
        b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n"
        b"Content-Length: 11\r\n\r\n{\"ok\":true}"
    )
    flush()


def _tls_stall(engine, in_bio, out_bio, flush, conn, observed):
    """Handshake done — then silence: proves recv-deadline on TLS."""
    if not _tls_read_request(engine, in_bio, conn, observed):
        return
    conn.settimeout(3.0)
    try:
        if conn.recv(4096) == b"":
            observed.append("eof")
    except OSError as exc:
        observed.append(type(exc).__name__)


def test_r4_https_fast_path(tmp_path):
    """Normal HTTPS request through the deadline transport: real TLS
    handshake + cert verification (test cert, explicit trust) + body."""
    cert_path, key_path = _tls_material(tmp_path)
    server, stop, _ = _tls_serve(cert_path, key_path, _tls_fast_ok)
    try:
        response = bounded_request(
            deadline_http_get,
            f"https://localhost:{server.getsockname()[1]}/x",
            timeout_seconds=3.0,
            verify=cert_path,
        )
        assert response.status_code == 200
        assert response.json() == {"ok": True}
    finally:
        stop.set()
        server.close()


def test_r4_tls_handshake_trickle_absolute_deadline(tmp_path):
    """Adversarial TLS peer trickling real handshake bytes (each byte
    valid, intervals below any inactivity slice) must abort at the
    absolute deadline — inactivity renewals are worthless here."""
    cert_path, key_path = _tls_material(tmp_path)
    server, stop, observed = _tls_serve(
        cert_path, key_path, _tls_fast_ok, trickle_handshake=True
    )
    try:
        started = time.monotonic()
        with pytest.raises(BoundedHttpTimeout):
            bounded_request(
                deadline_http_get,
                f"https://localhost:{server.getsockname()[1]}/x",
                timeout_seconds=_R4_BOUND,
                verify=cert_path,
            )
        elapsed = time.monotonic() - started
        # Without the absolute deadline the trickled handshake runs
        # seconds (40B/0.05s over ~2KB of records ≈ 2.5s+).
        assert elapsed < _R4_ELAPSED_MAX, f"elapsed {elapsed:.2f}s"
    finally:
        stop.set()
        server.close()


def test_r4_redirect_chain_shared_deadline():
    """A redirect must NOT renew the deadline: server A delays most of
    the budget then 302s to server B, which trickles. Total ≈ bound."""
    server_b, stop_b, observed_b = _serve(_status_line_trickle)
    port_b = server_b.getsockname()[1]
    # Server A: consume ~0.3s of the 0.4 budget, then redirect.
    def slow_redirect(conn, observed):
        try:
            if not _read_request(conn):
                return
            time.sleep(0.3)
            conn.sendall(
                b"HTTP/1.1 302 Found\r\nLocation: http://127.0.0.1:"
                + str(port_b).encode()
                + b"/x\r\nContent-Length: 0\r\n\r\n"
            )
        except OSError as exc:
            observed.append(type(exc).__name__)
        finally:
            conn.close()

    server_a, stop_a, _ = _serve(slow_redirect)
    try:
        started = time.monotonic()
        with pytest.raises(
            (BoundedHttpTimeout, BoundedHttpTransportError)
        ):
            bounded_request(
                deadline_http_get,
                f"http://127.0.0.1:{server_a.getsockname()[1]}/x",
                timeout_seconds=_R4_BOUND,
            )
        elapsed = time.monotonic() - started
        # Per-redirect renewal would grant B a fresh 0.4 window →
        # ≈0.8s+; shared deadline lands ≈0.4s.
        assert elapsed < _R4_ELAPSED_MAX, f"elapsed {elapsed:.2f}s"
    finally:
        stop_a.set()
        server_a.close()
        stop_b.set()
        server_b.close()


def test_r4_env_proxy_ignored_fail_closed(monkeypatch):
    """Governed calls never route through env proxies: a bogus
    HTTP_PROXY pointing at a dead port must not divert or break a
    reachable endpoint (trust_env=False on deadline sessions)."""
    monkeypatch.setenv("HTTP_PROXY", "http://127.0.0.1:1")
    monkeypatch.setenv("http_proxy", "http://127.0.0.1:1")
    monkeypatch.setenv("HTTPS_PROXY", "http://127.0.0.1:1")
    monkeypatch.setenv("https_proxy", "http://127.0.0.1:1")
    monkeypatch.delenv("NO_PROXY", raising=False)
    monkeypatch.delenv("no_proxy", raising=False)

    server, stop, _ = _serve(_fast_ok)
    try:
        response = bounded_request(
            deadline_http_get, _url(server), timeout_seconds=3.0
        )
        # Trust-env proxying would hit 127.0.0.1:1 (refused) — success
        # proves the env proxy never applied.
        assert response.status_code == 200
    finally:
        stop.set()
        server.close()


def test_r4_proxies_kwarg_rejected_fail_closed():
    """An explicit ``proxies=`` argument is rejected before any wire
    work — a ProxyManager would bypass the deadline pools entirely."""
    from app.infrastructure.http.deadline_transport import (
        BoundedHttpTransportPolicyError,
    )

    server, stop, _ = _serve(_fast_ok)
    try:
        with pytest.raises(BoundedHttpTransportPolicyError):
            deadline_http_get(
                _url(server), proxies={"http": "http://127.0.0.1:1"}
            )
    finally:
        stop.set()
        server.close()


def test_r4_explicit_proxy_fails_closed():
    """A pool-level proxy config on the governed transport is rejected
    loudly — never a silently unbounded path."""
    from urllib3.exceptions import ProxyError

    from app.infrastructure.http.deadline_transport import (
        _DeadlineHTTPSConnection,
    )

    https_conn = _DeadlineHTTPSConnection("example.com", 443)
    https_conn.proxy = "http://127.0.0.1:3128"

    deadline = time.monotonic() + 5.0
    with deadline_scope(deadline):
        with pytest.raises(ProxyError):
            https_conn.connect()


# -------------------------------------------------------------------
# C3-INTELLIGENCE-LOOP-03R2A-R5 — bounded DNS executor + dep freeze
# -------------------------------------------------------------------

import threading as _threading  # noqa: E402

from app.infrastructure.http.dns_resolver import (  # noqa: E402
    BoundedDnsResolver,
    DnsResolverSaturatedError,
    MAX_DNS_RESOLVER_OUTSTANDING,
    MAX_DNS_RESOLVER_WORKERS,
)


def test_r5_dns_fast_path_works():
    """Normal resolution through the bounded executor — request
    completes unchanged."""
    server, stop, _ = _serve(_fast_ok)
    try:
        response = bounded_request(
            deadline_http_get,
            f"http://localhost:{server.getsockname()[1]}/x",
            timeout_seconds=3.0,
        )
        assert response.status_code == 200
    finally:
        stop.set()
        server.close()


def test_r5_dns_slow_caller_deadline(monkeypatch):
    """getaddrinfo sleeping 1.0s under a 0.1s caller budget: the
    caller returns near its OWN deadline — it never waits for the
    worker."""
    real_getaddrinfo = socket.getaddrinfo

    def slow_getaddrinfo(host, port, family, socktype):
        time.sleep(1.0)
        return real_getaddrinfo(host, port, family, socktype)

    monkeypatch.setattr(socket, "getaddrinfo", slow_getaddrinfo)

    started = time.monotonic()
    with pytest.raises(BoundedHttpTimeout):
        bounded_request(
            deadline_http_get,
            "http://localhost:1/x",
            timeout_seconds=0.1,
        )
    elapsed = time.monotonic() - started
    # Scheduler/CI slack — structural bound is 0.1, worker runs 1.0.
    assert elapsed < 0.6, f"elapsed {elapsed:.2f}s"


def test_r5_dns_late_result_zero_side_effects(monkeypatch):
    """After the caller times out, the worker's late result is
    discarded — ZERO TCP connect, even after the worker finishes."""
    finished = _threading.Event()
    connect_attempts = []
    real_getaddrinfo = socket.getaddrinfo
    real_connect = socket.socket.connect

    def slow_getaddrinfo(host, port, family, socktype):
        time.sleep(0.6)
        result = real_getaddrinfo(host, port, family, socktype)
        finished.set()
        return result

    def counting_connect(self, sa):
        connect_attempts.append(sa)
        return real_connect(self, sa)

    monkeypatch.setattr(socket, "getaddrinfo", slow_getaddrinfo)
    monkeypatch.setattr(socket.socket, "connect", counting_connect)

    server, stop, _ = _serve(_fast_ok)
    try:
        started = time.monotonic()
        with pytest.raises(BoundedHttpTimeout):
            bounded_request(
                deadline_http_get,
                f"http://localhost:{server.getsockname()[1]}/x",
                timeout_seconds=0.1,
            )
        assert time.monotonic() - started < 0.6
        # Wait until the worker ACTUALLY finishes — late result must
        # still have produced zero connects.
        assert finished.wait(timeout=5.0)
        time.sleep(0.2)
        assert connect_attempts == []
    finally:
        stop.set()
        server.close()


def test_r5_dns_result_past_deadline_zero_connect(monkeypatch):
    """A result arriving just past the deadline is rejected by the
    recheck — zero connect attempts even though resolution
    'succeeded'."""
    connect_attempts = []
    real_getaddrinfo = socket.getaddrinfo
    real_connect = socket.socket.connect

    def near_deadline_getaddrinfo(host, port, family, socktype):
        time.sleep(0.35)  # returns just past the 0.3s budget
        return real_getaddrinfo(host, port, family, socktype)

    def counting_connect(self, sa):
        connect_attempts.append(sa)
        return real_connect(self, sa)

    monkeypatch.setattr(socket, "getaddrinfo", near_deadline_getaddrinfo)
    monkeypatch.setattr(socket.socket, "connect", counting_connect)

    server, stop, _ = _serve(_fast_ok)
    try:
        with pytest.raises(BoundedHttpTimeout):
            bounded_request(
                deadline_http_get,
                f"http://localhost:{server.getsockname()[1]}/x",
                timeout_seconds=0.3,
            )
        assert connect_attempts == []
    finally:
        stop.set()
        server.close()


def test_r5_dns_saturation_fails_closed(monkeypatch):
    """All outstanding slots occupied by slow lookups → a new request
    fails fast; thread count never exceeds MAX_WORKERS."""
    release = _threading.Event()
    real_getaddrinfo = socket.getaddrinfo

    def blocking_getaddrinfo(host, port, family, socktype):
        release.wait(timeout=10.0)
        return real_getaddrinfo(host, port, family, socktype)

    monkeypatch.setattr(socket, "getaddrinfo", blocking_getaddrinfo)

    resolver = BoundedDnsResolver(
        max_workers=MAX_DNS_RESOLVER_WORKERS,
        max_outstanding=MAX_DNS_RESOLVER_OUTSTANDING,
    )
    deadline = time.monotonic() + 30.0
    workers_before = len(resolver._pool._threads)
    # Occupy every outstanding slot directly (structural capacity
    # proof — not request-count dependent).
    holders = [
        _threading.Thread(
            target=lambda i=i: _swallow(
                resolver.resolve, "h%d" % i, 80, 0, socket.SOCK_STREAM,
                deadline,
            ),
            daemon=True,
        )
        for i in range(MAX_DNS_RESOLVER_OUTSTANDING)
    ]
    for t in holders:
        t.start()
    time.sleep(0.5)  # let submissions land
    try:
        # Next admission fails fast — no queue growth, no new worker.
        with pytest.raises(DnsResolverSaturatedError):
            resolver.resolve(
                "blocked.invalid", 80, 0, socket.SOCK_STREAM, deadline
            )
        workers_peak = len(resolver._pool._threads)
        assert workers_before <= workers_peak
        assert workers_peak <= MAX_DNS_RESOLVER_WORKERS
        # No TCP connect ever happened — workers only resolved DNS.
    finally:
        release.set()
        resolver._pool.shutdown(wait=True, cancel_futures=True)


def _swallow(fn, *args):
    try:
        fn(*args)
    except Exception:  # noqa: BLE001
        pass


def test_r5_dns_timeout_storm_bounded(monkeypatch):
    """Repeated slow DNS submissions beyond capacity: no unbounded
    thread growth, callers fail closed once saturated, the pool
    recovers afterwards."""
    release = _threading.Event()
    real_getaddrinfo = socket.getaddrinfo

    def blocking_getaddrinfo(host, port, family, socktype):
        release.wait(timeout=15.0)
        return real_getaddrinfo(host, port, family, socktype)

    monkeypatch.setattr(socket, "getaddrinfo", blocking_getaddrinfo)

    # Dedicated test instance — same class the singleton uses.
    resolver = BoundedDnsResolver()
    deadline = time.monotonic() + 20.0

    results = []
    storm = [
        _threading.Thread(
            target=lambda: results.append(
                _swallow_or_error(
                    resolver.resolve, "storm.invalid", 80, 0,
                    socket.SOCK_STREAM, deadline,
                )
            ),
            daemon=True,
        )
        for _ in range(MAX_DNS_RESOLVER_OUTSTANDING * 2)
    ]
    for t in storm:
        t.start()
    time.sleep(0.5)  # let submissions land while workers block

    try:
        # Thread count stays at the configured cap.
        assert len(resolver._pool._threads) <= MAX_DNS_RESOLVER_WORKERS
        # A late caller while still saturated fails fast.
        with pytest.raises(
            (DnsResolverSaturatedError, socket.timeout)
        ):
            resolver.resolve(
                "late.invalid", 80, 0, socket.SOCK_STREAM,
                time.monotonic() + 5.0,
            )
    finally:
        release.set()
    for t in storm:
        t.join(timeout=15.0)

    # Beyond-capacity callers failed closed (saturated or deadline).
    assert results.count("saturated") + results.count(
        "timeout"
    ) > 0
    # Recovery: capacity frees and a normal resolution succeeds.
    out = resolver.resolve(
        "localhost", 80, 0, socket.SOCK_STREAM,
        time.monotonic() + 5.0,
    )
    assert out
    resolver._pool.shutdown(wait=True, cancel_futures=True)


def _swallow_or_error(fn, *args):
    try:
        fn(*args)
        return "resolved"
    except DnsResolverSaturatedError:
        return "saturated"
    except socket.timeout:
        return "timeout"
    except Exception as exc:  # noqa: BLE001
        return type(exc).__name__


def test_r5_dns_gaierror_truthful_no_connect(monkeypatch):
    """Resolution failure maps to a truthful unavailable/timeout —
    never success, never connect."""
    connect_attempts = []
    real_connect = socket.socket.connect

    def failing_getaddrinfo(host, port, family, socktype):
        raise socket.gaierror(-2, "Name or service not known")

    def counting_connect(self, sa):
        connect_attempts.append(sa)
        return real_connect(self, sa)

    monkeypatch.setattr(socket, "getaddrinfo", failing_getaddrinfo)
    monkeypatch.setattr(socket.socket, "connect", counting_connect)

    with pytest.raises(
        (BoundedHttpTimeout, BoundedHttpTransportError)
    ):
        bounded_request(
            deadline_http_get,
            "http://unresolvable.invalid/x",
            timeout_seconds=1.0,
        )
    assert connect_attempts == []


def test_r5_transport_compatibility_guard():
    """Dependency-freeze guard: prove the private/internal urllib3
    surfaces deadline_transport depends on exist at runtime — an
    upgrade breaking them must fail LOUDLY here, forcing a rerun of
    the absolute-deadline acceptance suite."""
    import urllib3.connection as uc
    import urllib3.connectionpool as ucp
    import urllib3.poolmanager as upm
    import urllib3.util.connection as uconn
    import urllib3.util.ssl_ as usl

    assert callable(uc._match_hostname)
    assert callable(uc._assert_fingerprint)
    assert callable(uc.is_ipaddress)
    assert callable(usl.create_urllib3_context)
    assert callable(usl.resolve_cert_reqs)
    assert callable(usl.resolve_ssl_version)
    assert isinstance(usl.ALPN_PROTOCOLS, list)
    assert hasattr(usl, "HAS_NEVER_CHECK_COMMON_NAME")
    assert hasattr(usl, "IS_PYOPENSSL")
    assert callable(uconn._set_socket_options)
    assert callable(uconn.allowed_gai_family)
    for name in (
        "ConnectTimeoutError",
        "LocationParseError",
        "NameResolutionError",
        "NewConnectionError",
        "ProxyError",
    ):
        import urllib3.exceptions as uex

        assert hasattr(uex, name), name
    # Structural surfaces used by the subclasses.
    assert hasattr(uc.HTTPConnection, "_new_conn")
    assert hasattr(uc.HTTPSConnection, "connect")
    assert issubclass(ucp.HTTPSConnectionPool, object)
    # PoolManager stores scheme->pool class map on the INSTANCE.
    mgr = upm.PoolManager()
    assert "http" in mgr.pool_classes_by_scheme
    # The deadline transport actually wires itself end-to-end.
    import app.infrastructure.http.deadline_transport as dt

    session = dt._deadline_session()
    assert session.trust_env is False
    assert isinstance(
        session.get_adapter("http://x"), dt._DeadlineHTTPAdapter
    )
    assert isinstance(
        session.get_adapter("https://x"), dt._DeadlineHTTPAdapter
    )
    conn = dt._DeadlineHTTPConnection("example.com", 80)
    assert hasattr(conn, "_bounded_connect")
    https_conn = dt._DeadlineHTTPSConnection("example.com", 443)
    assert hasattr(https_conn, "_bounded_connect")
    assert hasattr(https_conn, "_deadline_connect")


# ------------------------------------------------------------------
# R2B regression: content-encoding + header-name case
#
# Live evaluation on the current surface proved ``bounded_request``
# returned the raw GZIP stream undecoded (``raw.read1()`` without
# ``decode_content``) and lost header lookups against lowercase field
# names (``Content-Type`` absent from a case-sensitive dict). Both
# made a valid MCP JSON response surface as ``mcp_invalid_response``.
# ------------------------------------------------------------------


def _gzip_json_lowercase_headers(conn, observed):
    """Real wire: gzipped JSON body, lowercase header names."""
    import gzip

    try:
        if not _read_request(conn):
            return
        body = gzip.compress(b'{"ok": true, "n": 7}')
        conn.sendall(
            b"HTTP/1.1 200 OK\r\n"
            b"content-type: application/json\r\n"
            b"content-encoding: gzip\r\n"
            b"content-length: " + str(len(body)).encode() + b"\r\n"
            b"\r\n" + body
        )
    except OSError:
        pass
    finally:
        conn.close()


def test_r2b_gzip_body_decoded_and_headers_case_insensitive():
    """A gzip-encoded JSON response must surface DECODED content and
    headers must resolve regardless of wire casing."""
    server, stop, _ = _serve(_gzip_json_lowercase_headers)
    try:
        response = bounded_request(
            deadline_http_get, _url(server), timeout_seconds=2.0
        )
        assert response.status_code == 200
        assert response.json() == {"ok": True, "n": 7}
        assert response.headers.get("Content-Type") == "application/json"
        assert response.headers.get("content-type") == "application/json"
        assert response.headers.get("CONTENT-ENCODING") == "gzip"
    finally:
        stop.set()
        server.close()


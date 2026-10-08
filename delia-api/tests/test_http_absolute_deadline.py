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

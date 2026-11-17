"""CI-only real Docker Engine chain using an ephemeral GitHub-hosted runner.

A pre-existing CI workflow creates and removes the disposable container.
These tests only issue GET through the approved ATLAS HML chain and reject
unsafe requests before the Engine. They must never run against srv-api.
"""
from __future__ import annotations

import asyncio
import json
import os
import socket
import threading
from pathlib import Path

import httpx
import pytest

from linux_ops_mcp import atlas_hml_unix_proxy as proxy
from linux_ops_mcp.atlas_hml_engine_boundary import HMLDockerInspectOnly, HML_TARGET
from linux_ops_mcp.deploy_host_source import DockerReadOnlyInspect

pytestmark = pytest.mark.skipif(
    not (
        os.getenv("GITHUB_ACTIONS") == "true"
        and os.getenv("ATLAS_DISPOSABLE_DOCKER") == "true"
        and os.getenv("ATLAS_REAL_HML_CHAIN_CI") == "true"
        and os.getuid() != 0
    ),
    reason="only on a non-root, GitHub-hosted, explicitly gated disposable Docker runner",
)
_EXPECTED_URL = "http://docker.local/containers/delpi-hml-public-hub/json"
_GET = (
    b"GET /containers/delpi-hml-public-hub/json HTTP/1.1\r\n"
    b"Host: docker.local\r\nConnection: close\r\n\r\n"
)


class RecordingEngineTransport(httpx.AsyncBaseTransport):
    """Only a CI runner opens the raw Docker socket, never the ATLAS MCP."""

    def __init__(self):
        self._engine = httpx.AsyncHTTPTransport(uds="/var/run/docker.sock")
        self.requests: list[tuple[str, str]] = []

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        self.requests.append((request.method, str(request.url)))
        return await self._engine.handle_async_request(request)

    async def aclose(self) -> None:
        await self._engine.aclose()


@pytest.fixture
def disposable_listener(tmp_path: Path, monkeypatch):
    parent = tmp_path / "hml"
    parent.mkdir()
    os.chmod(parent, 0o750)
    uds = parent / "inspect.sock"
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    listener.bind(str(uds))
    os.chmod(uds, 0o660)
    listener.listen(2)

    # Redirect the fixed-path production policy ONLY inside this disposable
    # test process. No production code, host path or account is changed.
    monkeypatch.setattr(proxy, "_HML_PATH", uds)
    monkeypatch.setattr(
        proxy, "atlas_collector_identity", lambda: (os.getuid(), os.getgid()),
    )
    try:
        yield uds, listener
    finally:
        listener.close()
        uds.unlink(missing_ok=True)


def _serve_once(endpoint, engine_transport):
    uds, listener = endpoint
    results, errors = [], []

    def run():
        try:
            results.append(proxy.serve_one_prebound(
                listener=listener,
                allowed_collector_uid=os.getuid(),
                inspector=HMLDockerInspectOnly(upstream=engine_transport),
                expected_path=uds,
                owner_uid=os.getuid(),
                socket_gid=os.getgid(),
            ))
        except Exception as exc:
            # Do not print exception text: an OS exception might carry a
            # sensitive path or an upstream detail.
            errors.append(type(exc).__name__)

    worker = threading.Thread(target=run, daemon=True)
    worker.start()
    return worker, results, errors


def _finish(worker, results, errors):
    worker.join(8)
    assert not worker.is_alive(), "one-shot proxy did not stop"
    assert errors == []
    assert len(results) == 1
    result = results[0]
    assert result.status == "blocked"
    assert not result.prepare_eligible
    assert not result.can_execute
    assert not result.proxy_policy_independently_attested
    assert not result.host_identity_attested
    assert not result.raw_docker_socket_exposed
    return result


def _exchange(path: Path, request_bytes: bytes):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.settimeout(4.0)
        client.connect(str(path))
        client.sendall(request_bytes)
        response = bytearray()
        while True:
            chunk = client.recv(4096)
            if not chunk:
                break
            response.extend(chunk)
    head, body = bytes(response).split(b"\r\n\r\n", 1)
    return int(head.split(b"\r\n", 1)[0].split()[1]), json.loads(body)


def test_actual_docker_engine_chain_is_readonly_and_sanitized(disposable_listener):
    uds, _ = disposable_listener
    engine = RecordingEngineTransport()
    worker, results, errors = _serve_once(disposable_listener, engine)

    async def read():
        transport = httpx.AsyncHTTPTransport(uds=str(uds))
        try:
            return await DockerReadOnlyInspect(transport=transport).inspect(HML_TARGET)
        finally:
            await transport.aclose()

    observed = asyncio.run(read())
    outcome = _finish(worker, results, errors)
    assert observed.running is True
    assert observed.healthy is True
    assert len(observed.container_id) == 64
    assert observed.image_id.startswith("sha256:")
    assert outcome.http_status == 200
    assert outcome.request_accepted
    assert engine.requests == [("GET", _EXPECTED_URL)]


@pytest.mark.parametrize("request_bytes,expected_code", [
    (_GET.replace(b"GET ", b"POST ", 1), 405),
    (_GET.replace(b"GET ", b"DELETE ", 1), 405),
    (_GET.replace(
        b"/containers/delpi-hml-public-hub/json",
        b"/containers/delpi-public-hub/json",
    ), 404),
    (_GET.replace(
        b"/containers/delpi-hml-public-hub/json", b"/containers/json",
    ), 404),
    (_GET[:-2] + b"Authorization: Bearer synthetic\r\n\r\n", 400),
])
def test_denials_never_reach_actual_engine(
    disposable_listener, request_bytes, expected_code,
):
    uds, _ = disposable_listener
    engine = RecordingEngineTransport()
    worker, results, errors = _serve_once(disposable_listener, engine)
    code, body = _exchange(uds, request_bytes)
    outcome = _finish(worker, results, errors)
    assert code == expected_code
    assert body == {"error": "HML_REQUEST_DENIED"}
    assert outcome.request_accepted is False
    assert engine.requests == []


def test_wrong_uid_never_reaches_actual_engine(
    disposable_listener, monkeypatch,
):
    uds, _ = disposable_listener
    monkeypatch.setattr(proxy, "_peer_uid", lambda _: os.getuid() + 1001)
    engine = RecordingEngineTransport()
    worker, results, errors = _serve_once(disposable_listener, engine)
    code, body = _exchange(uds, _GET)
    outcome = _finish(worker, results, errors)
    assert code == 403
    assert body == {"error": "HML_PEER_UNTRUSTED"}
    assert outcome.request_accepted is False
    assert engine.requests == []

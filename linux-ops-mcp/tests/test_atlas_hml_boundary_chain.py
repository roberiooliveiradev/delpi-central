"""Complete disposable chain: ATLAS reader -> UNIX proxy -> guarded Docker GET.

No Docker Engine socket, network, service unit, persistent process, Keycloak,
Core, secrets or production/HML container. The only listener is a test-owned
AF_UNIX path under pytest tmp_path and the upstream is httpx.MockTransport.
"""
from __future__ import annotations

import asyncio
import json
import os
import socket
import threading

import httpx
import pytest

from linux_ops_mcp import atlas_hml_unix_proxy as proxy
from linux_ops_mcp import atlas_hml_local_probe as probe
from linux_ops_mcp.atlas_hml_engine_boundary import HMLDockerInspectOnly, HML_TARGET
from linux_ops_mcp.deploy_host_source import DockerReadOnlyInspect, RuntimeContainer

CID = "a" * 64
IMAGE = "sha256:" + "b" * 64
GOOD_GET = (
    b"GET /containers/delpi-hml-public-hub/json HTTP/1.1\r\n"
    b"Host: docker.local\r\nConnection: close\r\n\r\n"
)
pytestmark = pytest.mark.skipif(
    os.getuid() == 0,
    reason="real SO_PEERCRED tests require a non-root runner",
)


@pytest.fixture
def listener_pair(tmp_path, monkeypatch):
    root = tmp_path / "atlas-hml-readonly"
    root.mkdir()
    os.chmod(root, 0o750)
    path = root / "inspect.sock"
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    listener.bind(str(path))
    os.chmod(path, 0o660)
    listener.listen(2)

    # This redirects only the already-fixed production-path check to
    # a disposable CI pathname. atlas_hml_uds_policy._SOCKET is not modified.
    monkeypatch.setattr(proxy, "_HML_PATH", path)
    monkeypatch.setattr(
        proxy, "atlas_collector_identity", lambda: (os.getuid(), os.getgid()),
    )
    try:
        yield path, listener
    finally:
        listener.close()
        path.unlink(missing_ok=True)


def engine_payload(*, project="delpi-hml", image=IMAGE):
    return {
        "Id": CID,
        "Image": image,
        "Name": "/delpi-hml-public-hub",
        "Config": {
            "Labels": {
                "com.docker.compose.project": project,
                "com.docker.compose.service": "public-hub",
            },
            "Env": ["FAKE_PRIVATE_VALUE=must_never_leave_engine"],
            "HostConfig": {"Binds": ["/private/test:/data"]},
        },
        "Mounts": [{"Source": "/private/test"}],
        "NetworkSettings": {"Networks": {"sensitive": {}}},
        "State": {"Running": True, "Health": {"Status": "healthy"}},
    }


def guarded_inspector(seen, *, project="delpi-hml", status_code=200, image=IMAGE):
    def upstream(request):
        seen.append((request.method, str(request.url)))
        return httpx.Response(
            status_code, json=engine_payload(project=project, image=image),
        )
    return HMLDockerInspectOnly(upstream=httpx.MockTransport(upstream))


def start_one(listener_pair, inspector):
    path, listener = listener_pair
    results, errors = [], []

    def execute():
        try:
            results.append(proxy.serve_one_prebound(
                listener=listener,
                allowed_collector_uid=os.getuid(),
                inspector=inspector,
                expected_path=path,
                owner_uid=os.getuid(),
                socket_gid=os.getgid(),
            ))
        except Exception as exc:
            errors.append(type(exc).__name__)

    thread = threading.Thread(target=execute, daemon=True)
    thread.start()
    return thread, results, errors


def completed(thread, results, errors):
    thread.join(6)
    assert not thread.is_alive(), "one-shot handler did not finish"
    assert errors == []
    assert len(results) == 1
    assert results[0].status == "blocked"
    assert results[0].prepare_eligible is False
    assert results[0].can_execute is False
    assert results[0].proxy_policy_independently_attested is False
    return results[0]


def exchange(path, message):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.settimeout(4)
        client.connect(str(path))
        client.sendall(message)
        raw = bytearray()
        while True:
            part = client.recv(4096)
            if not part:
                break
            raw.extend(part)
    header, body = bytes(raw).split(b"\r\n\r\n", 1)
    return int(header.split(b"\r\n", 1)[0].split()[1]), json.loads(body)


def test_complete_chain_returns_only_allowlisted_runtime_metadata(listener_pair):
    path, _ = listener_pair
    seen = []
    thread, results, errors = start_one(listener_pair, guarded_inspector(seen))

    async def query():
        reader = DockerReadOnlyInspect(
            transport=httpx.AsyncHTTPTransport(uds=str(path)),
        )
        return await reader.inspect(HML_TARGET)

    runtime = asyncio.run(query())
    result = completed(thread, results, errors)
    assert runtime == RuntimeContainer(CID, IMAGE, True, True)
    assert result.http_status == 200 and result.request_accepted is True
    assert seen == [(
        "GET", "http://docker.local/containers/delpi-hml-public-hub/json",
    )]
    assert "must_never_leave_engine" not in repr(runtime)
    assert "/private/test" not in repr(runtime)


@pytest.mark.parametrize("method,request_bytes", [
    ("POST", GOOD_GET.replace(b"GET ", b"POST ", 1)),
    ("DELETE", GOOD_GET.replace(b"GET ", b"DELETE ", 1)),
    ("OTHER_CONTAINER", GOOD_GET.replace(
        b"/containers/delpi-hml-public-hub/json",
        b"/containers/delpi-public-hub/json",
    )),
    ("LIST", GOOD_GET.replace(
        b"/containers/delpi-hml-public-hub/json", b"/containers/json",
    )),
    ("AUTHORIZATION", GOOD_GET[:-2] + b"Authorization: Bearer synthetic\r\n\r\n"),
])
def test_request_denied_before_any_upstream_access(listener_pair, method, request_bytes):
    path, _ = listener_pair
    seen = []
    thread, results, errors = start_one(listener_pair, guarded_inspector(seen))
    code, body = exchange(path, request_bytes)
    outcome = completed(thread, results, errors)
    assert code in (400, 404, 405), method
    assert body == {"error": "HML_REQUEST_DENIED"}
    assert outcome.request_accepted is False
    assert seen == []


def test_wrong_peer_identity_never_reads_upstream(listener_pair, monkeypatch):
    path, _ = listener_pair
    monkeypatch.setattr(proxy, "_peer_uid", lambda _client: os.getuid() + 1001)
    seen = []
    thread, results, errors = start_one(listener_pair, guarded_inspector(seen))
    code, body = exchange(path, GOOD_GET)
    assert code == 403 and body == {"error": "HML_PEER_UNTRUSTED"}
    assert completed(thread, results, errors).request_accepted is False
    assert seen == []


@pytest.mark.parametrize("project,status,image", [
    ("delpi-prod", 200, IMAGE),
    ("delpi-hml", 302, IMAGE),
    ("delpi-hml", 200, "sha256:incorrect"),
])
def test_invalid_upstream_is_sanitized_and_never_authorizes(
    listener_pair, project, status, image,
):
    path, _ = listener_pair
    seen = []
    thread, results, errors = start_one(listener_pair, guarded_inspector(
        seen, project=project, status_code=status, image=image,
    ))
    code, body = exchange(path, GOOD_GET)
    outcome = completed(thread, results, errors)
    assert code == 502 and body == {"error": "HML_INSPECT_UNAVAILABLE"}
    assert outcome.request_accepted is False
    assert len(seen) == 1
    assert "must_never_leave_engine" not in repr(body)


def test_real_path_refuses_unbounded_inspector_even_with_valid_uid(listener_pair):
    path, listener = listener_pair

    class ArbitraryInspector:
        async def inspect(self, target):
            raise AssertionError("must not reach untrusted inspector")

    with pytest.raises(
        proxy.HMLUnixProxyError, match="HML_ENGINE_BOUNDARY_REQUIRED",
    ):
        proxy.serve_one_prebound(
            listener=listener,
            allowed_collector_uid=os.getuid(),
            inspector=ArbitraryInspector(),
            expected_path=path,
            owner_uid=os.getuid(),
            socket_gid=os.getgid(),
        )


def test_integrated_manual_probe_observes_image_but_remains_blocked(listener_pair):
    path, _ = listener_pair
    seen = []
    thread, results, errors = start_one(listener_pair, guarded_inspector(seen))

    async def run_probe():
        return await probe.inspect_hml_local(
            identity=probe.LocalOSObservation(
                uid=1001,
                euid=1001,
                groups=("atlas-hml",),
                checkout_writable=False,
            ),
            observer=object(),
            inspector=DockerReadOnlyInspect(
                transport=httpx.AsyncHTTPTransport(uds=str(path)),
            ),
            metadata_only=True,
            metadata_reader=object(),
        )

    report = asyncio.run(run_probe())
    assert report.status == "blocked"
    assert report.docker_image_id == IMAGE
    assert report.docker_running is True
    assert report.docker_healthy is True
    assert "PREPARE_DISABLED" in report.blocks
    assert "ACT_DISABLED" in report.blocks
    assert "HML_PROXY_POLICY_NOT_INDEPENDENTLY_ATTESTED" in report.blocks
    assert report.git_head is None
    assert not report.collector_identity_attested
    assert not report.checkout_integrity_attested
    assert not report.prepare_eligible
    assert not report.can_execute
    assert completed(thread, results, errors).status == "blocked"
    assert len(seen) == 1

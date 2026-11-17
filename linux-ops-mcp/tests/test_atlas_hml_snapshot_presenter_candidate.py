"""Fixture-only POSIX tests for Architecture B snapshot presenter candidate.

Sockets, JSON and snapshots exist only in pytest tmp_path. There is no
Docker Engine, systemd installation, permission escalation or MCP wiring.
"""
from __future__ import annotations

import json
import os
import socket
import threading
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from linux_ops_mcp import atlas_hml_snapshot_file_reader as file_reader
from linux_ops_mcp import atlas_hml_snapshot_presenter_candidate as presenter

_REQUEST = (
    b"GET /v1/hml/public-hub/snapshot HTTP/1.1\r\n"
    b"Host: atlas-hml.local\r\n\r\n"
)
_META = {
    "schema": "atlas.hml.inspect.v1",
    "source": "root-one-shot-snapshot-claim-untrusted",
    "environment": "hml",
    "compose_project": "delpi-hml",
    "service_id": "public-hub",
    "container_name": "delpi-hml-public-hub",
    "container_id": "a" * 64,
    "image_id": "sha256:" + "b" * 64,
    "running": True,
    "healthy": True,
}


@pytest.fixture
def fixture(tmp_path):
    root = tmp_path / "hml-presenter-test"
    root.mkdir()
    os.chmod(root, 0o750)
    snapshot_path = root / "inspect-snapshot.json"
    moment = datetime.now(timezone.utc)
    snapshot_path.write_bytes(json.dumps({
        **_META, "observed_at": moment.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }, separators=(",", ":")).encode("ascii"))
    os.chmod(snapshot_path, 0o640)
    path = root / "inspect.sock"
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    listener.bind(str(path))
    os.chmod(path, 0o660)
    listener.listen(2)
    try:
        yield root, path, listener, snapshot_path
    finally:
        listener.close()
        path.unlink(missing_ok=True)


def _file_reader(root):
    def read(*, now):
        return file_reader._review_from_directory(
            root,
            owner_uid=os.getuid(),
            expected_gid=os.getgid(),
            now=now,
        )
    return read


def _start(fixture, *, uid=None, reader=None):
    root, path, listener, _ = fixture
    result, errors = [], []
    reader = reader if reader is not None else _file_reader(root)

    def run():
        try:
            result.append(presenter._serve_one_prebound_snapshot_review(
                listener=listener,
                allowed_uid=os.getuid() if uid is None else uid,
                expected_path=path, owner_uid=os.getuid(),
                socket_gid=os.getgid(), reader=reader,
            ))
        except BaseException as exc:
            errors.append(exc)

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return thread, result, errors


def _client(fixture, request):
    _, path, _, _ = fixture
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.settimeout(4)
        client.connect(str(path))
        client.sendall(request)
        client.shutdown(socket.SHUT_WR)
        message = bytearray()
        while True:
            part = client.recv(2048)
            if not part:
                break
            message.extend(part)
    head, body = bytes(message).split(b"\r\n\r\n", 1)
    code = int(head.split(b" ", 2)[1])
    return code, json.loads(body), head


def _wait(thread, result, errors):
    thread.join(6)
    assert not thread.is_alive(), "presenter candidate failed to terminate"
    assert not errors, repr(errors)
    assert len(result) == 1
    return result[0]


@pytest.mark.skipif(os.getuid() == 0, reason="kernel positive UID requires nonroot CI")
def test_real_uds_peer_and_snapshot_roundtrip_stays_blocked(fixture):
    thread, results, errors = _start(fixture)
    code, payload, head = _client(fixture, _REQUEST)
    observed = _wait(thread, results, errors)
    assert code == 200 and observed.http_status == 200
    assert observed.status == "blocked" and observed.snapshot_read
    assert observed.request_accepted and not observed.prepare_eligible
    assert not observed.can_execute and not observed.docker_access_attested
    assert payload == {
        "schema": "atlas.hml.presentation.v1",
        "environment": "hml",
        "service_id": "public-hub",
        "status": "blocked",
        "running_untrusted": True,
        "healthy_untrusted": True,
        "observed_at_untrusted": payload["observed_at_untrusted"],
        "snapshot_origin_attested": False,
        "docker_access_boundary_attested": False,
        "prepare_eligible": False,
        "can_execute": False,
    }
    assert payload["observed_at_untrusted"].endswith("Z")
    assert b"Cache-Control: no-store" in head
    assert "Env" not in str(payload) and "Mounts" not in str(payload)


@pytest.mark.skipif(os.getuid() == 0, reason="kernel positive UID requires nonroot CI")
def test_unhealthy_hml_claim_still_blocked(fixture):
    _, _, _, path = fixture
    doc = json.loads(path.read_text())
    doc["healthy"] = False
    path.write_text(json.dumps(doc))
    os.chmod(path, 0o640)
    thread, results, errors = _start(fixture)
    code, payload, _ = _client(fixture, _REQUEST)
    assert _wait(thread, results, errors).status == "blocked"
    assert code == 200 and not payload["healthy_untrusted"]
    assert payload["status"] == "blocked" and not payload["can_execute"]


@pytest.mark.skipif(os.getuid() == 0, reason="kernel positive UID requires nonroot CI")
@pytest.mark.parametrize("request,status", [
    (b"POST /v1/hml/public-hub/snapshot HTTP/1.1\r\nHost: atlas-hml.local\r\n\r\n", 405),
    (b"DELETE /v1/hml/public-hub/snapshot HTTP/1.1\r\nHost: atlas-hml.local\r\n\r\n", 405),
    (b"HEAD /v1/hml/public-hub/snapshot HTTP/1.1\r\nHost: atlas-hml.local\r\n\r\n", 405),
    (b"GET /v1/prod/public-hub/snapshot HTTP/1.1\r\nHost: atlas-hml.local\r\n\r\n", 404),
    (b"GET /containers/delpi-public-hub/json HTTP/1.1\r\nHost: atlas-hml.local\r\n\r\n", 404),
    (b"GET /v1/hml/public-hub/snapshot?x=1 HTTP/1.1\r\nHost: atlas-hml.local\r\n\r\n", 404),
    (b"GET /v1/hml/public-hub/snapshot HTTP/1.1\r\nHost: attacker\r\n\r\n", 400),
    (b"GET /v1/hml/public-hub/snapshot HTTP/1.1\r\n\r\n", 400),
    (_REQUEST + b"POST /unrelated HTTP/1.1\r\n\r\n", 400),
    (_REQUEST[:-2] + b"Content-Length: 1\r\n\r\nx", 400),
    (_REQUEST[:-2] + b"Authorization: Bearer forbidden\r\n\r\n", 400),
    (_REQUEST[:-2] + b"Transfer-Encoding: chunked\r\n\r\n", 400),
    (_REQUEST[:-2] + b"X-Filler: " + b"x" * 600 + b"\r\n\r\n", 400),
])
def test_method_host_target_body_and_pipelining_denied_before_read(
    fixture, request, status,
):
    calls = []

    def must_not_read(*, now):
        calls.append(now)
        raise AssertionError("reader invoked for rejected request")

    thread, results, errors = _start(fixture, reader=must_not_read)
    code, payload, head = _client(fixture, request)
    result = _wait(thread, results, errors)
    assert code == status
    assert payload == {"error": "HML_PRESENTER_REQUEST_DENIED"}
    assert result.status == "blocked" and not result.request_accepted
    assert not result.snapshot_read and not result.can_execute
    assert not calls
    assert b"Cache-Control: no-store" in head


@pytest.mark.skipif(os.getuid() == 0, reason="kernel UID refusal fixture requires nonroot CI")
def test_kernel_peer_uid_mismatch_is_refused_before_snapshot_read(fixture):
    calls = []

    def must_not_read(*, now):
        calls.append(now)
        raise AssertionError("unexpected read")

    thread, results, errors = _start(
        fixture, reader=must_not_read, uid=os.getuid() + 1,
    )
    code, payload, _ = _client(fixture, _REQUEST)
    result = _wait(thread, results, errors)
    assert code == 403
    assert payload == {"error": "HML_PRESENTER_PEER_DENIED"}
    assert not result.snapshot_read and not calls


@pytest.mark.skipif(os.getuid() == 0, reason="kernel positive UID requires nonroot CI")
@pytest.mark.parametrize("alter", ("missing", "prod", "expired", "symlink", "bad_acl"))
def test_unavailable_or_adulterated_snapshot_is_sanitized(fixture, alter, monkeypatch):
    root, _, _, path = fixture
    if alter == "missing":
        path.unlink()
    elif alter == "prod":
        data = json.loads(path.read_text())
        data["environment"] = "prod"
        path.write_text(json.dumps(data))
        os.chmod(path, 0o640)
    elif alter == "expired":
        data = json.loads(path.read_text())
        data["observed_at"] = (
            datetime.now(timezone.utc) - timedelta(minutes=5)
        ).strftime("%Y-%m-%dT%H:%M:%SZ")
        path.write_text(json.dumps(data))
        os.chmod(path, 0o640)
    elif alter == "symlink":
        target = path.with_name("original")
        path.rename(target)
        path.symlink_to(target)
    else:
        monkeypatch.setattr(file_reader, "has_no_extended_posix_acl", lambda *_args, **_kwargs: False)

    thread, results, errors = _start(fixture)
    code, payload, _ = _client(fixture, _REQUEST)
    result = _wait(thread, results, errors)
    assert code == 503
    assert payload == {"error": "HML_PRESENTER_SNAPSHOT_UNAVAILABLE"}
    assert result.status == "blocked" and result.request_accepted
    assert not result.snapshot_read and not result.can_execute


@pytest.mark.skipif(os.getuid() == 0, reason="kernel positive UID requires nonroot CI")
def test_forged_attestation_is_denied_even_with_synthetic_reader(fixture):
    root, *_ = fixture
    base = _file_reader(root)(now=datetime.now(timezone.utc))
    assert base.status == "blocked"
    forged = replace(base, prepare_eligible=True, can_execute=True)

    thread, results, errors = _start(fixture, reader=lambda *, now: forged)
    code, payload, _ = _client(fixture, _REQUEST)
    result = _wait(thread, results, errors)
    assert code == 503
    assert payload == {"error": "HML_PRESENTER_SNAPSHOT_UNAVAILABLE"}
    assert not result.snapshot_read and not result.can_execute


def test_fixed_path_policy_forbids_injected_reader_without_touching_host():
    with pytest.raises(presenter.HMLSnapshotPresenterError, match="HML_PRESENTER_IDENTITY_UNVERIFIABLE|HML_PRESENTER_POLICY_UNVERIFIABLE"):
        presenter._serve_one_prebound_snapshot_review(
            listener=object(),
            allowed_uid=1,
            expected_path=presenter._FIXED_SOCKET,
            owner_uid=1, socket_gid=1,
            reader=lambda *, now: None,
        )


def test_non_listening_fd_and_bad_owner_refused_before_accept(fixture):
    root, path, listener, _ = fixture
    with pytest.raises(presenter.HMLSnapshotPresenterError, match="HML_PRESENTER_LISTENER_UNTRUSTED"):
        presenter._serve_one_prebound_snapshot_review(
            listener=listener, allowed_uid=max(1, os.getuid()),
            expected_path=path, owner_uid=os.getuid() + 1,
            socket_gid=os.getgid(), reader=_file_reader(root),
        )


def test_module_exposes_no_entrypoint_or_docker_transport():
    for name in ("main", "create_mcp_server", "get_docker_client", "bind_listener", "deploy", "start_service"):
        assert not hasattr(presenter, name)
    assert not hasattr(presenter, "HMLDockerInspectOnly")
    assert not hasattr(presenter, "httpx")

"""Disposable end-to-end architecture B chain (fixtures only, no host install).

Covers: signed produce -> atomic publish -> FD read -> trust verify ->
continuity store across restart -> lifecycle latch -> presenter UDS GET ->
denials for method/PROD -> integrity faults never grant PREPARE/ACT.
"""
from __future__ import annotations

import json
import os
import socket
import threading
from datetime import datetime, timezone

import pytest

from linux_ops_mcp import atlas_hml_snapshot_file_reader as file_reader
from linux_ops_mcp import atlas_hml_snapshot_presenter_candidate as presenter
from linux_ops_mcp.atlas_hml_b_continuity_store import (
    HMLContinuityRecord,
    HMLContinuityStore,
    HMLContinuityStoreError,
)
from linux_ops_mcp.atlas_hml_b_lifecycle import (
    HMLLifecycleError,
    HMLLifecycleState,
    HMLLifecycleSupervisor,
)
from linux_ops_mcp.atlas_hml_b_signed_producer import publish_signed_hml_bundle
from linux_ops_mcp.atlas_hml_b_snapshot_file_session import HMLSnapshotFileSession
from linux_ops_mcp.atlas_hml_b_snapshot_trust import (
    HMLSnapshotTrustError,
    build_keyring,
    generate_fixture_keypair,
    verify_signed_snapshot_envelope,
)
from linux_ops_mcp.deploy_host_source import RuntimeContainer

_NOW = datetime(2026, 11, 17, 21, 0, tzinfo=timezone.utc)
_CONTAINER = RuntimeContainer(
    container_id="a" * 64,
    image_id="sha256:" + "b" * 64,
    running=True,
    healthy=True,
)
_GET = (
    b"GET /v1/hml/public-hub/snapshot HTTP/1.1\r\n"
    b"Host: atlas-hml.local\r\n\r\n"
)


@pytest.fixture
def disposable(tmp_path):
    root = tmp_path / "atlas-b-e2e"
    root.mkdir()
    os.chmod(root, 0o750)
    private, public, key_id = generate_fixture_keypair()
    ring = build_keyring(active=((key_id, public),))
    return {
        "root": root,
        "private": private,
        "public": public,
        "key_id": key_id,
        "ring": ring,
        "uid": os.getuid(),
        "gid": os.getgid(),
    }


def _reader(root):
    def read(*, now):
        return file_reader._review_from_directory(
            root,
            owner_uid=os.getuid(),
            expected_gid=os.getgid(),
            now=now,
        )
    return read


def _exchange(root, request: bytes):
    path = root / "inspect.sock"
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    listener.bind(str(path))
    os.chmod(path, 0o660)
    listener.listen(1)
    result, errors = [], []

    def run():
        try:
            result.append(presenter._serve_one_prebound_snapshot_review(
                listener=listener,
                allowed_uid=os.getuid(),
                expected_path=path,
                owner_uid=os.getuid(),
                socket_gid=os.getgid(),
                reader=_reader(root),
            ))
        except BaseException as exc:
            errors.append(exc)
        finally:
            listener.close()

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
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
    thread.join(6)
    path.unlink(missing_ok=True)
    assert not thread.is_alive()
    assert not errors, repr(errors)
    assert len(result) == 1
    head, body = bytes(message).split(b"\r\n\r\n", 1)
    code = int(head.split(b" ", 2)[1])
    return code, json.loads(body), result[0]


@pytest.mark.skipif(os.getuid() == 0, reason="peer UID fixtures require non-root")
def test_signed_publish_fd_trust_continuity_lifecycle_and_uds(disposable):
    root = disposable["root"]
    # Wall clock keeps mtime/TTL/observed_at coherent for FD reader + presenter.
    now = datetime.now(timezone.utc).replace(microsecond=0)
    receipt = publish_signed_hml_bundle(
        _CONTAINER,
        directory=root,
        owner_uid=disposable["uid"],
        expected_gid=disposable["gid"],
        observed_at=now,
        generation=1,
        private_key=disposable["private"],
        public_key=disposable["public"],
    )
    assert receipt.status == "blocked"
    assert not receipt.authenticity_independent
    assert not receipt.prepare_eligible and not receipt.can_execute

    envelope = (root / "inspect-snapshot.envelope.v1.json").read_bytes()
    trusted = verify_signed_snapshot_envelope(
        envelope, now=now, keyring=disposable["ring"],
    )
    assert trusted.signature_verified
    assert trusted.envelope.diagnostic.status == "blocked"
    assert not trusted.can_execute

    record = file_reader._read_record_from_directory(
        root, owner_uid=disposable["uid"], expected_gid=disposable["gid"], now=now,
    )
    session = HMLSnapshotFileSession()
    observed = session.observe(record, now=now, monotonic_ns=100)
    assert observed.fixture_continuity_ok and not observed.can_execute

    store = HMLContinuityStore(
        root, owner_uid=disposable["uid"], expected_gid=disposable["gid"],
    )
    store.commit(HMLContinuityRecord(
        generation=1,
        digest=trusted.envelope.payload_sha256,
        observed_at=now,
        container_id=_CONTAINER.container_id,
        image_id=_CONTAINER.image_id,
        updated_at=now,
    ))
    restarted = HMLContinuityStore(
        root, owner_uid=disposable["uid"], expected_gid=disposable["gid"],
    )
    with pytest.raises(HMLContinuityStoreError) as err:
        restarted.commit(HMLContinuityRecord(
            generation=1,
            digest=trusted.envelope.payload_sha256,
            observed_at=now,
            container_id=_CONTAINER.container_id,
            image_id=_CONTAINER.image_id,
            updated_at=now,
        ))
    assert err.value.code == "HML_CONTINUITY_STORE_REPLAY"

    life = HMLLifecycleSupervisor()
    life.mark_available()
    life.mark_integrity_compromised()
    assert life.state is HMLLifecycleState.RECOVERY_BLOCKED
    with pytest.raises(HMLLifecycleError):
        life.attempt_recovery()

    code, body, presentation = _exchange(root, _GET)
    assert code == 200
    assert body["status"] == "blocked"
    assert presentation.status == "blocked"
    assert not getattr(presentation, "prepare_eligible", False)
    assert not getattr(presentation, "can_execute", False)


@pytest.mark.skipif(os.getuid() == 0, reason="peer UID fixtures require non-root")
def test_write_method_and_prod_path_denied(disposable):
    root = disposable["root"]
    publish_signed_hml_bundle(
        _CONTAINER,
        directory=root,
        owner_uid=disposable["uid"],
        expected_gid=disposable["gid"],
        observed_at=datetime.now(timezone.utc).replace(microsecond=0),
        generation=1,
        private_key=disposable["private"],
        public_key=disposable["public"],
    )
    write_code, write_body, write_pres = _exchange(
        root,
        b"POST /v1/hml/public-hub/snapshot HTTP/1.1\r\n"
        b"Host: atlas-hml.local\r\nContent-Length: 0\r\n\r\n",
    )
    assert write_code != 200
    assert write_pres.status == "blocked"
    assert not write_body.get("prepare_eligible", False)

    prod_code, prod_body, prod_pres = _exchange(
        root,
        b"GET /v1/prod/public-hub/snapshot HTTP/1.1\r\n"
        b"Host: atlas-hml.local\r\n\r\n",
    )
    assert prod_code != 200
    assert prod_pres.status == "blocked"
    assert not prod_body.get("can_execute", False)


def test_bad_signature_latches_lifecycle_without_prepare(disposable):
    root = disposable["root"]
    publish_signed_hml_bundle(
        _CONTAINER,
        directory=root,
        owner_uid=disposable["uid"],
        expected_gid=disposable["gid"],
        observed_at=_NOW,
        generation=1,
        private_key=disposable["private"],
        public_key=disposable["public"],
    )
    envelope = bytearray((root / "inspect-snapshot.envelope.v1.json").read_bytes())
    # Corrupt signature section while keeping JSON mostly parseable.
    marker = b'"signature_b64":"'
    idx = envelope.find(marker)
    assert idx > 0
    envelope[idx + len(marker)] = ord("A") if envelope[idx + len(marker)] != ord("A") else ord("B")
    with pytest.raises(HMLSnapshotTrustError):
        verify_signed_snapshot_envelope(
            bytes(envelope), now=_NOW, keyring=disposable["ring"],
        )
    life = HMLLifecycleSupervisor()
    life.mark_available()
    life.mark_failure("SNAPSHOT_INVALID")
    assert life.state is HMLLifecycleState.RECOVERY_BLOCKED
    assert not life.diagnose().prepare_eligible
    assert not life.diagnose().can_execute

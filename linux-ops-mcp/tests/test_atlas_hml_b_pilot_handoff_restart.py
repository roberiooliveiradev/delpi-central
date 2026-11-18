"""ATLAS HML B: persisted signer restarts and separate-process UDS bridge.

Disposable tmp directories, ephemerally generated keys, runner-local Unix
sockets and subprocesses only. No production Docker, systemd, GLPI or /run.
"""
from __future__ import annotations

import base64
import os
import socket
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone

import pytest

from linux_ops_mcp.atlas_hml_b_continuity_store import HMLContinuityStore
from linux_ops_mcp.atlas_hml_b_external_signing_intent import (
    prepare_signing_intent, seal_externally_signed_intent,
)
from linux_ops_mcp.atlas_hml_b_key_lifecycle import (
    generate_ephemeral_keypair, write_ephemeral_private_key,
)
from linux_ops_mcp.atlas_hml_b_local_signer import HMLLocalSigner, HMLLocalSignerError
from linux_ops_mcp.atlas_hml_b_nonroot_sign_bridge import (
    HMLNonrootBridgeError, build_nonroot_signing_intent,
    request_signature_via_nonroot_uds,
)
from linux_ops_mcp.atlas_hml_b_snapshot_trust import build_keyring
from linux_ops_mcp.atlas_hml_snapshot_publisher_candidate import (
    _publish_in_review_directory, build_hml_snapshot_claim,
)
from linux_ops_mcp.deploy_host_source import RuntimeContainer

_NOW = datetime.now(timezone.utc).replace(microsecond=0)
_HML = RuntimeContainer(
    container_id="a" * 64, image_id="sha256:" + "b" * 64,
    running=True, healthy=True,
)


@pytest.fixture
def setup(tmp_path):
    keys = generate_ephemeral_keypair()
    key_dir = tmp_path / "keys"
    key_dir.mkdir()
    key_dir.chmod(0o700)
    private_path = write_ephemeral_private_key(
        key_dir, keys, owner_uid=os.getuid(), expected_gid=os.getgid(),
    )
    state_dir = tmp_path / "signer-state"
    state_dir.mkdir()
    state_dir.chmod(0o750)
    handoff = tmp_path / "handoff"
    handoff.mkdir()
    handoff.chmod(0o750)
    return keys, private_path, state_dir, handoff


def signer(setup, *, disposable_genesis=False):
    keys, private, state_dir, _ = setup
    checkpoint = HMLContinuityStore(
        state_dir, owner_uid=os.getuid(), expected_gid=os.getgid(),
    )
    return HMLLocalSigner.from_key_file(
        private, public_key=keys.public_key,
        owner_uid=os.getuid(), expected_gid=os.getgid(),
        allowed_peer_uids=frozenset({max(1, os.getuid())}),
        checkpoint_store=checkpoint,
        disposable_genesis=disposable_genesis,
    )


@pytest.mark.skipif(os.getuid() == 0, reason="nonroot signer peer UID required")
def test_genesis_is_explicit_and_restart_reuses_persisted_generation(setup):
    keys, _, _, _ = setup
    with pytest.raises(HMLLocalSignerError) as e:
        signer(setup)
    assert e.value.code == "HML_LOCAL_SIGNER_BOOTSTRAP_REVIEW_REQUIRED"

    first = signer(setup, disposable_genesis=True)
    intent1 = prepare_signing_intent(
        _HML, observed_at=_NOW, generation=1, key_id=keys.key_id,
    )
    out1 = first.sign_intent(
        intent1, now=_NOW, peer_uid=os.getuid(), expected_generation=1,
    )
    assert out1.status == "blocked"
    assert not out1.can_execute and not out1.prepare_eligible
    assert not out1.authenticity_independent
    persisted = HMLContinuityStore(
        setup[2], owner_uid=os.getuid(), expected_gid=os.getgid(),
    ).load()
    assert persisted is not None and persisted.generation == 1

    after_restart = signer(setup)
    intent2 = prepare_signing_intent(
        _HML, observed_at=_NOW + timedelta(seconds=1),
        generation=2, key_id=keys.key_id,
    )
    out2 = after_restart.sign_intent(
        intent2, now=_NOW + timedelta(seconds=1),
        peer_uid=os.getuid(), expected_generation=2,
    )
    assert out2.generation == 2
    ring = build_keyring(active=((keys.key_id, keys.public_key),))
    assert seal_externally_signed_intent(
        intent2, signature=out2.signature, keyring=ring,
        now=_NOW + timedelta(seconds=1),
    ).signature_verified
    assert signer(setup)._last_generation == 2
    with pytest.raises(HMLLocalSignerError) as e:
        signer(setup).sign_intent(
            intent2, now=_NOW + timedelta(seconds=1),
            peer_uid=os.getuid(), expected_generation=2,
        )
    assert e.value.code == "HML_LOCAL_SIGNER_GENERATION_REGRESSION"


@pytest.mark.skipif(os.getuid() == 0, reason="nonroot signer peer UID required")
def test_missing_or_corrupt_checkpoint_denies_restart(setup):
    keys = setup[0]
    initial = signer(setup, disposable_genesis=True)
    intent = prepare_signing_intent(
        _HML, observed_at=_NOW, generation=1, key_id=keys.key_id,
    )
    initial.sign_intent(intent, now=_NOW, peer_uid=os.getuid(), expected_generation=1)
    state_path = setup[2] / "continuity-state.v1.json"
    state_path.unlink()
    with pytest.raises(HMLLocalSignerError) as e:
        signer(setup)
    assert e.value.code == "HML_LOCAL_SIGNER_BOOTSTRAP_REVIEW_REQUIRED"
    state_path.write_bytes(b'{"schema":"tampered"}')
    state_path.chmod(0o640)
    with pytest.raises(HMLLocalSignerError) as e:
        signer(setup)
    assert e.value.code == "HML_LOCAL_SIGNER_CHECKPOINT_UNTRUSTED"


@pytest.mark.skipif(os.getuid() == 0, reason="nonroot signer peer UID required")
def test_competing_signers_same_generation_no_second_signature(setup):
    keys = setup[0]
    first = signer(setup, disposable_genesis=True)
    intent = prepare_signing_intent(
        _HML, observed_at=_NOW, generation=1, key_id=keys.key_id,
    )
    second = signer(setup, disposable_genesis=True)
    first.sign_intent(intent, now=_NOW, peer_uid=os.getuid(), expected_generation=1)
    with pytest.raises(HMLLocalSignerError) as e:
        second.sign_intent(
            intent, now=_NOW, peer_uid=os.getuid(), expected_generation=1,
        )
    assert e.value.code == "HML_LOCAL_SIGNER_CHECKPOINT_UNTRUSTED"
    assert second.halted


@pytest.mark.skipif(os.getuid() == 0, reason="nonroot signer peer UID required")
def test_checkpoint_failure_never_returns_signature(setup, monkeypatch):
    keys = setup[0]
    guarded = signer(setup, disposable_genesis=True)
    def no_write(*args, **kwargs):
        from linux_ops_mcp.atlas_hml_b_continuity_store import HMLContinuityStoreError
        raise HMLContinuityStoreError("HML_CONTINUITY_STORE_WRITE_FAILED")
    monkeypatch.setattr(guarded._checkpoint_store, "commit", no_write)
    with pytest.raises(HMLLocalSignerError) as e:
        guarded.sign_intent(
            prepare_signing_intent(
                _HML, observed_at=_NOW, generation=1, key_id=keys.key_id,
            ),
            now=_NOW, peer_uid=os.getuid(), expected_generation=1,
        )
    assert e.value.code == "HML_LOCAL_SIGNER_CHECKPOINT_UNTRUSTED"
    assert guarded.halted
    assert not (setup[2] / "continuity-state.v1.json").exists()


@pytest.mark.skipif(os.getuid() == 0, reason="nonroot bridge required")
def test_bridge_handoff_rejects_prod_and_stale(setup):
    keys, _, _, handoff = setup
    claim = build_hml_snapshot_claim(_HML, observed_at=_NOW)
    _publish_in_review_directory(
        handoff, raw=claim, owner_uid=os.getuid(),
        expected_gid=os.getgid(), now=_NOW,
    )
    intent = build_nonroot_signing_intent(
        directory=handoff, owner_uid=os.getuid(), expected_gid=os.getgid(),
        generation=1, key_id=keys.key_id, now=_NOW,
    )
    assert intent.status == "blocked"
    assert b"prod" not in intent.signing_bytes[:25]
    with pytest.raises(HMLNonrootBridgeError) as e:
        build_nonroot_signing_intent(
            directory=handoff, owner_uid=os.getuid(), expected_gid=os.getgid(),
            generation=1, key_id=keys.key_id,
            now=_NOW + timedelta(minutes=3),
        )
    assert e.value.code == "HML_BRIDGE_CLAIM_UNTRUSTED"

    tampered = claim.replace(b'"environment":"hml"', b'"environment":"prod"')
    # Simulate an uncooperative writer bypassing the safe producer API.
    # The bridge must refuse the modified bytes during its own FD read.
    (handoff / "inspect-snapshot.json").write_bytes(tampered)
    (handoff / "inspect-snapshot.json").chmod(0o640)
    with pytest.raises(HMLNonrootBridgeError):
        build_nonroot_signing_intent(
            directory=handoff, owner_uid=os.getuid(), expected_gid=os.getgid(),
            generation=1, key_id=keys.key_id, now=_NOW,
        )


@pytest.mark.skipif(os.getuid() == 0, reason="nonroot bridge required")
def test_bridge_refuses_root_and_unverified_identity(monkeypatch, setup):
    import linux_ops_mcp.atlas_hml_b_nonroot_sign_bridge as bridge
    monkeypatch.setattr(bridge.os, "getresuid", lambda: (0, 0, 0))
    with pytest.raises(HMLNonrootBridgeError) as e:
        build_nonroot_signing_intent(
            directory=setup[3], owner_uid=os.getuid(),
            expected_gid=os.getgid(), generation=1,
            key_id=setup[0].key_id, now=_NOW,
        )
    assert e.value.code == "HML_BRIDGE_NOT_UNPRIVILEGED"


_SERVER_CODE = r"""
import base64
import os
import socket
import sys
from datetime import datetime
from pathlib import Path
from linux_ops_mcp.atlas_hml_b_continuity_store import HMLContinuityStore
from linux_ops_mcp.atlas_hml_b_local_signer import HMLLocalSigner, _serve_one_local_sign_request

keypath, public, socketpath, statepath, now_iso, generation, genesis = sys.argv[1:]
public = base64.b64decode(public)
signer = HMLLocalSigner.from_key_file(
    Path(keypath), public_key=public,
    owner_uid=os.getuid(), expected_gid=os.getgid(),
    allowed_peer_uids=frozenset({os.getuid()}),
    checkpoint_store=HMLContinuityStore(
        Path(statepath), owner_uid=os.getuid(), expected_gid=os.getgid(),
    ),
    disposable_genesis=(genesis == "true"),
)
listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
listener.bind(socketpath)
os.chmod(socketpath, 0o660)
listener.listen(1)
try:
    _serve_one_local_sign_request(
        listener=listener, signer=signer, expected_path=Path(socketpath),
        now=datetime.fromisoformat(now_iso), expected_generation=int(generation),
    )
finally:
    listener.close()
"""


@pytest.mark.skipif(os.getuid() == 0 or not sys.platform.startswith("linux"),
                    reason="disposable Linux nonroot process fixture only")
def test_two_subprocess_roundtrips_with_restart_and_peer_uid(setup, tmp_path):
    keys, private, state_dir, handoff = setup
    ring = build_keyring(active=((keys.key_id, keys.public_key),))
    socket_path = tmp_path / "sign.sock"
    for generation in (1, 2):
        when = _NOW + timedelta(seconds=generation - 1)
        _publish_in_review_directory(
            handoff, raw=build_hml_snapshot_claim(_HML, observed_at=when),
            owner_uid=os.getuid(), expected_gid=os.getgid(), now=when,
        )
        intent = build_nonroot_signing_intent(
            directory=handoff, owner_uid=os.getuid(),
            expected_gid=os.getgid(), generation=generation,
            key_id=keys.key_id, now=when,
        )
        try:
            socket_path.unlink()
        except FileNotFoundError:
            pass
        child = subprocess.Popen(
            [sys.executable, "-B", "-c", _SERVER_CODE, str(private),
             base64.b64encode(keys.public_key).decode("ascii"),
             str(socket_path), str(state_dir),
             when.isoformat(), str(generation),
             "true" if generation == 1 else "false"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
        try:
            for _ in range(100):
                if socket_path.exists() or child.poll() is not None:
                    break
                time.sleep(0.03)
            assert child.poll() is None and socket_path.exists()
            with pytest.raises(HMLNonrootBridgeError) as e:
                request_signature_via_nonroot_uds(
                    intent, socket_path=socket_path,
                    expected_socket_owner_uid=os.getuid(),
                    expected_socket_gid=os.getgid(),
                    expected_signer_uid=os.getuid(),
                    keyring=ring, now=when,
                )
            assert e.value.code == "HML_BRIDGE_POLICY_DENIED"
            reviewed = request_signature_via_nonroot_uds(
                intent, socket_path=socket_path,
                expected_socket_owner_uid=os.getuid(),
                expected_socket_gid=os.getgid(),
                expected_signer_uid=os.getuid(),
                keyring=ring, now=when,
                disposable_same_uid_fixture=True,
            )
            assert reviewed.status == "blocked"
            assert reviewed.signer_peer_verified_in_fixture
            assert not reviewed.host_isolation_attested
            assert not reviewed.can_execute and not reviewed.prepare_eligible
            assert child.wait(timeout=8) == 0
            assert HMLContinuityStore(
                state_dir, owner_uid=os.getuid(), expected_gid=os.getgid(),
            ).load().generation == generation
        finally:
            if child.poll() is None:
                child.kill()
                child.wait(timeout=3)

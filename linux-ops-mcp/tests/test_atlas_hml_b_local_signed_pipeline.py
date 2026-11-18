"""Integrated local-signing pipeline tests on disposable directories."""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import pytest

from linux_ops_mcp.atlas_hml_b_continuity_store import HMLContinuityStore
from linux_ops_mcp.atlas_hml_b_key_lifecycle import (
    generate_ephemeral_keypair,
    rotate_keyring,
    write_ephemeral_private_key,
)
from linux_ops_mcp.atlas_hml_b_lifecycle import (
    HMLLifecycleState,
    HMLLifecycleSupervisor,
)
from linux_ops_mcp.atlas_hml_b_local_signer import HMLLocalSigner
from linux_ops_mcp.atlas_hml_b_local_signed_pipeline import (
    HMLLocalPipelineError,
    run_local_signed_hml_pipeline,
)
from linux_ops_mcp.atlas_hml_b_snapshot_trust import (
    build_keyring,
    verify_signed_snapshot_envelope,
)
from linux_ops_mcp.deploy_host_source import RuntimeContainer

_CONTAINER = RuntimeContainer(
    container_id="a" * 64,
    image_id="sha256:" + "b" * 64,
    running=True,
    healthy=True,
)


@pytest.fixture
def env(tmp_path):
    root = tmp_path / "pipeline"
    root.mkdir()
    os.chmod(root, 0o750)
    keys_dir = tmp_path / "keys"
    keys_dir.mkdir()
    os.chmod(keys_dir, 0o700)
    keys = generate_ephemeral_keypair()
    priv = write_ephemeral_private_key(
        keys_dir, keys, owner_uid=os.getuid(), expected_gid=os.getgid(),
    )
    signer = HMLLocalSigner.from_key_file(
        priv, public_key=keys.public_key,
        owner_uid=os.getuid(), expected_gid=os.getgid(),
        allowed_peer_uids=frozenset({os.getuid()}),
    )
    ring = build_keyring(active=((keys.key_id, keys.public_key),))
    store = HMLContinuityStore(
        root, owner_uid=os.getuid(), expected_gid=os.getgid(),
    )
    return {
        "root": root, "keys": keys, "signer": signer, "ring": ring,
        "store": store, "uid": os.getuid(), "gid": os.getgid(),
    }


def test_full_pipeline_sign_publish_verify_continuity(env):
    now = datetime.now(timezone.utc).replace(microsecond=0)
    life = HMLLifecycleSupervisor()
    result = run_local_signed_hml_pipeline(
        _CONTAINER,
        directory=env["root"],
        owner_uid=env["uid"],
        expected_gid=env["gid"],
        observed_at=now,
        generation=1,
        signer=env["signer"],
        keyring=env["ring"],
        peer_uid=env["uid"],
        continuity=env["store"],
        lifecycle=life,
    )
    assert result.status == "blocked"
    assert result.signature_verified
    assert not result.authenticity_independent
    assert not result.prepare_eligible and not result.can_execute
    assert (env["root"] / "inspect-snapshot.json").is_file()
    assert (env["root"] / "inspect-snapshot.envelope.v1.json").is_file()
    verified = verify_signed_snapshot_envelope(
        result.envelope, now=now, keyring=env["ring"],
    )
    assert verified.signature_verified
    # Restart simulation: replay generation 1 must fail closed.
    restarted = HMLContinuityStore(
        env["root"], owner_uid=env["uid"], expected_gid=env["gid"],
    )
    with pytest.raises(HMLLocalPipelineError) as err:
        run_local_signed_hml_pipeline(
            _CONTAINER,
            directory=env["root"],
            owner_uid=env["uid"],
            expected_gid=env["gid"],
            observed_at=now + timedelta(seconds=5),
            generation=1,
            signer=env["signer"],
            keyring=env["ring"],
            peer_uid=env["uid"],
            continuity=restarted,
            lifecycle=HMLLifecycleSupervisor(),
        )
    assert err.value.code in {
        "HML_LOCAL_SIGNER_REPLAY",
        "HML_CONTINUITY_STORE_REPLAY",
        "HML_LOCAL_SIGNER_GENERATION_REGRESSION",
    }


def test_tampered_envelope_after_sign_denied(env):
    now = datetime.now(timezone.utc).replace(microsecond=0)
    result = run_local_signed_hml_pipeline(
        _CONTAINER,
        directory=env["root"],
        owner_uid=env["uid"],
        expected_gid=env["gid"],
        observed_at=now,
        generation=1,
        signer=env["signer"],
        keyring=env["ring"],
        peer_uid=env["uid"],
    )
    tampered = bytearray(result.envelope)
    idx = tampered.find(b"signature_b64")
    tampered[idx + 20] = ord("A") if tampered[idx + 20] != ord("A") else ord("B")
    with pytest.raises(Exception):
        verify_signed_snapshot_envelope(
            bytes(tampered), now=now, keyring=env["ring"],
        )


def test_key_rotation_old_signature_rejected_new_accepted(env, tmp_path):
    now = datetime.now(timezone.utc).replace(microsecond=0)
    run_local_signed_hml_pipeline(
        _CONTAINER,
        directory=env["root"],
        owner_uid=env["uid"],
        expected_gid=env["gid"],
        observed_at=now,
        generation=1,
        signer=env["signer"],
        keyring=env["ring"],
        peer_uid=env["uid"],
        continuity=env["store"],
    )
    successor = generate_ephemeral_keypair()
    keys_dir = tmp_path / "keys2"
    keys_dir.mkdir()
    os.chmod(keys_dir, 0o700)
    priv = write_ephemeral_private_key(
        keys_dir, successor, owner_uid=env["uid"], expected_gid=env["gid"],
    )
    new_signer = HMLLocalSigner.from_key_file(
        priv, public_key=successor.public_key,
        owner_uid=env["uid"], expected_gid=env["gid"],
        allowed_peer_uids=frozenset({env["uid"]}),
    )
    rotated = rotate_keyring(previous=env["keys"], successor=successor)
    root2 = tmp_path / "pipeline2"
    root2.mkdir()
    os.chmod(root2, 0o750)
    store2 = HMLContinuityStore(
        root2, owner_uid=env["uid"], expected_gid=env["gid"],
    )
    # Fresh signer process starts at generation 1 for its own counter.
    ok = run_local_signed_hml_pipeline(
        _CONTAINER,
        directory=root2,
        owner_uid=env["uid"],
        expected_gid=env["gid"],
        observed_at=now + timedelta(seconds=10),
        generation=1,
        signer=new_signer,
        keyring=rotated,
        peer_uid=env["uid"],
        continuity=store2,
    )
    assert ok.signature_verified and ok.key_id == successor.key_id
    # Old key id is revoked in rotated keyring.
    with pytest.raises(Exception):
        rotated.active_public(env["keys"].key_id)


def test_publish_failure_does_not_enable_prepare(env, monkeypatch):
    now = datetime.now(timezone.utc).replace(microsecond=0)
    life = HMLLifecycleSupervisor()

    def boom(*args, **kwargs):
        from linux_ops_mcp.atlas_hml_snapshot_publisher_candidate import (
            HMLSnapshotPublishError,
        )
        raise HMLSnapshotPublishError("HML_SNAPSHOT_PUBLISH_UNAVAILABLE")

    monkeypatch.setattr(
        "linux_ops_mcp.atlas_hml_b_local_signed_pipeline._publish_in_review_directory",
        boom,
    )
    with pytest.raises(HMLLocalPipelineError):
        run_local_signed_hml_pipeline(
            _CONTAINER,
            directory=env["root"],
            owner_uid=env["uid"],
            expected_gid=env["gid"],
            observed_at=now,
            generation=1,
            signer=env["signer"],
            keyring=env["ring"],
            peer_uid=env["uid"],
            lifecycle=life,
        )
    assert life.state in {
        HMLLifecycleState.FAILED, HMLLifecycleState.RECOVERY_BLOCKED,
    }
    assert not life.diagnose().prepare_eligible
    assert not life.diagnose().can_execute

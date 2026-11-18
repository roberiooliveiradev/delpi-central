"""ATLAS Etapas 66-69 disposable tests: chain, bootstrap, recovery, units, preflight."""
from __future__ import annotations

import json
import os
import socket
import stat
import threading
from datetime import datetime, timezone

import pytest

from linux_ops_mcp.atlas_hml_b_bootstrap_control import (
    HMLBootstrapControlError,
    reject_absence_as_genesis,
    review_untrusted_bootstrap_dossier,
)
from linux_ops_mcp.atlas_hml_b_candidate_unit_review import (
    HMLCandidateUnitError,
    review_candidate_unit_sources,
)
from linux_ops_mcp.atlas_hml_b_chain_orchestrator import (
    HMLChainOrchestratorError,
    run_bridge_signed_chain_fixture,
)
from linux_ops_mcp.atlas_hml_b_counter_recovery import (
    HMLCounterRecoveryError,
    assert_generation_floor,
    review_untrusted_counter_recovery,
)
from linux_ops_mcp.atlas_hml_b_external_signing_intent import prepare_signing_intent
from linux_ops_mcp.atlas_hml_b_handoff_checklist import build_stage66_69_handoff_checklist
from linux_ops_mcp.atlas_hml_b_key_lifecycle import generate_ephemeral_keypair
from linux_ops_mcp.atlas_hml_b_local_signer import HMLLocalSigner
from linux_ops_mcp.atlas_hml_b_preflight_bundle import (
    HMLPreflightBundleError,
    review_untrusted_preflight_bundle,
)
from linux_ops_mcp.atlas_hml_b_signed_presenter import (
    HMLSignedPresenterError,
    present_verified_signed_envelope,
)
from linux_ops_mcp.atlas_hml_b_signer_listen import (
    HMLSignerListenError,
    bind_signer_owned_socket,
)
from linux_ops_mcp.atlas_hml_b_snapshot_trust import (
    build_keyring,
    sign_snapshot_envelope,
    verify_signed_snapshot_envelope,
)
from linux_ops_mcp.deploy_host_source import RuntimeContainer

def _now() -> datetime:
    return datetime.now(timezone.utc)
_CONTAINER = RuntimeContainer(
    container_id="a" * 64,
    image_id="sha256:" + "b" * 64,
    running=True,
    healthy=True,
)
_SHA = "8db122c0a50196d9124c936645f46cd912ade164"


@pytest.mark.skipif(os.getuid() == 0, reason="non-root fixtures")
def test_signer_binds_after_nonroot_and_rejects_existing_path(tmp_path):
    parent = tmp_path / "signer-sock"
    parent.mkdir()
    os.chmod(parent, 0o2750)
    path = parent / "sign.sock"
    keys = generate_ephemeral_keypair()
    signer = HMLLocalSigner(
        private_key=keys.private_key,
        public_key=keys.public_key,
        allowed_peer_uids=frozenset({os.getuid()}),
    )
    listener = bind_signer_owned_socket(
        socket_path=path, owner_uid=os.getuid(), socket_gid=os.getgid(),
    )
    try:
        assert listener.getsockopt(socket.SOL_SOCKET, socket.SO_ACCEPTCONN) == 1
        st = os.stat(path, follow_symlinks=False)
        assert stat.S_ISSOCK(st.st_mode)
        assert st.st_uid == os.getuid()
        assert stat.S_IMODE(st.st_mode) == 0o660
        with pytest.raises(HMLSignerListenError) as exc:
            bind_signer_owned_socket(
                socket_path=path, owner_uid=os.getuid(), socket_gid=os.getgid(),
            )
        assert exc.value.code == "HML_SIGNER_LISTEN_PATH_EXISTS"
    finally:
        listener.close()
        path.unlink(missing_ok=True)


@pytest.mark.skipif(os.getuid() == 0, reason="non-root fixtures")
def test_signer_listen_bind_and_signed_presenter(tmp_path):
    parent = tmp_path / "sock"
    parent.mkdir()
    os.chmod(parent, 0o2750)
    path = parent / "sign.sock"
    keys = generate_ephemeral_keypair()
    ring = build_keyring(active=((keys.key_id, keys.public_key),))
    now = _now()
    intent = prepare_signing_intent(
        _CONTAINER, observed_at=now, generation=1, key_id=keys.key_id,
    )
    listener = bind_signer_owned_socket(
        socket_path=path, owner_uid=os.getuid(), socket_gid=os.getgid(),
    )
    listener.settimeout(2.0)
    signer = HMLLocalSigner(
        private_key=keys.private_key,
        public_key=keys.public_key,
        allowed_peer_uids=frozenset({os.getuid()}),
    )
    from linux_ops_mcp.atlas_hml_b_local_signer import (
        _serve_one_local_sign_request,
        encode_local_sign_request,
    )
    errors: list[object] = []

    def server():
        try:
            _serve_one_local_sign_request(
                listener=listener, signer=signer, expected_path=path,
                now=now, expected_generation=1,
            )
        except Exception as exc:  # noqa: BLE001
            errors.append(getattr(exc, "code", str(exc)))
        finally:
            try:
                listener.close()
            except OSError:
                pass

    thread = threading.Thread(target=server, daemon=True)
    thread.start()
    conn = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    conn.settimeout(2.0)
    conn.connect(str(path))
    conn.sendall(encode_local_sign_request(intent))
    conn.shutdown(socket.SHUT_WR)
    data = conn.recv(4096)
    conn.close()
    thread.join(timeout=3.0)
    path.unlink(missing_ok=True)
    assert b"signature_b64" in data
    assert not errors
    envelope = sign_snapshot_envelope(
        intent.payload, generation=1, produced_at=now,
        private_key=keys.private_key, public_key=keys.public_key,
    )
    presented = present_verified_signed_envelope(envelope, keyring=ring, now=now)
    assert presented.status == "blocked"
    assert presented.signature_verified
    assert not presented.can_execute
    assert not presented.prepare_eligible
    bad = bytearray(envelope)
    bad[-1] ^= 0x01
    with pytest.raises(HMLSignedPresenterError):
        present_verified_signed_envelope(bytes(bad), keyring=ring, now=now)


@pytest.mark.skipif(os.getuid() == 0, reason="non-root bridge/signer fixtures")
def test_bridge_signed_chain_fixture(tmp_path):
    claim = tmp_path / "claim"
    sock = tmp_path / "sock"
    claim.mkdir()
    sock.mkdir()
    os.chmod(claim, 0o750)
    os.chmod(sock, 0o750)
    result = run_bridge_signed_chain_fixture(
        _CONTAINER,
        claim_directory=claim,
        socket_directory=sock,
        owner_uid=os.getuid(),
        expected_gid=os.getgid(),
        socket_gid=os.getgid(),
        generation=1,
        observed_at=_now(),
        disposable_same_uid_fixture=True,
    )
    assert result.bridge_used
    # Fixture listener is pre-bound by the orchestrator (same UID), never signer-owned bind.
    assert not result.signer_self_bound
    assert not result.authenticity_independent
    assert result.signature_verified
    assert result.status == "blocked"
    assert not result.can_execute


def _bootstrap_doc(**overrides):
    doc = {
        "schema": "atlas.hml.b.bootstrap-control.v1",
        "host": "srv-api",
        "environment": "hml",
        "target": "delpi-hml-public-hub",
        "revision_sha": _SHA,
        "artifact_version": "atlas-hml-b-66-69",
        "key_fingerprint": "a" * 32,
        "change_record_id": "CHG-ATLAS-BOOTSTRAP-1",
        "external_anchor_id": "GLPI-9999",
        "external_anchor_kind": "glpi_change",
        "owner_approved": True,
        "checkpoint_absent_claimed": True,
        "prior_generation_known": False,
        "disposable_fixture": False,
        "prepare_enabled": False,
        "act_enabled": False,
    }
    doc.update(overrides)
    return json.dumps(doc, separators=(",", ":")).encode("utf-8")


def test_bootstrap_absence_never_genesis_and_stays_blocked():
    review = review_untrusted_bootstrap_dossier(_bootstrap_doc())
    assert review.status == "blocked"
    assert review.approval_pending
    assert not review.genesis_authorized
    assert not review.absence_treated_as_genesis
    assert not review.can_execute
    with pytest.raises(HMLBootstrapControlError) as exc:
        reject_absence_as_genesis()
    assert exc.value.code == "HML_BOOTSTRAP_ABSENCE_NOT_GENESIS"
    incomplete = _bootstrap_doc(owner_approved=False, change_record_id="x")
    # change_record still present; flip approval
    review2 = review_untrusted_bootstrap_dossier(
        _bootstrap_doc(owner_approved=False),
    )
    assert review2.approval_pending
    assert not review2.genesis_authorized


def _recovery_doc(**overrides):
    doc = {
        "schema": "atlas.hml.b.counter-recovery.v1",
        "incident": "restore_old_backup",
        "local_generation": 5,
        "anchor_generation": 5,
        "backup_generation": 2,
        "checkpoint_present": True,
        "checkpoint_corrupt": False,
        "signature_returned": False,
        "reservation_persisted": True,
        "concurrent_writers": False,
        "operator_reconcile_approved": False,
        "prepare_enabled": False,
        "act_enabled": False,
    }
    doc.update(overrides)
    return json.dumps(doc, separators=(",", ":")).encode("utf-8")


def test_counter_recovery_never_regresses_and_blocks_incidents():
    review = review_untrusted_counter_recovery(_recovery_doc())
    assert review.decision == "BLOCKED_RECONCILE_REQUIRED"
    assert review.required_generation_floor == 5
    assert review.silent_regression_prevented
    assert not review.can_execute
    with pytest.raises(HMLCounterRecoveryError):
        assert_generation_floor(proposed=3, floor=5)
    assert_generation_floor(proposed=6, floor=5)
    crash = review_untrusted_counter_recovery(
        _recovery_doc(incident="crash_after_reserve_before_return", backup_generation=5),
    )
    assert crash.decision == "BLOCKED_RECONCILE_REQUIRED"


def test_candidate_units_review_and_install_forbidden():
    review = review_candidate_unit_sources()
    assert review.files_reviewed == 6
    assert review.status == "blocked"
    assert not review.auto_enable_possible
    assert not review.install_sections_present
    assert not review.can_execute
    sources = {
        name: path.read_text(encoding="utf-8")
        for name, path in (
            (p.name, p)
            for p in (
                __import__("pathlib").Path(__file__).resolve().parents[1]
                / "candidate-units"
            ).glob("*.candidate")
        )
    }
    poisoned = dict(sources)
    poisoned["atlas-hml-local-signer.service.candidate"] += "\n[Install]\nWantedBy=multi-user.target\n"
    with pytest.raises(HMLCandidateUnitError) as exc:
        review_candidate_unit_sources(poisoned)
    assert exc.value.code == "HML_CANDIDATE_INSTALL_FORBIDDEN"


def _preflight_doc(**overrides):
    doc = {
        "schema": "atlas.hml.b.preflight-bundle.v1",
        "host": "srv-api",
        "environment": "hml",
        "revision_sha": _SHA,
        "os_release_id": "ubuntu",
        "users_present": {
            "atlas-hml": False,
            "atlas-hml-bridge": False,
            "atlas-hml-signer": False,
        },
        "groups_present": {
            "atlas-hml": False,
            "atlas-hml-bridge": False,
            "atlas-hml-signer": False,
        },
        "paths": {
            "snapshot_dir": False,
            "signer_socket_dir": False,
            "signer_key_dir": False,
            "signer_state_dir": False,
        },
        "sockets": {"presenter": False, "signer": False},
        "systemd_units": {
            "producer": False, "producer_timer": False, "signer": False,
            "bridge": False, "presenter": False,
        },
        "docker_endpoints": {
            "unix_docker_sock": True,
            "unix_containerd": True,
            "tcp_endpoint_detected": False,
        },
        "hml_container": {"name": "delpi-hml-public-hub", "running_claimed": True},
        "prod_container": {"name": "delpi-public-hub", "running_claimed": True},
        "capabilities": {
            "effective_empty_claimed": True,
            "bounding_empty_claimed": True,
        },
        "secrets_redacted": True,
        "prepare_enabled": False,
        "act_enabled": False,
        "mcp_tools": [
            "get_deployment_revision", "get_host_health",
            "get_service_health", "list_managed_services",
        ],
    }
    doc.update(overrides)
    return json.dumps(doc, separators=(",", ":")).encode("utf-8")


def test_preflight_secret_denial_and_blocking_findings():
    review = review_untrusted_preflight_bundle(_preflight_doc())
    assert review.status == "blocked"
    assert not review.host_attested
    assert any(item.blocking for item in review.findings)
    with pytest.raises(HMLPreflightBundleError) as exc:
        review_untrusted_preflight_bundle(b"password=leaked-secret-material")
    assert exc.value.code == "HML_PREFLIGHT_SECRET_MATERIAL_DENIED"
    tcp = json.loads(_preflight_doc())
    tcp["docker_endpoints"]["tcp_endpoint_detected"] = True
    review_tcp = review_untrusted_preflight_bundle(
        json.dumps(tcp, separators=(",", ":")).encode("utf-8"),
    )
    assert any(f.code == "DOCKER_TCP_ENDPOINT_DETECTED" for f in review_tcp.findings)


def test_handoff_checklist_prepare_act_off_and_progress():
    checklist = build_stage66_69_handoff_checklist()
    assert checklist.status == "blocked"
    assert not checklist.can_execute
    assert not checklist.prepare_eligible
    assert checklist.progress_percent_reference == 60
    ids = {item.id for item in checklist.items}
    assert "PREPARE_ACT" in ids
    assert "SEC_01_10" in ids
    assert "HOST_BOOTSTRAP_GEN1" in ids


def test_prod_payload_and_prepare_flags_denied_in_bootstrap():
    with pytest.raises(HMLBootstrapControlError):
        review_untrusted_bootstrap_dossier(
            _bootstrap_doc(target="delpi-public-hub"),
        )
    with pytest.raises(HMLBootstrapControlError):
        review_untrusted_bootstrap_dossier(
            _bootstrap_doc(prepare_enabled=True),
        )

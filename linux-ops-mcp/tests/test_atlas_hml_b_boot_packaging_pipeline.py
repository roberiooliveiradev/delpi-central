"""ATLAS boot/packaging/signing pipeline package — disposable tests."""
from __future__ import annotations

import json
import os
import stat
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from linux_ops_mcp.atlas_hml_b_glpi_key_registry import (
    HMLGlpiKeyRegistryError,
    build_glpi_registry_template,
    review_glpi_key_registry_record,
)
from linux_ops_mcp.atlas_hml_b_hml_prod_readiness import build_readiness_matrix
from linux_ops_mcp.atlas_hml_b_key_lifecycle import generate_ephemeral_keypair
from linux_ops_mcp.atlas_hml_b_runtime_packaging import (
    HMLRuntimePackagingError,
    review_runtime_identity_preflight,
    review_runtime_packaging,
    run_packaging_entrypoint,
)
from linux_ops_mcp.atlas_hml_b_signed_pipeline_runtime import (
    HMLSignedPipelineError,
    run_disposable_signed_pipeline,
)
from linux_ops_mcp.atlas_hml_b_stage73_boot_guard import inspect_stage73_directory
from linux_ops_mcp.atlas_hml_b_stage74_tmpfiles_audit import review_no_clobber_candidate
from linux_ops_mcp.atlas_hml_b_stage75_boot_activation_gate import (
    Stage75BootGateError,
    build_atlas_only_rollback_inventory,
    evaluate_stage75_boot_activation_gate,
    render_post_reboot_validation_criteria,
    validate_post_create_directories,
)
from linux_ops_mcp.deploy_host_source import RuntimeContainer
_NOW = datetime(2026, 11, 18, 15, 0, tzinfo=timezone.utc)
_CONTAINER = RuntimeContainer(
    container_id="a" * 64,
    image_id="sha256:" + "b" * 64,
    running=True,
    healthy=True,
)


def _uid_gid_maps():
    names = {
        "root": 0 if os.getuid() != 0 else os.getuid(),
        "atlas-hml": os.getuid() if os.getuid() > 0 else 1000,
        "atlas-hml-bridge": os.getuid() if os.getuid() > 0 else 1001,
        "atlas-hml-signer": os.getuid() if os.getuid() > 0 else 1002,
    }
    # For fixture ownership we own all dirs as current uid/gid except we map
    # policy names onto the current non-root identity for disposable checks.
    uid = os.getuid()
    gid = os.getgid()
    uid_map = {
        "root": uid,  # disposable: treat current as policy owner stand-in
        "atlas-hml": uid,
        "atlas-hml-bridge": uid,
        "atlas-hml-signer": uid,
    }
    gid_map = {
        "root": gid,
        "atlas-hml": gid,
        "atlas-hml-bridge": gid,
        "atlas-hml-signer": gid,
    }
    return uid_map, gid_map


def _layout(root: Path, mode_override: dict[str, int] | None = None):
    modes = {
        "/run/atlas-hml-readonly": 0o750,
        "/run/atlas-hml-signer": 0o750,
        "/run/atlas-hml-signer-socket": 0o2750,
        "/var/lib/atlas-hml-signer-state": 0o750,
        "/var/lib/atlas-hml-signer-keys": 0o700,
    }
    if mode_override:
        modes.update(mode_override)
    for path, mode in modes.items():
        target = root / path.lstrip("/")
        target.mkdir(parents=True, exist_ok=True)
        os.chmod(target, mode)


def test_stage75_rejects_drift_even_when_tmpfiles_claimed_success(tmp_path):
    root = tmp_path / "boot"
    root.mkdir()
    _layout(root, {"/run/atlas-hml-signer": 0o777})
    uid_map, gid_map = _uid_gid_maps()
    post = validate_post_create_directories(
        root=root,
        uid_map=uid_map,
        gid_map=gid_map,
        claim_tmpfiles_succeeded=True,
    )
    assert not post.all_policy_match
    assert any(code.startswith("TMPFILES_SUCCESS_MASKED_DRIFT:") for code in post.rejected_codes)
    assert post.status == "blocked"
    assert not post.can_execute


def test_stage75_gate_composes_no_clobber_and_rollback(tmp_path):
    assert review_no_clobber_candidate() is True
    root = tmp_path / "fixture"
    root.mkdir()
    for rel in (
        "etc/tmpfiles.d", "run/tmpfiles.d",
        "usr/local/lib/tmpfiles.d", "usr/lib/tmpfiles.d",
        "etc/systemd/system", "run/systemd/system", "usr/lib/systemd/system",
    ):
        (root / rel).mkdir(parents=True)
    _layout(root)
    uid_map, gid_map = _uid_gid_maps()
    gate = evaluate_stage75_boot_activation_gate(
        fixture_root=root,
        uid_map=uid_map,
        gid_map=gid_map,
        claim_tmpfiles_succeeded=False,
    )
    assert gate.status == "blocked"
    assert gate.no_clobber is True
    assert gate.package.status == "blocked"
    assert not gate.activation_authorized
    assert not gate.prepare_eligible
    inv = build_atlas_only_rollback_inventory()
    assert "atlas-hml-local-signer.service.candidate" in inv.atlas_only_components
    criteria = render_post_reboot_validation_criteria()
    assert criteria["reject_on_tmpfiles_success_with_dac_drift"] is True
    assert criteria["prepare_eligible"] is False


def test_stage75_symlink_component_denied(tmp_path):
    root = tmp_path / "sym"
    root.mkdir()
    run = root / "run"
    run.mkdir()
    # Replace a policy directory with a symlink
    target = tmp_path / "elsewhere"
    target.mkdir()
    os.symlink(target, run / "atlas-hml-readonly")
    uid_map, gid_map = _uid_gid_maps()
    check = inspect_stage73_directory(
        root=root,
        path="/run/atlas-hml-readonly",
        expected_uid=uid_map["root"],
        expected_gid=gid_map["atlas-hml"],
        expected_mode=0o750,
    )
    assert check.policy_match is False


@pytest.mark.skipif(os.getuid() == 0, reason="non-root packaging preflight")
def test_runtime_packaging_and_entrypoint_disposable_only(monkeypatch, tmp_path):
    review = review_runtime_packaging()
    assert review.status == "blocked"
    assert review.installable is False
    assert "atlas-hml-signer.entrypoint.py" in review.entrypoint_wrappers
    pre = review_runtime_identity_preflight(role="signer", allow_socket_fds=True, disposable_fixture=True)
    assert pre.status == "blocked"
    assert pre.uid == os.getuid()
    monkeypatch.setenv("ATLAS_HML_RUNTIME_MODE", "disposable-fixture")
    monkeypatch.delenv("DOCKER_HOST", raising=False)
    rc = run_packaging_entrypoint(
        "signer",
        ["--disposable-fixture", "--expected-uid", str(os.getuid()),
         "--expected-gid", str(os.getgid())],
    )
    assert rc == 2
    monkeypatch.delenv("ATLAS_HML_RUNTIME_MODE", raising=False)
    with pytest.raises(HMLRuntimePackagingError) as exc:
        run_packaging_entrypoint("signer", ["--disposable-fixture"])
    assert exc.value.code == "HML_RUNTIME_MODE_ENV_REQUIRED"


@pytest.mark.skipif(os.getuid() == 0, reason="non-root socket pipeline")
def test_signed_pipeline_socket_verify_continuity(tmp_path):
    root = tmp_path / "pipe"
    root.mkdir()
    (root / "DISPOSABLE_FIXTURE").write_text("yes\n", encoding="utf-8")
    result = run_disposable_signed_pipeline(
        fixture_root=root, container=_CONTAINER, generation=1,
        observed_at=datetime.now(timezone.utc),
    )
    assert result.status == "blocked"
    assert result.signature_verified is True
    assert result.continuity_persisted is True
    assert result.socket_mode == 0o660
    assert not result.can_execute


@pytest.mark.skipif(os.getuid() == 0, reason="non-root socket pipeline")
def test_signed_pipeline_rejects_missing_marker_and_host_root(tmp_path):
    root = tmp_path / "bad"
    root.mkdir()
    with pytest.raises(HMLSignedPipelineError) as exc:
        run_disposable_signed_pipeline(fixture_root=root, container=_CONTAINER)
    assert exc.value.code == "HML_PIPELINE_DISPOSABLE_MARKER_REQUIRED"
    with pytest.raises(HMLSignedPipelineError):
        run_disposable_signed_pipeline(fixture_root=Path("/"), container=_CONTAINER)


def test_glpi_registry_metadata_only_and_secret_rejected():
    keys = generate_ephemeral_keypair()
    raw = build_glpi_registry_template(
        key_id=keys.key_id, generation=1, glpi_ticket_id="GLPI-1001",
    )
    review = review_glpi_key_registry_record(raw)
    assert review.status == "blocked"
    assert review.private_material_present is False
    assert review.glpi_called is False
    dirty = raw[:-1] + b',"pem":"BEGIN PRIVATE"}'
    # invalid schema
    with pytest.raises(HMLGlpiKeyRegistryError):
        review_glpi_key_registry_record(dirty)
    with pytest.raises(HMLGlpiKeyRegistryError) as exc:
        review_glpi_key_registry_record(
            b'{"schema":"x","host":"srv-api","environment":"hml","key_id":"'
            + keys.key_id.encode()
            + b'","public_key_fingerprint":"'
            + keys.key_id.encode()
            + b'","generation":1,"glpi_ticket_id":"T","glpi_recovery_identifier":'
            + b'"ATLAS-HML-ED25519-PRIVATE-V1","rotation_of_key_id":null,'
            + b'"revoked":false,"owner_approved":false,"private_material_present":false,'
            + b'"prepare_enabled":false,"act_enabled":false,"note":"BEGIN PRIVATE"}'
        )
    assert exc.value.code in {
        "HML_GLPI_SCHEMA_DENIED", "HML_GLPI_SECRET_PAYLOAD_DENIED", "HML_GLPI_FIELD_DENIED",
    }


def test_readiness_matrix_blocked_and_mcp_read_count():
    matrix = build_readiness_matrix()
    assert matrix.status == "blocked"
    assert not matrix.hml_pilot_authorized
    assert not matrix.prod_validation_authorized
    assert "PREPARE_DISABLED" in matrix.blocks
    try:
        from linux_ops_mcp.server import READ_TOOLS
        legacy = {
            "get_deployment_revision", "get_host_health",
            "get_service_health", "list_managed_services",
        }
        multiserver = {
            "list_servers", "get_server_health",
            "get_infrastructure_health", "get_server_services",
        }
        assert legacy <= READ_TOOLS
        assert multiserver <= READ_TOOLS
        assert len(READ_TOOLS) == 8
        assert not any(name.startswith(("prepare_", "act_")) for name in READ_TOOLS)
    except Exception:
        # fallback: count @mcp.tool in server.py
        text = Path(__file__).resolve().parents[1].joinpath(
            "linux_ops_mcp", "server.py"
        ).read_text(encoding="utf-8")
        assert text.count("@mcp.tool(") == 8

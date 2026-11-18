"""Stage75/76 boot gate: CLI JSON, GID0, post-create fail-closed."""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from linux_ops_mcp.atlas_hml_b_stage71_readonly_preflight import _DIRECTORY_POLICY
from linux_ops_mcp.atlas_hml_b_stage75_boot_activation_gate import (
    Stage75BootGateError,
    _validate_identity_maps,
    build_stage75_cli_report,
    evaluate_stage75_boot_activation_gate,
    main,
    validate_post_create_directories,
)


def _maps(uid=None, gid=None):
    uid = os.getuid() if uid is None else uid
    gid = os.getgid() if gid is None else gid
    names = {owner for _, owner, _, _ in _DIRECTORY_POLICY} | {
        group for _, _, group, _ in _DIRECTORY_POLICY
    }
    uid_map = {name: (0 if name == "root" else uid) for name in names}
    gid_map = {name: gid for name in names}
    return uid_map, gid_map


def _layout(root: Path, mode_override: dict[str, int] | None = None):
    modes = {path: mode for path, _, _, mode in _DIRECTORY_POLICY}
    if mode_override:
        modes.update(mode_override)
    for path, mode in modes.items():
        target = root / path.lstrip("/")
        target.mkdir(parents=True, exist_ok=True)
        os.chmod(target, mode)


def test_cli_json_without_slots_attribute_error(capsys):
    assert main([]) == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "atlas.hml.stage75.boot-gate.v1"
    assert payload["status"] == "blocked"
    assert payload["prepare_eligible"] is False
    assert payload["can_execute"] is False
    assert "rollback" in payload and "atlas_only_components" in payload["rollback"]
    # Must not use __dict__ on slotted dataclass (would raise AttributeError).
    assert isinstance(payload["rollback"]["stop_conditions"], list)


def test_cli_with_fixture_root_structured_evaluation(tmp_path, capsys):
    for rel in (
        "etc/tmpfiles.d", "usr/lib/tmpfiles.d",
        "etc/systemd/system", "run/systemd/system", "usr/lib/systemd/system",
    ):
        (tmp_path / rel).mkdir(parents=True)
    assert main(["--fixture-root", str(tmp_path)]) == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["evaluation"]["status"] == "blocked"
    assert payload["evaluation"]["boot_audit"]["candidate_no_clobber"] is True
    assert payload["activation_authorized"] is False


def test_gid_zero_allowed_only_for_root_group_name():
    uid_map, gid_map = _maps()
    gid_map["root"] = 0
    _validate_identity_maps(uid_map, gid_map)
    bad = dict(gid_map)
    bad["atlas-hml"] = 0
    with pytest.raises(Stage75BootGateError) as exc:
        _validate_identity_maps(uid_map, bad)
    assert exc.value.code == "STAGE75_GID_MAP_DENIED"


def test_post_create_rejects_wrong_mode_even_if_tmpfiles_claimed_success(tmp_path):
    root = tmp_path / "boot"
    root.mkdir()
    _layout(root, {"/run/atlas-hml-signer": 0o777})
    uid_map, gid_map = _maps()
    # disposable: map policy owners to current identity
    uid_map = {name: os.getuid() for name in uid_map}
    gid_map = {name: os.getgid() for name in gid_map}
    post = validate_post_create_directories(
        root=root,
        uid_map=uid_map,
        gid_map=gid_map,
        claim_tmpfiles_succeeded=True,
    )
    assert not post.all_policy_match
    assert any(c.startswith("TMPFILES_SUCCESS_MASKED_DRIFT:") for c in post.rejected_codes)
    assert any(c.startswith("DAC_ACL_OR_SETGID_DENIED:") for c in post.rejected_codes)
    assert post.status == "blocked"
    assert not post.can_execute


def test_post_create_rejects_symlink_replacement(tmp_path):
    root = tmp_path / "sym"
    root.mkdir()
    run = root / "run"
    run.mkdir()
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    os.symlink(elsewhere, run / "atlas-hml-readonly")
    uid_map, gid_map = _maps()
    uid_map = {name: os.getuid() for name in uid_map}
    gid_map = {name: os.getgid() for name in gid_map}
    post = validate_post_create_directories(root=root, uid_map=uid_map, gid_map=gid_map)
    assert not post.all_policy_match
    assert any("atlas-hml-readonly" in c for c in post.rejected_codes)


def test_gate_surfaces_critical_tmpfiles_conflict(tmp_path):
    folder = tmp_path / "etc/tmpfiles.d"
    folder.mkdir(parents=True)
    (folder / "danger.conf").write_text(
        "Z /var/lib - - - -\n", encoding="utf-8",
    )
    for rel in ("etc/systemd/system", "run/systemd/system", "usr/lib/systemd/system"):
        (tmp_path / rel).mkdir(parents=True, exist_ok=True)
    gate = evaluate_stage75_boot_activation_gate(fixture_root=tmp_path)
    assert "TMPFILES_RECURSIVE_PARENT_CONFLICT" in gate.boot_audit.critical_codes
    assert "TMPFILES_CRITICAL_CONFLICT" in gate.post_create.rejected_codes
    assert gate.status == "blocked"
    assert not gate.activation_authorized
    report = build_stage75_cli_report(gate)
    assert report["error_code"] == "STAGE75_TMPFILES_OR_DAC_DENIED"


def test_mcp_read_tools_untouched():
    text = Path(__file__).resolve().parents[1].joinpath(
        "linux_ops_mcp", "server.py",
    ).read_text(encoding="utf-8")
    assert text.count("@mcp.tool(") == 4

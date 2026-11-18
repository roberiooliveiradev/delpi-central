"""Stage 71 source-only preparation: fake filesystem and untrusted Git dossiers."""
from __future__ import annotations

import json
import os
import socket

import pytest

from linux_ops_mcp import atlas_hml_b_stage71_readonly_preflight as probe
from linux_ops_mcp.atlas_hml_b_stage71_git_reconcile import (
    Stage71GitReconcileError, review_stage71_git_dossier,
)
from linux_ops_mcp.atlas_hml_b_stage71_provisioning_review import (
    build_stage71_provisioning_review,
)

_LOCAL = "0869cb82a9c68846e58a285926d02c98d6d4847e"
_REMOTE = "b00865e643301c31bb038a49b3f76e022da984cc"


def _git_doc(**patch):
    data = {
        "schema": "atlas.hml.stage71.git-reconcile.v1",
        "host": "srv-api",
        "repo_path": "/home/operador/projetos/delpi-central",
        "branch": "main",
        "local_head": _LOCAL,
        "local_origin_main": _LOCAL,
        "remote_main": _REMOTE,
        "ancestry_checked_claimed": True,
        "remote_touches_dirty_claimed": False,
        "dirty_changes": [
            {"path": "infra/scripts/up-hml-sequential.sh", "kind": "mode_100644_to_100755"},
            {"path": "shared/delpi_auth.egg-info/SOURCES.txt",
             "kind": "one_generated_source_entry"},
        ],
        "index_clean_claimed": True,
        "untracked_paths_present_claimed": False,
        "merge_or_rebase_in_progress_claimed": False,
    }
    data.update(patch)
    return json.dumps(data, separators=(",", ":")).encode("utf-8")


def test_git_current_baseline_requires_manual_reconcile_and_never_pulls():
    review = review_stage71_git_dossier(_git_doc())
    assert review.status == "blocked"
    assert "LOCAL_WORKTREE_DIRTY_PRESERVE" in review.findings
    assert "REMOTE_AHEAD_OR_DIVERGED_REQUIRES_FRESH_ANCHOR" in review.findings
    assert not review.pull_allowed
    assert not review.stash_allowed
    assert not review.reset_allowed
    assert not review.clean_allowed
    assert not review.deploy_allowed
    assert not review.can_execute


def test_even_clean_git_claim_cannot_authorize_pull():
    review = review_stage71_git_dossier(_git_doc(
        local_head=_REMOTE, local_origin_main=_REMOTE,
        remote_main=_REMOTE, dirty_changes=[],
    ))
    assert review.status == "blocked"
    assert review.manual_review_required
    assert not review.pull_allowed
    assert "NO_LOCAL_CHANGES_CLAIMED_STILL_NEEDS_VERIFICATION" in review.findings


@pytest.mark.parametrize("patch,expected", [
    ({"branch": "feature"}, "STAGE71_GIT_SCOPE_DENIED"),
    ({"host": "other"}, "STAGE71_GIT_SCOPE_DENIED"),
    ({"local_head": "f" * 39}, "STAGE71_GIT_SCOPE_DENIED"),
    ({"local_origin_main": True}, "STAGE71_GIT_SCOPE_DENIED"),
    ({"index_clean_claimed": 1}, "STAGE71_GIT_SCOPE_DENIED"),
    ({"dirty_changes": "clean"}, "STAGE71_GIT_DIRTY_DENIED"),
    ({"dirty_changes": [{"path": "a"}]}, "STAGE71_GIT_DIRTY_DENIED"),
    ({"dirty_changes": [{"path": [], "kind": "mode_100644_to_100755"}]}, "STAGE71_GIT_DIRTY_DENIED"),
    ({"dirty_changes": [
        {"path": "infra/scripts/up-hml-sequential.sh", "kind": "mode_100644_to_100755"},
        {"path": "infra/scripts/up-hml-sequential.sh", "kind": "mode_100644_to_100755"},
    ]}, "STAGE71_GIT_DUPLICATE_CHANGE"),
])
def test_git_schema_fail_closed(patch, expected):
    with pytest.raises(Stage71GitReconcileError) as exc:
        review_stage71_git_dossier(_git_doc(**patch))
    assert exc.value.code == expected


def test_git_unknown_worktree_change_blocks_without_disclosing_path():
    review = review_stage71_git_dossier(_git_doc(dirty_changes=[
        {"path": "internal/another-module.py", "kind": "content_changed"},
    ]))
    assert "UNEXPECTED_LOCAL_MODIFICATION" in review.findings
    assert "internal/another-module.py" not in repr(review)
    assert not review.pull_allowed


def test_git_conflict_untracked_index_and_operation_detected():
    review = review_stage71_git_dossier(_git_doc(
        remote_touches_dirty_claimed=True,
        ancestry_checked_claimed=False,
        merge_or_rebase_in_progress_claimed=True,
        untracked_paths_present_claimed=True,
        index_clean_claimed=False,
    ))
    for code in (
        "REMOTE_CONFLICTS_LOCAL_DIRTY", "ANCESTRY_NOT_CHECKED",
        "ONGOING_GIT_OPERATION", "UNTRACKED_PATHS_UNREVIEWED", "INDEX_NOT_CLEAN",
    ):
        assert code in review.findings


@pytest.mark.parametrize("raw,expected", [
    (b"", "STAGE71_GIT_INPUT_DENIED"),
    (b"not-json", "STAGE71_GIT_INVALID_JSON"),
    (b'{"schema":1,"schema":2}', "STAGE71_GIT_DUPLICATE"),
    (b'{"token=supersecret":true}', "STAGE71_GIT_SECRET_DENIED"),
    (b'{"a":NaN}', "STAGE71_GIT_INVALID_JSON"),
])
def test_git_rejects_invalid_or_secret_material(raw, expected):
    with pytest.raises(Stage71GitReconcileError) as exc:
        review_stage71_git_dossier(raw)
    assert exc.value.code == expected


def test_readonly_probe_never_claims_host_attestation(tmp_path):
    data = probe.collect_stage71_readonly(root=tmp_path)
    assert data.status == "blocked"
    assert not data.can_execute
    assert not data.can_provision
    assert not data.host_attested
    assert not data.prepare_eligible
    assert data.docker_socket_kind == "absent"
    assert data.apparmor_enabled is None
    assert all(not item.user_present for item in data.identities)
    assert all(not item.present for item in data.directories)
    review = build_stage71_provisioning_review(data, docker_group_gid=988)
    assert review.status == "blocked"
    assert len(review.steps) == 7
    assert not review.commands_generated
    assert not review.change_authorized
    assert "IDENTITY_MISSING_ATLAS_HML_SIGNER" in review.findings
    assert "IDENTITY_MISSING_ATLAS_HML_BRIDGE" in review.findings
    assert not review.can_execute


def test_probe_reports_fixed_unit_paths_and_flag_only(tmp_path):
    unit = tmp_path / "etc/systemd/system/atlas-hml-local-signer.service"
    unit.parent.mkdir(parents=True)
    unit.write_text("not an operational unit")
    apparmor = tmp_path / "sys/module/apparmor/parameters/enabled"
    apparmor.parent.mkdir(parents=True)
    apparmor.write_bytes(b"Y\n")
    docker_path = tmp_path / "run/docker.sock"
    docker_path.parent.mkdir(parents=True)
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        listener.bind(str(docker_path))
        data = probe.collect_stage71_readonly(root=tmp_path)
    finally:
        listener.close()
    assert data.docker_socket_kind == "socket"
    assert data.apparmor_enabled is True
    assert "atlas-hml-local-signer.service" in data.systemd_unit_names_found
    assert "ATLAS_UNIT_PRESENT_MANUAL_REVIEW" in data.findings
    assert data.status == "blocked"
    assert not data.host_attested


def test_probe_wrong_directory_dac_never_approves(tmp_path):
    parent = tmp_path / "run/atlas-hml-signer-socket"
    parent.mkdir(parents=True, mode=0o700)
    os.chmod(parent, 0o777)
    snapshot = probe.collect_stage71_readonly(root=tmp_path)
    case = next(item for item in snapshot.directories
                if item.path == "/run/atlas-hml-signer-socket")
    assert case.present and not case.compliant
    assert case.finding == "DAC_OR_ACL_DENIED"
    assert "ATLAS_DIRECTORY_DAC_DENIED" in snapshot.findings
    result = build_stage71_provisioning_review(snapshot)
    assert "DIRECTORY_POLICY_DENIED_ATLAS_HML_SIGNER_SOCKET" in result.findings


def test_probe_root_symlink_denied(tmp_path):
    link = tmp_path / "link"
    link.symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(ValueError, match="STAGE71_ROOT_DENIED"):
        probe.collect_stage71_readonly(root=link)


def test_directory_requires_owner_uid_exact_even_when_other_dac_matches(tmp_path, monkeypatch):
    parent = tmp_path / "run/atlas-hml-signer-socket"
    parent.mkdir(parents=True)
    os.chmod(parent, 0o2750)
    uid, gid = os.getuid(), os.getgid()
    identities = (
        probe.Stage71Identity("atlas-hml", True, uid, gid, True, gid),
        probe.Stage71Identity("atlas-hml-bridge", True, uid + 1, gid, True, gid),
        probe.Stage71Identity("atlas-hml-signer", True, uid + 1, gid, True, gid),
    )
    monkeypatch.setattr(probe, "_get_identities", lambda root: identities)
    result = probe.collect_stage71_readonly(root=tmp_path)
    case = next(item for item in result.directories
                if item.path == "/run/atlas-hml-signer-socket")
    assert case.present and not case.compliant
    assert case.finding == "DAC_OR_ACL_DENIED"
    assert result.status == "blocked"


def _constructed_review(*, docker_primary=False, collision=False, missing=False):
    gids = (985, 988 if docker_primary else 801, 802)
    uids = (995, 996, 996 if collision else 997)
    ids = tuple(probe.Stage71Identity(
        name, not (missing and i == 2),
        None if (missing and i == 2) else uids[i],
        None if (missing and i == 2) else gids[i],
        not (missing and i == 2),
        None if (missing and i == 2) else gids[i],
    ) for i, name in enumerate(("atlas-hml", "atlas-hml-bridge", "atlas-hml-signer")))
    paths = tuple(probe.Stage71Directory(name, True, 0o750, 1, 1, True,
                                         True, "DAC_MATCH") for name, _, _, _
                  in probe._DIRECTORY_POLICY)
    return probe.Stage71ReadOnlyPreflight(
        identities=ids, directories=paths, systemd_unit_names_found=(),
        docker_socket_kind="socket", docker_socket_mode=0o660,
        docker_socket_uid=0, docker_socket_gid=988,
        apparmor_enabled=True, findings=("PROBE_UNTRUSTED",),
    )


@pytest.mark.parametrize("case,expected", [
    ({"docker_primary": True}, "DOCKER_PRIMARY_GROUP_DENIED"),
    ({"collision": True}, "IDENTITY_COLLISION_DENIED"),
    ({"missing": True}, "IDENTITY_MISSING_ATLAS_HML_SIGNER"),
])
def test_provisioning_plan_fails_closed_on_identity_risks(case, expected):
    review = build_stage71_provisioning_review(
        _constructed_review(**case), docker_group_gid=988,
    )
    assert expected in review.findings
    assert not review.can_execute
    assert not review.can_provision if hasattr(review, "can_provision") else not review.can_execute


def test_provisioning_never_authorizes_even_apparently_compliant_observation():
    review = build_stage71_provisioning_review(
        _constructed_review(), docker_group_gid=988,
    )
    assert review.status == "blocked"
    assert not review.host_attested
    assert not review.can_execute
    assert not review.change_authorized
    assert not review.commands_generated
    assert review.progress_percent_reference == 60
    assert all(step.action == "OWNER_AUTHORIZATION_REQUIRED" for step in review.steps)

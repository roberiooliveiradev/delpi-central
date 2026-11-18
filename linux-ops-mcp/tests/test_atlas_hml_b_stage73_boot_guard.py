"""ATLAS stage 73: disposable negative tests, never touch the real host."""
import os
import socket
import pytest
from linux_ops_mcp.atlas_hml_b_candidate_unit_review import _DIR, HMLCandidateUnitError
from linux_ops_mcp.atlas_hml_b_stage71_readonly_preflight import (
    Stage71Identity, Stage71ReadOnlyPreflight, _DIRECTORY_POLICY,
)
from linux_ops_mcp import atlas_hml_b_stage73_boot_guard as guard


def sources():
    return {p.name: p.read_text(encoding="utf-8") for p in _DIR.glob("*.candidate")}


def identities(collision=False, docker_primary=False):
    gids = (985, 984, 984 if collision else (998 if docker_primary else 983))
    uids = (995, 994, 994 if collision else 993)
    people = tuple(Stage71Identity(name, True, uids[i], gids[i], True, gids[i])
                   for i, name in enumerate(("atlas-hml", "atlas-hml-bridge", "atlas-hml-signer")))
    observed = Stage71ReadOnlyPreflight(
        identities=people, directories=(), systemd_unit_names_found=(),
        docker_socket_kind="socket", docker_socket_mode=0o660,
        docker_socket_uid=0, docker_socket_gid=998,
        apparmor_enabled=True, findings=(),
    )
    return guard.review_stage73_identities(observed, docker_group_gid=998)


def test_packaging_blocked_and_five_tmpfiles_rules():
    v = guard.review_stage73_package()
    payload = guard.render_stage73_tmpfiles_payload()
    assert v.status == "blocked" and v.candidate_units_reviewed == 6
    assert v.tmpfiles_directives == 5 and not v.installed
    assert not v.boot_recreation_attested and not v.can_execute
    assert not v.prepare_eligible
    assert len([line for line in payload.splitlines() if line.startswith("d ")]) == 5
    assert "d /run/atlas-hml-signer-socket 02750 atlas-hml-signer atlas-hml-bridge -" in payload


@pytest.mark.parametrize("name,old,new", [
    ("atlas-hml-local-signer.service.candidate", "User=atlas-hml-signer", "User=root"),
    ("atlas-hml-local-signer.service.candidate", "Group=atlas-hml-signer", "Group=docker"),
    ("atlas-hml-local-signer.service.candidate", "PrivateNetwork=yes", "PrivateNetwork=no"),
    ("atlas-hml-local-signer.service.candidate", "FileDescriptorStoreMax=0", "FileDescriptorStoreMax=8"),
    ("atlas-hml-local-signer.service.candidate", "StandardInput=null", "StandardInput=socket"),
    ("atlas-hml-local-signer.service.candidate", "CapabilityBoundingSet=", "CapabilityBoundingSet=CAP_SYS_ADMIN"),
    ("atlas-hml-nonroot-bridge.service.candidate", "SupplementaryGroups=atlas-hml", "SupplementaryGroups=docker"),
    ("atlas-hml-nonroot-bridge.service.candidate", "ReadOnlyPaths=/run/atlas-hml-readonly", "ReadOnlyPaths=/var/lib/atlas-hml-signer-keys"),
    ("atlas-hml-nonroot-bridge.service.candidate", "InaccessiblePaths=/run/docker.sock /var/run/docker.sock", "InaccessiblePaths=/run/atlas-hml-signer"),
    ("atlas-hml-nonroot-bridge.service.candidate", "RestrictAddressFamilies=AF_UNIX", "RestrictAddressFamilies=AF_INET AF_UNIX"),
])
def test_role_or_fd_policy_mutation_denied(name, old, new):
    data = sources()
    assert old in data[name]
    data[name] = data[name].replace(old, new, 1)
    with pytest.raises((guard.Stage73ReviewError, HMLCandidateUnitError)):
        guard.review_stage73_package(data)


@pytest.mark.parametrize("entry", [
    "Environment=DOCKER_HOST=tcp://127.0.0.1:2375",
    "PassEnvironment=DOCKER_HOST",
    "Sockets=docker.socket",
    "BindPaths=/run/docker.sock",
    "StandardInputData=secret",
    "ExecStartPre=/bin/sh -c true",
    "LoadCredential=key:/some/path",
    "ReadWritePaths=/var/lib/atlas-hml-signer-keys",
])
def test_unsafe_bridge_directive_denied(entry):
    data = sources()
    data["atlas-hml-nonroot-bridge.service.candidate"] += entry + "\n"
    with pytest.raises((guard.Stage73ReviewError, HMLCandidateUnitError)):
        guard.review_stage73_package(data)


@pytest.mark.parametrize("replacement", [
    "d /run/atlas-hml-signer-socket 0777 atlas-hml-signer atlas-hml-bridge -",
    "d /run/atlas-hml-signer-socket 02750 root atlas-hml-bridge -",
    "d /run/docker.sock 0777 root docker -",
])
def test_tmpfiles_drift_denied(replacement):
    data = sources()
    name = "atlas-hml-runtime-layout.tmpfiles.candidate"
    old = "d /run/atlas-hml-signer-socket 02750 atlas-hml-signer atlas-hml-bridge -"
    data[name] = data[name].replace(old, replacement)
    with pytest.raises((guard.Stage73ReviewError, HMLCandidateUnitError)):
        guard.review_stage73_package(data)


def test_tmpfiles_order_denied():
    data = sources()
    name = "atlas-hml-runtime-layout.tmpfiles.candidate"
    lines = data[name].splitlines()
    lines[-1], lines[-2] = lines[-2], lines[-1]
    data[name] = "\n".join(lines) + "\n"
    with pytest.raises(guard.Stage73ReviewError, match="STAGE73_TMPFILES_ORDER_DENIED"):
        guard.review_stage73_package(data)


def fixture(tmp_path):
    path = tmp_path / "run/atlas-hml-signer-socket"
    path.mkdir(parents=True)
    os.chmod(tmp_path, 0o700)
    os.chmod(tmp_path / "run", 0o755)
    os.chmod(path, 0o2750)
    return path


def inspect(tmp_path, *, uid=None, gid=None, mode=0o2750):
    return guard.inspect_stage73_directory(
        root=tmp_path, path="/run/atlas-hml-signer-socket",
        expected_uid=os.getuid() if uid is None else uid,
        expected_gid=os.getgid() if gid is None else gid,
        expected_mode=mode,
    )


def test_matching_fixture_not_attestation(tmp_path):
    fixture(tmp_path)
    result = inspect(tmp_path)
    assert result.policy_match and result.finding == "FD_POLICY_MATCH_UNTRUSTED"
    assert guard.review_stage73_package().status == "blocked"


@pytest.mark.parametrize("mode", [0o750, 0o700, 0o2770, 0o2755])
def test_bad_mode_or_setgid_denied(tmp_path, mode):
    path = fixture(tmp_path)
    os.chmod(path, mode)
    assert not inspect(tmp_path).policy_match


def test_uid_gid_drift_denied(tmp_path):
    fixture(tmp_path)
    assert not inspect(tmp_path, uid=os.getuid() + 1).policy_match
    assert not inspect(tmp_path, gid=os.getgid() + 1).policy_match


def test_symlink_and_dangling_symlink_denied(tmp_path):
    path = fixture(tmp_path)
    path.rmdir()
    path.symlink_to(tmp_path / "missing")
    assert not inspect(tmp_path).policy_match
    path.unlink()
    target = tmp_path / "target"
    target.mkdir()
    path.symlink_to(target, target_is_directory=True)
    assert not inspect(tmp_path).policy_match


def test_parent_symlink_denied(tmp_path):
    path = fixture(tmp_path)
    path.rmdir()
    (tmp_path / "run").rmdir()
    real = tmp_path / "real"
    real.mkdir()
    (tmp_path / "run").symlink_to(real, target_is_directory=True)
    assert not inspect(tmp_path).policy_match


def test_world_writable_ancestor_denied(tmp_path):
    fixture(tmp_path)
    os.chmod(tmp_path / "run", 0o777)
    assert inspect(tmp_path).finding == "ANCESTOR_DENIED"


def test_unverifiable_acl_denied(tmp_path, monkeypatch):
    fixture(tmp_path)
    monkeypatch.setattr(guard, "has_no_extended_posix_acl", lambda *a, **k: False)
    assert not inspect(tmp_path).policy_match


def test_socket_in_place_of_directory_denied(tmp_path):
    path = fixture(tmp_path)
    path.rmdir()
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as listener:
        listener.bind(str(path))
        assert not inspect(tmp_path).policy_match


def test_unknown_path_denied(tmp_path):
    with pytest.raises(guard.Stage73ReviewError):
        guard.inspect_stage73_directory(
            root=tmp_path, path="/run/docker.sock", expected_uid=0,
            expected_gid=1, expected_mode=0o750,
        )


def test_identity_collision_docker_and_pilot_block():
    assert not any(x.startswith("IDENTITY_") for x in identities().findings)
    assert "IDENTITY_COLLISION_OR_MISSING" in identities(collision=True).findings
    assert "DOCKER_PRIMARY_GROUP_DENIED" in identities(docker_primary=True).findings
    assert not identities().supplementary_groups_attested
    checks = tuple(guard.Stage73DirectoryCheck(
        path, True, True, "FD_POLICY_MATCH_UNTRUSTED"
    ) for path, _, _, _ in _DIRECTORY_POLICY)
    result = guard.review_stage73_pilot_gate(
        guard.review_stage73_package(), identities(), checks
    )
    assert result.directory_policy_matches and result.identity_primary_policy_matches
    assert result.status == "blocked" and not result.can_execute
    assert not result.prepare_eligible and not result.independently_attested
    assert "SEC_01_TO_10_PENDING" in result.blocks


def test_pilot_missing_evidence_denied():
    with pytest.raises(guard.Stage73ReviewError):
        guard.review_stage73_pilot_gate(
            guard.review_stage73_package(), identities(), ()
        )

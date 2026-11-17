"""Disposable filesystem tests for candidate HML snapshot file reader.

Fixtures are tmp_path-only. They never create /run resources, contact Docker,
change system users/groups, create a listener, deploy or enable PREPARE/ACT.
"""
from __future__ import annotations

import errno
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from linux_ops_mcp import atlas_hml_snapshot_file_reader as reader

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
def snapshot(tmp_path):
    now = datetime.now(timezone.utc)
    directory = tmp_path / "atlas-hml-readonly"
    directory.mkdir()
    os.chmod(directory, 0o750)
    file_path = directory / "inspect-snapshot.json"
    payload = {**_META, "observed_at": now.strftime("%Y-%m-%dT%H:%M:%SZ")}
    file_path.write_bytes(json.dumps(payload, separators=(",", ":")).encode())
    os.chmod(file_path, 0o640)
    return directory, file_path, now


def observe(snapshot, *, owner=None, gid=None, now=None):
    directory, _, observed = snapshot
    return reader._review_from_directory(
        directory,
        owner_uid=os.getuid() if owner is None else owner,
        expected_gid=os.getgid() if gid is None else gid,
        now=observed if now is None else now,
    )


def denied(code, run):
    with pytest.raises(reader.HMLSnapshotFileError) as exc:
        run()
    assert exc.value.code == code
    assert "private" not in str(exc.value).lower()


def test_valid_disposable_snapshot_is_only_diagnostic_and_blocked(snapshot):
    report = observe(snapshot)
    assert report.status == "blocked"
    assert report.environment == "hml"
    assert report.service_id == "public-hub"
    assert report.image_id == "sha256:" + "b"*64
    assert report.running and report.healthy
    assert not report.snapshot_origin_attested
    assert not report.docker_access_boundary_attested
    assert not report.proxy_policy_independently_attested
    assert not report.host_identity_attested
    assert not report.checkout_integrity_attested
    assert not report.challenge_consumed
    assert not report.prepare_eligible and not report.can_execute
    assert "SNAPSHOT_TIMESTAMP_CLAIM_ONLY" in report.blocks
    assert "PREPARE_DISABLED" in report.blocks
    assert "ACT_DISABLED" in report.blocks


def test_snapshot_absent_is_not_an_implicit_success(snapshot):
    _, file_path, _ = snapshot
    file_path.unlink()
    denied("HML_SNAPSHOT_FILE_UNAVAILABLE", lambda: observe(snapshot))


@pytest.mark.parametrize("mode", [0o700, 0o770, 0o755, 0o777])
def test_parent_directory_mode_must_be_exact(snapshot, mode):
    directory, _, _ = snapshot
    os.chmod(directory, mode)
    denied("HML_SNAPSHOT_DIRECTORY_UNSAFE", lambda: observe(snapshot))


@pytest.mark.parametrize("mode", [0o600, 0o644, 0o660, 0o666, 0o777])
def test_snapshot_mode_must_be_exact(snapshot, mode):
    _, file_path, _ = snapshot
    os.chmod(file_path, mode)
    denied("HML_SNAPSHOT_FILE_UNSAFE", lambda: observe(snapshot))


def test_wrong_owner_or_group_deny_without_attempting_privilege_change(snapshot):
    denied("HML_SNAPSHOT_DIRECTORY_UNSAFE", lambda: observe(snapshot, owner=os.getuid()+1))
    denied("HML_SNAPSHOT_DIRECTORY_UNSAFE", lambda: observe(snapshot, gid=os.getgid()+1))


def test_snapshot_is_never_allowed_to_be_a_symlink(snapshot):
    _, path, _ = snapshot
    target = path.with_name("target")
    path.rename(target)
    path.symlink_to(target)
    denied("HML_SNAPSHOT_FILE_UNVERIFIABLE", lambda: observe(snapshot))


def test_parent_directory_symlink_is_denied(snapshot):
    directory, _, _ = snapshot
    moved = directory.with_name("renamed")
    directory.rename(moved)
    directory.symlink_to(moved, target_is_directory=True)
    denied("HML_SNAPSHOT_FILE_UNVERIFIABLE", lambda: observe(snapshot))


def test_hardlinked_snapshot_is_denied(snapshot):
    _, path, _ = snapshot
    os.link(path, path.with_name("another-link"))
    denied("HML_SNAPSHOT_FILE_UNSAFE", lambda: observe(snapshot))


def test_fifo_cannot_block_the_reader(snapshot):
    _, path, _ = snapshot
    path.unlink()
    os.mkfifo(path, 0o640)
    denied("HML_SNAPSHOT_FILE_UNSAFE", lambda: observe(snapshot))


@pytest.mark.parametrize("length", [0, 2049])
def test_empty_or_oversized_files_are_denied(snapshot, length):
    _, path, _ = snapshot
    path.write_bytes(b"x"*length)
    os.chmod(path, 0o640)
    denied("HML_SNAPSHOT_FILE_UNSAFE", lambda: observe(snapshot))


@pytest.mark.parametrize("delta", [-120, 10])
def test_stale_or_future_file_mtime_is_not_trusted(snapshot, delta):
    _, path, now = snapshot
    value = (now + timedelta(seconds=delta)).timestamp()
    os.utime(path, (value, value))
    denied("HML_SNAPSHOT_FILE_MTIME_UNTRUSTED", lambda: observe(snapshot))


def test_json_timestamp_stale_is_denied_even_if_file_mtime_is_fresh(snapshot):
    _, path, now = snapshot
    payload = {**_META, "observed_at": (now-timedelta(minutes=2)).strftime("%Y-%m-%dT%H:%M:%SZ")}
    path.write_bytes(json.dumps(payload).encode())
    os.chmod(path, 0o640)
    denied("HML_SNAPSHOT_EXPIRED_OR_FUTURE", lambda: observe(snapshot))


def test_prod_claim_is_never_accepted_from_an_os_safe_file(snapshot):
    _, path, now = snapshot
    payload = {**_META, "environment": "prod", "observed_at": now.strftime("%Y-%m-%dT%H:%M:%SZ")}
    path.write_bytes(json.dumps(payload).encode())
    os.chmod(path, 0o640)
    denied("HML_SNAPSHOT_TARGET_DENIED", lambda: observe(snapshot))


def test_swap_during_read_denies_instead_of_accepting_detached_inode(snapshot, monkeypatch):
    _, path, _ = snapshot
    original = reader._read_bounded
    def swap(fd, size):
        content = original(fd, size)
        path.rename(path.with_name("removed-during-read"))
        path.write_bytes(content)
        os.chmod(path, 0o640)
        return content
    monkeypatch.setattr(reader, "_read_bounded", swap)
    denied("HML_SNAPSHOT_FILE_CHANGED", lambda: observe(snapshot))


def test_truncated_read_is_rejected_without_using_partial_json(snapshot, monkeypatch):
    monkeypatch.setattr(reader, "_read_bounded", lambda fd, size: (_ for _ in ()).throw(
        reader.HMLSnapshotFileError("HML_SNAPSHOT_FILE_CHANGED")
    ))
    denied("HML_SNAPSHOT_FILE_CHANGED", lambda: observe(snapshot))


def test_relative_path_and_naive_timestamp_denied_before_os_access(snapshot):
    dirpath, _, now = snapshot
    denied("HML_SNAPSHOT_REVIEW_INPUT_INVALID", lambda: reader._review_from_directory(
        Path("relative"),
        owner_uid=os.getuid(),
        expected_gid=os.getgid(),
        now=now,
    ))
    denied("HML_SNAPSHOT_REVIEW_INPUT_INVALID", lambda: observe(
        snapshot, now=now.replace(tzinfo=None)
    ))


def test_fixed_entrypoint_rejects_missing_group_and_forces_root_owner(monkeypatch):
    def missing(_name):
        raise KeyError("private-user-record")
    monkeypatch.setattr(reader.grp, "getgrnam", missing)
    denied("HML_SNAPSHOT_READER_IDENTITY_UNAVAILABLE", lambda: reader.read_fixed_hml_snapshot(
        now=datetime.now(timezone.utc),
    ))

    calls = []
    monkeypatch.setattr(reader.grp, "getgrnam", lambda name: SimpleNamespace(gr_gid=985))
    monkeypatch.setattr(reader, "_review_from_directory", lambda *args, **kwargs: (
        calls.append((args, kwargs)) or "blocked-placeholder"
    ))
    now = datetime.now(timezone.utc)
    assert reader.read_fixed_hml_snapshot(now=now) == "blocked-placeholder"
    assert calls == [((reader._FIXED_DIRECTORY,), {
        "owner_uid": 0, "expected_gid": 985, "now": now,
    })]


def test_no_producer_service_or_mcp_tool_in_snapshot_file_reader():
    for name in ("main", "create_mcp_server", "serve", "deploy", "write_snapshot"):
        assert not hasattr(reader, name)


@pytest.mark.parametrize("target,attribute", [
    ("directory", "system.posix_acl_access"),
    ("directory", "system.posix_acl_default"),
    ("file", "system.posix_acl_access"),
])
def test_extended_acl_on_snapshot_inode_is_denied(snapshot, monkeypatch, target, attribute):
    directory, file_path, _ = snapshot
    checked_path = directory if target == "directory" else file_path
    checked_stat = os.stat(checked_path)
    original = reader.os.getxattr

    def extra_acl(fd, name):
        stat_fd = os.fstat(fd)
        if (
            name == attribute and
            (stat_fd.st_dev, stat_fd.st_ino) == (checked_stat.st_dev, checked_stat.st_ino)
        ):
            return b"extended-acl-synthetic-fixture"
        return original(fd, name)

    monkeypatch.setattr(reader.os, "getxattr", extra_acl)
    code = (
        "HML_SNAPSHOT_DIRECTORY_ACL_UNTRUSTED"
        if target == "directory"
        else "HML_SNAPSHOT_FILE_ACL_UNTRUSTED"
    )
    denied(code, lambda: observe(snapshot))


@pytest.mark.parametrize("os_error", [errno.EACCES, errno.EOPNOTSUPP, errno.EIO])
def test_snapshot_reader_fails_closed_when_acl_cannot_be_inspected(
    snapshot, monkeypatch, os_error,
):
    def uninspectable(_fd, _name):
        raise OSError(os_error, "synthetic private xattr metadata")

    monkeypatch.setattr(reader.os, "getxattr", uninspectable)
    denied("HML_SNAPSHOT_DIRECTORY_ACL_UNTRUSTED", lambda: observe(snapshot))


def test_snapshot_reader_refuses_missing_acl_inspection_api(snapshot, monkeypatch):
    monkeypatch.delattr(reader.os, "getxattr", raising=True)
    denied("HML_SNAPSHOT_DIRECTORY_ACL_UNTRUSTED", lambda: observe(snapshot))


def test_acl_introduced_during_snapshot_read_is_rejected(snapshot, monkeypatch):
    directory, file_path, _ = snapshot
    file_stat = os.stat(file_path)
    original_attr = reader.os.getxattr
    original_read = reader._read_bounded
    state = {"acl_changed": False}

    def changed_mid_read(fd, size):
        raw = original_read(fd, size)
        state["acl_changed"] = True
        return raw

    def changed_acl(fd, name):
        meta = os.fstat(fd)
        if (
            state["acl_changed"]
            and name == "system.posix_acl_access"
            and (meta.st_dev, meta.st_ino) == (file_stat.st_dev, file_stat.st_ino)
        ):
            return b"synthetic-acl-after-read"
        return original_attr(fd, name)

    monkeypatch.setattr(reader, "_read_bounded", changed_mid_read)
    monkeypatch.setattr(reader.os, "getxattr", changed_acl)
    denied("HML_SNAPSHOT_FILE_ACL_UNTRUSTED", lambda: observe(snapshot))

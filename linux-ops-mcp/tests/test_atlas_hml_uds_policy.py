"""HML UDS policy negatives. All sockets are disposable and local.

No host, Docker, credentials, network, service unit, chmod/chown outside
pytest tmp_path or privileged user is involved.
"""
from __future__ import annotations

import os
import socket
from pathlib import Path
from types import SimpleNamespace

import pytest

from linux_ops_mcp import atlas_hml_uds_policy as policy


@pytest.fixture
def local_socket(tmp_path):
    parent = tmp_path / "atlas-hml-readonly"
    parent.mkdir()
    os.chmod(parent, 0o750)
    path = parent / "inspect.sock"
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    listener.bind(str(path))
    os.chmod(path, 0o660)
    listener.listen(1)
    try:
        yield path, listener
    finally:
        listener.close()
        path.unlink(missing_ok=True)


def verify(path, **kwargs):
    return policy.verify_socket_metadata(
        path=path, owner_uid=os.getuid(), socket_gid=os.getgid(), **kwargs,
    )


def test_valid_disposable_socket_metadata(local_socket):
    path, _ = local_socket
    assert verify(path) is None


@pytest.mark.parametrize("mode", [0o600, 0o644, 0o666, 0o777, 0o1660])
def test_socket_permissions_fail_closed(local_socket, mode):
    path, _ = local_socket
    os.chmod(path, mode)
    with pytest.raises(policy.HMLUDSPolicyError, match="HML_PROXY_PATH_UNSAFE"):
        verify(path)


@pytest.mark.parametrize("mode", [0o700, 0o770, 0o751, 0o777])
def test_parent_permissions_fail_closed(local_socket, mode):
    path, _ = local_socket
    os.chmod(path.parent, mode)
    with pytest.raises(policy.HMLUDSPolicyError, match="HML_PROXY_PATH_UNSAFE"):
        verify(path)


def test_unexpected_owner_and_group_fail_closed(local_socket):
    path, _ = local_socket
    with pytest.raises(policy.HMLUDSPolicyError, match="HML_PROXY_PATH_UNSAFE"):
        policy.verify_socket_metadata(
            path=path, owner_uid=os.getuid()+1, socket_gid=os.getgid(),
        )
    with pytest.raises(policy.HMLUDSPolicyError, match="HML_PROXY_PATH_UNSAFE"):
        policy.verify_socket_metadata(
            path=path, owner_uid=os.getuid(), socket_gid=os.getgid()+1,
        )


def test_alias_of_raw_socket_cannot_be_passed_as_proxy(local_socket):
    path, _ = local_socket
    with pytest.raises(policy.HMLUDSPolicyError, match="HML_RAW_DOCKER_SOCKET_DENIED"):
        verify(path, raw_sockets=(path,))


def test_unreadable_raw_socket_metadata_fails_closed(local_socket, monkeypatch):
    path, _ = local_socket
    raw = Path("/root/test-unreadable-raw-docker.sock")
    original_stat = Path.stat
    def failing_stat(self, *args, **kwargs):
        if self == raw:
            raise PermissionError("not permitted")
        return original_stat(self, *args, **kwargs)
    monkeypatch.setattr(Path, "stat", failing_stat)
    with pytest.raises(policy.HMLUDSPolicyError, match="HML_PROXY_ALIAS_UNVERIFIED"):
        verify(path, raw_sockets=(raw,))


def test_symlink_not_accepted(local_socket):
    path, _ = local_socket
    alias = path.parent / "alias.sock"
    alias.symlink_to(path)
    with pytest.raises(policy.HMLUDSPolicyError, match="HML_PROXY_PATH_UNSAFE"):
        verify(alias)


def test_fixed_production_path_rejects_owner_or_group_overrides():
    for overrides in ({"owner_uid": 1}, {"socket_gid": 12}):
        with pytest.raises(policy.HMLUDSPolicyError, match="HML_PROXY_PATH_UNSAFE"):
            policy.verify_socket_metadata(path=policy._SOCKET, **overrides)


def test_account_identity_bound_to_named_nonlogin_user(monkeypatch):
    monkeypatch.setattr(policy.pwd, "getpwnam", lambda name: SimpleNamespace(
        pw_uid=995, pw_gid=985, pw_shell="/usr/sbin/nologin",
    ) if name=="atlas-hml" else None)
    monkeypatch.setattr(policy.grp, "getgrnam", lambda name: SimpleNamespace(
        gr_gid=985,
    ) if name=="atlas-hml" else None)
    assert policy.atlas_collector_identity() == (995,985)


@pytest.mark.parametrize("uid,gid,primary,shell", [
    (0,985,985,"/usr/sbin/nologin"),
    (995,0,0,"/usr/sbin/nologin"),
    (995,985,1000,"/usr/sbin/nologin"),
    (995,985,985,"/bin/bash"),
])
def test_invalid_identity_is_denied(monkeypatch, uid, gid, primary, shell):
    monkeypatch.setattr(policy.pwd, "getpwnam", lambda _:
        SimpleNamespace(pw_uid=uid,pw_gid=primary,pw_shell=shell))
    monkeypatch.setattr(policy.grp, "getgrnam", lambda _:
        SimpleNamespace(gr_gid=gid))
    with pytest.raises(policy.HMLUDSPolicyError, match="HML_PROXY_IDENTITY_UNAVAILABLE"):
        policy.atlas_collector_identity()


def test_missing_identity_is_denied(monkeypatch):
    def missing(_):
        raise KeyError("missing")
    monkeypatch.setattr(policy.pwd,"getpwnam",missing)
    with pytest.raises(policy.HMLUDSPolicyError, match="HML_PROXY_IDENTITY_UNAVAILABLE"):
        policy.atlas_collector_identity()

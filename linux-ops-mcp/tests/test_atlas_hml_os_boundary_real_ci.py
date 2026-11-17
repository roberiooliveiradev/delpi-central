"""Disposable GitHub Actions OS security experiment for ATLAS HML (#232).

Only the existing disposable-docker CI job may run these tests, explicitly as
root on that runner. The one privileged action is opening an already-running
CI Docker socket for a harmless GET; no Docker mutation or host/PROD access.

The experiment proves two DIFFERENT properties of the ephemeral runner:
- DAC denies a newly opened Docker socket to a UID without docker membership;
- a pre-connected Docker FD survives a UID drop and can still execute a GET.

This is a deliberate demonstration of the *risk* of inherited FDs, NOT proof
of isolation for the future presenter, root producer, srv-api, or systemd.
"""
from __future__ import annotations

import errno
import json
import os
import pwd
import signal
import socket
import stat
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import pytest

from linux_ops_mcp import atlas_hml_snapshot_file_reader as snapshot_reader


_FLAGS = ("GITHUB_ACTIONS", "ATLAS_DISPOSABLE_DOCKER", "ATLAS_REAL_HML_CHAIN_CI")
_DOCKER_SOCKET = "/var/run/docker.sock"
_PING_REQUEST = b"GET /_ping HTTP/1.1\r\nHost: docker.local\r\nConnection: close\r\n\r\n"

pytestmark = pytest.mark.skipif(
    any(os.environ.get(flag) != "true" for flag in _FLAGS),
    reason="OS/FD test is exclusive to disposable GitHub Actions Docker CI",
)


def _preflight() -> pwd.struct_passwd:
    """Fail closed if the deliberately privileged CI gate is misconfigured."""
    assert all(os.environ.get(flag) == "true" for flag in _FLAGS)
    assert os.name == "posix" and os.getuid() == os.geteuid() == 0
    user = pwd.getpwnam("nobody")
    assert user.pw_uid > 0 and user.pw_gid > 0

    metadata = os.stat(_DOCKER_SOCKET)
    assert stat.S_ISSOCK(metadata.st_mode), "CI Docker socket is not a socket"
    assert not (stat.S_IMODE(metadata.st_mode) & 0o007), "CI Docker socket is world-accessible"
    assert metadata.st_gid != user.pw_gid, "Restricted CI identity belongs to Docker socket group"
    return user


def _run_with_dropped_identity(user: pwd.struct_passwd, probe: Callable[[], str]) -> str:
    """Fork, drop all supplemental groups and UID/GID, return a finite verdict.

    No root process in the target host, unit, or Docker daemon is ever started.
    The parent (CI root) never imports a runtime presenter or invokes PREPARE.
    """
    read_fd, write_fd = os.pipe()
    pid = os.fork()
    if pid == 0:
        os.close(read_fd)
        signal.alarm(7)
        verdict = "PROBE_ERROR"
        try:
            os.setgroups([])
            os.setgid(user.pw_gid)
            os.setuid(user.pw_uid)
            if (
                os.geteuid() != user.pw_uid or os.getegid() != user.pw_gid
                or os.getgroups()
            ):
                verdict = "IDENTITY_NOT_DROPPED"
            else:
                verdict = probe()
        except BaseException:
            verdict = "PROBE_ERROR"
        try:
            os.write(write_fd, verdict.encode("ascii", "strict")[:128])
        except (OSError, UnicodeError):
            pass
        finally:
            os.close(write_fd)
            os._exit(0)

    os.close(write_fd)
    try:
        verdict = os.read(read_fd, 128)
    finally:
        os.close(read_fd)
    observed_pid, status = os.waitpid(pid, 0)
    assert observed_pid == pid
    assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0, "Disposable child failed"
    return verdict.decode("ascii", "strict")


def test_unprivileged_uid_cannot_connect_to_existing_docker_socket():
    user = _preflight()

    def fresh_connection() -> str:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.settimeout(3)
            try:
                client.connect(_DOCKER_SOCKET)
            except OSError as exc:
                return "DAC_DENIED" if exc.errno in (errno.EACCES, errno.EPERM) else "WRONG_ERROR"
            return "UNEXPECTED_RAW_ENGINE_ACCESS"

    assert _run_with_dropped_identity(user, fresh_connection) == "DAC_DENIED"


def test_inherited_connected_docker_fd_bypasses_new_path_dac_check():
    """Positive *counterexample*: privilege drop DOES NOT revoke an open FD.

    Only GET /_ping against disposable CI Engine. No payload/log is emitted.
    This must never be misreported as the presenter being safe.
    """
    user = _preflight()
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as privileged:
        privileged.settimeout(3)
        privileged.connect(_DOCKER_SOCKET)

        def inherited_connection() -> str:
            privileged.sendall(_PING_REQUEST)
            reply = privileged.recv(96)
            return "INHERITED_FD_STILL_WORKS" if reply.startswith(
                b"HTTP/1.1 200 "
            ) else "UNEXPECTED_ENGINE_RESPONSE"

        assert _run_with_dropped_identity(
            user, inherited_connection,
        ) == "INHERITED_FD_STILL_WORKS"


def test_root_owned_snapshot_readable_but_not_mutable_by_restricted_reader():
    """DAC behavior on a temp CI fixture, not /run nor the real atlas-hml UID."""
    user = _preflight()
    with tempfile.TemporaryDirectory(prefix="atlas-hml-ci-", dir="/tmp") as location:
        directory = Path(location)
        os.chown(directory, 0, user.pw_gid)
        os.chmod(directory, 0o750)

        now = datetime.now(timezone.utc)
        payload = {
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
            "observed_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        file = directory / "inspect-snapshot.json"
        file.write_bytes(json.dumps(payload, separators=(",", ":")).encode("ascii"))
        os.chown(file, 0, user.pw_gid)
        os.chmod(file, 0o640)
        private = directory / "root-only-test"
        private.write_bytes(b"DISPOSABLE-CI-ONLY")
        os.chown(private, 0, 0)
        os.chmod(private, 0o600)

        def snapshot_access() -> str:
            result = snapshot_reader._review_from_directory(
                directory, owner_uid=0, expected_gid=user.pw_gid, now=now,
            )
            if (
                result.status != "blocked" or result.snapshot_origin_attested
                or result.docker_access_boundary_attested or result.prepare_eligible
                or result.can_execute
            ):
                return "FALSE_ATTESTATION"

            for target, flags in (
                (file, os.O_WRONLY | os.O_NOFOLLOW),
                (directory / "unauthorized-create", os.O_WRONLY | os.O_CREAT | os.O_EXCL),
                (private, os.O_RDONLY | os.O_NOFOLLOW),
            ):
                try:
                    fd = os.open(target, flags, 0o600)
                except OSError as exc:
                    if exc.errno not in (errno.EACCES, errno.EPERM):
                        return "UNEXPECTED_FS_ERROR"
                else:
                    os.close(fd)
                    return "UNEXPECTED_FS_PERMISSION"
            return "SNAPSHOT_READ_ONLY_AND_BLOCKED"

        assert _run_with_dropped_identity(
            user, snapshot_access,
        ) == "SNAPSHOT_READ_ONLY_AND_BLOCKED"

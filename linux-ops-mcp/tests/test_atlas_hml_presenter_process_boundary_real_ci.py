"""Architecture B real process-boundary experiment: DISPOSABLE GITHUB CI ONLY.

This is NOT a production launcher, daemon, unit or shell script.
It runs only in the existing ephemeral GitHub Actions Docker job, as root
there, and uses a root-owned /tmp fixture and non-root subprocesses.
No Docker HTTP call is made. The root parent opens a Docker UNIX connection
only to model the risk of a privileged FD crossing an exec boundary.

SECURITY LESSON:
  subprocess(close_fds=True, pass_fds=(listener_fd,), user=nobody,
             group=nobody, extra_groups=[])
  must allow a peer-authenticated snapshot GET but NOT transfer Docker's FD.
An intentionally poisoned negative passes the Docker FD and must be refused.
Both probes use the same actual presenter candidate on disposable fixtures.

A green CI result never attests systemd, /run/atlas-hml-readonly, srv-api,
the root producer, LSM, nonstandard Engine aliases or network access.
"""
from __future__ import annotations

import json
import os
import pwd
import socket
import stat
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest


_FLAGS = ("GITHUB_ACTIONS", "ATLAS_DISPOSABLE_DOCKER", "ATLAS_REAL_HML_CHAIN_CI")
_DOCKER = "/var/run/docker.sock"
_NOW = lambda: datetime.now(timezone.utc)

pytestmark = pytest.mark.skipif(
    any(os.getenv(flag) != "true" for flag in _FLAGS),
    reason="disposable Docker CI only: no host or manual invocation",
)

_PRESENTER_CHILD = r"""
import os, socket, stat, sys
from datetime import datetime, timezone
from pathlib import Path
from linux_ops_mcp import atlas_hml_snapshot_presenter_candidate as presenter
from linux_ops_mcp import atlas_hml_snapshot_file_reader as reader

uid, gid, listener_fd, raw_inode = [int(x) for x in sys.argv[1:5]]
directory = Path(sys.argv[5])
if os.getuid() != uid or os.geteuid() != uid or os.getgid() != gid:
    sys.exit(31)
if os.getgroups():
    sys.exit(32)

# Enumerate FDs *after exec*; Python fd inheritance is not limited by
# NoNewPrivileges. Inspect socket inodes and deny even if the forbidden FD
# number was reallocated by exec.
sockets = set()
for name in os.listdir("/proc/self/fd"):
    try:
        metadata = os.fstat(int(name))
    except (ValueError, OSError):
        continue
    if stat.S_ISSOCK(metadata.st_mode):
        sockets.add(metadata.st_ino)
listener_inode = os.fstat(listener_fd).st_ino
if raw_inode in sockets:
    sys.exit(47)  # Intentionally poisoned inheritance fixture is detected.
if sockets != {listener_inode}:
    sys.exit(33)

# Independent negative: a freshly opened Docker socket must be refused by
# kernel DAC even though a root process holds another live Docker FD.
with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as prohibited:
    prohibited.settimeout(2)
    try:
        prohibited.connect("/var/run/docker.sock")
    except PermissionError:
        pass
    else:
        sys.exit(34)

def fixture_reader(*, now):
    return reader._review_from_directory(
        directory, owner_uid=0, expected_gid=gid, now=now,
    )

with socket.socket(fileno=listener_fd) as listener:
    outcome = presenter._serve_one_prebound_snapshot_review(
        listener=listener,
        reader=fixture_reader,
        allowed_uid=uid,
        expected_path=directory / "inspect.sock",
        owner_uid=0,
        socket_gid=gid,
    )
if (
    outcome.status != "blocked"
    or outcome.docker_access_attested
    or outcome.snapshot_origin_attested
    or outcome.prepare_eligible
    or outcome.can_execute
):
    sys.exit(35)
if outcome.http_status not in (200, 404, 405) or not outcome.request_accepted == (outcome.http_status == 200):
    sys.exit(36)
print("BLOCKED_PRESENTER_PROCESS_PASS")
"""

_CLIENT_CHILD = r"""
import json, socket, sys
from pathlib import Path

path, kind = sys.argv[1:3]
requests = {
    "valid": b"GET /v1/hml/public-hub/snapshot HTTP/1.1\r\nHost: atlas-hml.local\r\n\r\n",
    "prod": b"GET /v1/prod/public-hub/snapshot HTTP/1.1\r\nHost: atlas-hml.local\r\n\r\n",
    "post": b"POST /v1/hml/public-hub/snapshot HTTP/1.1\r\nHost: atlas-hml.local\r\n\r\n",
}
with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
    connection.settimeout(3)
    connection.connect(path)
    connection.sendall(requests[kind])
    connection.shutdown(socket.SHUT_WR)
    data = bytearray()
    while True:
        block = connection.recv(2048)
        if not block:
            break
        data.extend(block)
head, body = bytes(data).split(b"\r\n\r\n", 1)
status = int(head.split(b" ", 2)[1])
payload = json.loads(body)
print(json.dumps({"status": status, "body": payload}, sort_keys=True))
"""


def _preflight() -> pwd.struct_passwd:
    """Fail closed if running outside the existing disposable Docker CI job."""
    assert all(os.environ.get(flag) == "true" for flag in _FLAGS)
    assert sys.platform.startswith("linux") and os.geteuid() == os.getuid() == 0
    assert Path("/proc/self/fd").is_dir(), "FD evidence requires Linux procfs"
    user = pwd.getpwnam("nobody")
    assert user.pw_uid > 0 and user.pw_gid > 0
    source = os.stat(_DOCKER)
    assert stat.S_ISSOCK(source.st_mode)
    assert not (stat.S_IMODE(source.st_mode) & 0o007)
    assert source.st_gid != user.pw_gid
    return user


_ISOLATED_MODULES = (
    "__init__.py",
    "atlas_hml_snapshot_presenter_candidate.py",
    "atlas_hml_snapshot_file_reader.py",
    "atlas_hml_snapshot_candidate.py",
    "atlas_hml_posix_acl_review.py",
    "atlas_hml_uds_policy.py",
)


def _stage_readonly_test_modules(directory: Path, user: pwd.struct_passwd) -> None:
    """Copy allowlisted source to root-owned /tmp with group read.

    GitHub's /home/runner may be private to the CI login UID. Dropping to
    nobody and then importing from its checkout would fail even with a valid
    PYTHONPATH. Do not widen workspace permissions or run the child as root.
    """
    source = Path(__file__).resolve().parents[1] / "linux_ops_mcp"
    library_root = directory / "isolated-python"
    package = library_root / "linux_ops_mcp"
    package.mkdir(parents=True, exist_ok=False)
    for name in _ISOLATED_MODULES:
        target = package / name
        target.write_bytes((source / name).read_bytes())
        os.chown(target, 0, user.pw_gid)
        os.chmod(target, 0o640)
    for folder in (library_root, package):
        os.chown(folder, 0, user.pw_gid)
        os.chmod(folder, 0o750)


def _drop_args(user: pwd.struct_passwd, directory: Path) -> dict:
    """Use subprocess kernel UID/GID parameters, NEVER a shell or sudo."""
    return {
        "user": user.pw_uid,
        "group": user.pw_gid,
        "extra_groups": [],
        "close_fds": True,
        "env": {
            "PYTHONPATH": str(directory / "isolated-python"),
            "PYTHONDONTWRITEBYTECODE": "1",
        },
        "cwd": str(directory),
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "text": True,
    }


@pytest.mark.parametrize("kind,expected_status", [
    ("valid", 200),
    ("prod", 404),
    ("post", 405),
])
def test_real_subprocess_privilege_boundary_only_in_ephemeral_ci(kind, expected_status):
    user = _preflight()
    with tempfile.TemporaryDirectory(prefix="atlas-b-ci-", dir="/tmp") as location:
        directory = Path(location)
        os.chown(directory, 0, user.pw_gid)
        os.chmod(directory, 0o750)
        _stage_readonly_test_modules(directory, user)

        now = _NOW()
        snapshot = directory / "inspect-snapshot.json"
        snapshot.write_bytes(json.dumps({
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
        }, separators=(",", ":")).encode("ascii"))
        os.chown(snapshot, 0, user.pw_gid)
        os.chmod(snapshot, 0o640)

        path = directory / "inspect.sock"
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as listening:
            listening.bind(str(path))
            os.chown(path, 0, user.pw_gid)
            os.chmod(path, 0o660)
            listening.listen(2)

            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as raw:
                raw.settimeout(2)
                raw.connect(_DOCKER)
                raw_inode = os.fstat(raw.fileno()).st_ino

                params = _drop_args(user, directory)
                child = subprocess.Popen([
                    sys.executable, "-B", "-c", _PRESENTER_CHILD,
                    str(user.pw_uid), str(user.pw_gid),
                    str(listening.fileno()), str(raw_inode), str(directory),
                ], pass_fds=(listening.fileno(),), **params)
                try:
                    client = subprocess.run([
                        sys.executable, "-B", "-c", _CLIENT_CHILD,
                        str(path), kind,
                    ], timeout=7, **params)
                    assert client.returncode == 0, "Disposable peer request failed"
                    observed = json.loads(client.stdout)
                    assert observed["status"] == expected_status
                    if expected_status == 200:
                        body = observed["body"]
                        assert body["status"] == "blocked"
                        assert body["environment"] == "hml"
                        assert body["service_id"] == "public-hub"
                        assert body["running_untrusted"] is True
                        assert body["healthy_untrusted"] is True
                        assert body["snapshot_origin_attested"] is False
                        assert body["docker_access_boundary_attested"] is False
                        assert body["prepare_eligible"] is False
                        assert body["can_execute"] is False
                        assert "container_id" not in body
                        assert "image_id" not in body
                    else:
                        assert observed["body"] == {"error": "HML_PRESENTER_REQUEST_DENIED"}
                    out, err = child.communicate(timeout=7)
                    assert child.returncode == 0, f"Disposable presenter exit={child.returncode}"
                    assert out.strip() == "BLOCKED_PRESENTER_PROCESS_PASS"
                    assert not err.strip(), "Unexpected CI presenter stderr"
                finally:
                    if child.poll() is None:
                        child.kill()
                        child.communicate(timeout=3)


def test_intentionally_passed_privileged_docker_fd_is_detected_before_serving():
    """Negative control: an exec with Docker FD would violate Architecture B."""
    user = _preflight()
    with tempfile.TemporaryDirectory(prefix="atlas-b-leak-ci-", dir="/tmp") as location:
        directory = Path(location)
        os.chown(directory, 0, user.pw_gid)
        os.chmod(directory, 0o750)
        _stage_readonly_test_modules(directory, user)

        path = directory / "inspect.sock"
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as listener:
            listener.bind(str(path))
            os.chown(path, 0, user.pw_gid)
            os.chmod(path, 0o660)
            listener.listen(1)
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as docker:
                docker.settimeout(2)
                docker.connect(_DOCKER)
                root_socket_inode = os.fstat(docker.fileno()).st_ino
                result = subprocess.run([
                    sys.executable, "-B", "-c", _PRESENTER_CHILD,
                    str(user.pw_uid), str(user.pw_gid),
                    str(listener.fileno()), str(root_socket_inode), str(directory),
                ], pass_fds=(listener.fileno(), docker.fileno()),
                   timeout=6, **_drop_args(user, directory))
                assert result.returncode == 47, (
                    "Raw Docker FD leaked into presenter without being rejected"
                )
                assert result.stdout == ""

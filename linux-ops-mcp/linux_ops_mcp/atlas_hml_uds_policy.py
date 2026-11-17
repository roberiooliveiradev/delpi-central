"""Fail-closed UNIX socket metadata policy for the ATLAS HML Docker projection.

Source only: no listener, daemon, chmod, chown, Docker access or deployment.
The fixed root-owned socket must be group-accessible *only* to atlas-hml.
Metadata checks do not attest the process behind the socket, Docker upstream
confinement, NSS membership completeness or transport/process identity.
"""
from __future__ import annotations

import grp
import pwd
import stat
from pathlib import Path

_SOCKET = Path("/run/atlas-hml-readonly/inspect.sock")
_RAW_DOCKER = (Path("/run/docker.sock"), Path("/var/run/docker.sock"))


class HMLUDSPolicyError(Exception):
    """Finite error code, never an OS exception carrying host metadata."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def atlas_collector_identity() -> tuple[int, int]:
    """Resolve the dedicated local identity, not a request-supplied UID/GID."""
    try:
        account = pwd.getpwnam("atlas-hml")
        group = grp.getgrnam("atlas-hml")
    except KeyError:
        raise HMLUDSPolicyError("HML_PROXY_IDENTITY_UNAVAILABLE") from None
    if (
        account.pw_uid <= 0
        or group.gr_gid <= 0
        or account.pw_gid != group.gr_gid
        or account.pw_shell not in ("/usr/sbin/nologin", "/sbin/nologin")
    ):
        raise HMLUDSPolicyError("HML_PROXY_IDENTITY_UNAVAILABLE")
    return account.pw_uid, group.gr_gid


def verify_socket_metadata(
    *,
    path: Path = _SOCKET,
    owner_uid: int = 0,
    socket_gid: int | None = None,
    raw_sockets: tuple[Path, ...] = _RAW_DOCKER,
) -> None:
    """Verify UDS pathname policy before any connect/accept.

    Non-default path/owner/group inputs exist solely for disposable CI
    fixtures; production callers must use the fixed path and root ownership.
    No file-descriptor inode comparison is attempted: Linux AF_UNIX socket
    descriptors use sockfs inode numbers distinct from pathname inode numbers.
    """
    if (
        type(path) is not Path
        or not path.is_absolute()
        or type(owner_uid) is not int or owner_uid < 0
        or type(raw_sockets) is not tuple
        or not all(type(raw) is Path and raw.is_absolute() for raw in raw_sockets)
        or (socket_gid is not None and (type(socket_gid) is not int or socket_gid < 0))
    ):
        raise HMLUDSPolicyError("HML_PROXY_PATH_UNSAFE")
    if path == _SOCKET and (owner_uid != 0 or socket_gid is not None):
        # Never let production consumers override the owner/group policy.
        raise HMLUDSPolicyError("HML_PROXY_PATH_UNSAFE")
    if socket_gid is None:
        _, socket_gid = atlas_collector_identity()
    try:
        parent = path.parent.lstat()
        entry = path.lstat()
        if (
            path.parent.is_symlink()
            or not stat.S_ISDIR(parent.st_mode)
            or parent.st_uid != owner_uid
            or bool(parent.st_mode & (stat.S_IWGRP | stat.S_IWOTH))
            or not stat.S_ISSOCK(entry.st_mode)
            or entry.st_uid != owner_uid
            or entry.st_gid != socket_gid
            or stat.S_IMODE(entry.st_mode) != 0o660
        ):
            raise HMLUDSPolicyError("HML_PROXY_PATH_UNSAFE")
        for raw in raw_sockets:
            try:
                raw_entry = raw.stat()
            except FileNotFoundError:
                continue
            except OSError:
                raise HMLUDSPolicyError("HML_PROXY_ALIAS_UNVERIFIED") from None
            if (entry.st_dev, entry.st_ino) == (raw_entry.st_dev, raw_entry.st_ino):
                raise HMLUDSPolicyError("HML_RAW_DOCKER_SOCKET_DENIED")
    except FileNotFoundError:
        raise HMLUDSPolicyError("HML_PROXY_UNAVAILABLE") from None
    except HMLUDSPolicyError:
        raise
    except OSError:
        raise HMLUDSPolicyError("HML_PROXY_PATH_UNSAFE") from None

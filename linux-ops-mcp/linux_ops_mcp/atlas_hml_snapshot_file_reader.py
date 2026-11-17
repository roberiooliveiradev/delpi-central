"""HML snapshot file review candidate: read-only, not an activated data source.

Designed for architecture review of the one-shot producer proposal. This
module reads no Docker endpoint, opens no socket, creates no file/process,
and is NOT wired to MCP, the prebound UDS proxy, PREPARE or ACT.

Root-owned metadata and a recent JSON timestamp are NOT origin attestation.
An operator with root access can still forge or replace this snapshot.
"""
from __future__ import annotations

import grp
import os
import stat
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .atlas_hml_snapshot_candidate import (
    SnapshotContractError,
    SnapshotDiagnostic,
    review_untrusted_snapshot,
)

_FIXED_DIRECTORY = Path("/run/atlas-hml-readonly")
_FILENAME = "inspect-snapshot.json"
_MAX_PAYLOAD = 2048
_MAX_AGE = timedelta(seconds=60)
_MAX_FUTURE_SKEW = timedelta(seconds=5)
_DIRECTORY_MODE = 0o750
_FILE_MODE = 0o640


class HMLSnapshotFileError(Exception):
    """Sanitized denial code: do not forward OS exception strings."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _metadata_signature(value: os.stat_result) -> tuple[int, ...]:
    return (
        value.st_dev, value.st_ino, value.st_uid, value.st_gid,
        value.st_mode, value.st_nlink, value.st_size,
        value.st_mtime_ns, value.st_ctime_ns,
    )


def _read_bounded(fd: int, expected_size: int) -> bytes:
    """One bounded read; a short read is a fail-closed result."""
    if not 1 <= expected_size <= _MAX_PAYLOAD:
        raise HMLSnapshotFileError("HML_SNAPSHOT_FILE_UNSAFE")
    data = os.read(fd, _MAX_PAYLOAD + 1)
    if len(data) != expected_size:
        raise HMLSnapshotFileError("HML_SNAPSHOT_FILE_CHANGED")
    return data


def _review_from_directory(
    directory: Path, *,
    owner_uid: int,
    expected_gid: int,
    now: datetime,
) -> SnapshotDiagnostic:
    """Internal fixture-capable read. Never an MCP/CLI/HTTP entrypoint.

    Production callers MUST use read_fixed_hml_snapshot() rather than
    injecting a path or expected ownership.
    """
    if (
        not isinstance(directory, Path)
        or not directory.is_absolute()
        or type(owner_uid) is not int or owner_uid < 0
        or type(expected_gid) is not int or expected_gid < 0
        or type(now) is not datetime
        or now.tzinfo is None or now.utcoffset() is None
        or not hasattr(os, "O_NOFOLLOW")
        or not hasattr(os, "O_DIRECTORY")
    ):
        raise HMLSnapshotFileError("HML_SNAPSHOT_REVIEW_INPUT_INVALID")

    directory_fd = -1
    file_fd = -1
    try:
        directory_fd = os.open(
            directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
        )
        parent = os.fstat(directory_fd)
        if (
            not stat.S_ISDIR(parent.st_mode)
            or parent.st_uid != owner_uid
            or parent.st_gid != expected_gid
            or stat.S_IMODE(parent.st_mode) != _DIRECTORY_MODE
        ):
            raise HMLSnapshotFileError("HML_SNAPSHOT_DIRECTORY_UNSAFE")

        file_fd = os.open(
            _FILENAME,
            os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
            dir_fd=directory_fd,
        )
        before = os.fstat(file_fd)
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_uid != owner_uid
            or before.st_gid != expected_gid
            or stat.S_IMODE(before.st_mode) != _FILE_MODE
            or before.st_nlink != 1
            or before.st_dev != parent.st_dev
            or not 1 <= before.st_size <= _MAX_PAYLOAD
        ):
            raise HMLSnapshotFileError("HML_SNAPSHOT_FILE_UNSAFE")

        now_utc = now.astimezone(timezone.utc)
        observed_fs = datetime.fromtimestamp(before.st_mtime, timezone.utc)
        fs_age = now_utc - observed_fs
        if not -_MAX_FUTURE_SKEW <= fs_age <= _MAX_AGE:
            raise HMLSnapshotFileError("HML_SNAPSHOT_FILE_MTIME_UNTRUSTED")

        raw = _read_bounded(file_fd, before.st_size)
        after = os.fstat(file_fd)
        pathname = os.stat(_FILENAME, dir_fd=directory_fd, follow_symlinks=False)
        parent_again = os.stat(directory, follow_symlinks=False)
        if (
            _metadata_signature(before) != _metadata_signature(after)
            or _metadata_signature(before) != _metadata_signature(pathname)
            or _metadata_signature(parent) != _metadata_signature(parent_again)
        ):
            raise HMLSnapshotFileError("HML_SNAPSHOT_FILE_CHANGED")

        try:
            return review_untrusted_snapshot(raw, now=now)
        except SnapshotContractError as exc:
            raise HMLSnapshotFileError(exc.code) from None
    except FileNotFoundError:
        raise HMLSnapshotFileError("HML_SNAPSHOT_FILE_UNAVAILABLE") from None
    except HMLSnapshotFileError:
        raise
    except (OSError, OverflowError, ValueError, TypeError):
        raise HMLSnapshotFileError("HML_SNAPSHOT_FILE_UNVERIFIABLE") from None
    finally:
        if file_fd >= 0:
            os.close(file_fd)
        if directory_fd >= 0:
            os.close(directory_fd)


def read_fixed_hml_snapshot(*, now: datetime) -> SnapshotDiagnostic:
    """Candidate-only fixed path, no caller-supplied UID/GID or filename.

    This does not attest a producer, file atomicity, an image, a release,
    the supervisor, or anything required to enable PREPARE or ACT.
    """
    try:
        group = grp.getgrnam("atlas-hml")
    except (KeyError, OSError):
        raise HMLSnapshotFileError("HML_SNAPSHOT_READER_IDENTITY_UNAVAILABLE") from None
    if type(group.gr_gid) is not int or group.gr_gid <= 0:
        raise HMLSnapshotFileError("HML_SNAPSHOT_READER_IDENTITY_UNAVAILABLE")
    return _review_from_directory(
        _FIXED_DIRECTORY,
        owner_uid=0,
        expected_gid=group.gr_gid,
        now=now,
    )

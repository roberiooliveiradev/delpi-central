"""Candidate-only HML snapshot handoff for security review, NOT deployment.

The pure encoder accepts only typed, sanitized RuntimeContainer metadata.
The internal publisher writes only to a caller-provided disposable directory
under strict owner/group/mode checks. There is no production entrypoint, Docker
client, timer, service unit, CLI, MCP tool or privileged-process setup.

Atomic rename protects against a partial *reader-visible* file, not against a
compromised producer, file ownership spoofing by root, replay, or time-of-check
and time-of-use by another privileged host process. PREPARE/ACT stay disabled.
"""
from __future__ import annotations

import json
import os
import secrets
import stat
from datetime import datetime, timezone
from pathlib import Path

from .atlas_hml_snapshot_candidate import (
    SnapshotContractError,
    review_untrusted_snapshot,
)
from .atlas_hml_snapshot_file_reader import (
    _DIRECTORY_MODE,
    _FILE_MODE,
    _FILENAME,
    _MAX_PAYLOAD,
)
from .deploy_host_source import RuntimeContainer

_EXPECTED_SOURCE = "root-one-shot-snapshot-claim-untrusted"
_STAGE_PREFIX = ".atlas-hml-stage-"


class HMLSnapshotPublishError(Exception):
    """Sanitized failure code only. Never print raw snapshot or host paths."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def build_hml_snapshot_claim(
    container: RuntimeContainer, *, observed_at: datetime,
) -> bytes:
    """Construct a minimal *untrusted* HML-only JSON claim, without I/O."""
    if (
        type(container) is not RuntimeContainer
        or type(observed_at) is not datetime
        or observed_at.tzinfo is None
        or observed_at.utcoffset() is None
        or type(container.running) is not bool
        or type(container.healthy) is not bool
        or type(container.container_id) is not str
        or type(container.image_id) is not str
    ):
        raise HMLSnapshotPublishError("HML_SNAPSHOT_PRODUCER_INPUT_INVALID")

    timestamp = (
        observed_at.astimezone(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
    document = {
        "schema": "atlas.hml.inspect.v1",
        "source": _EXPECTED_SOURCE,
        "environment": "hml",
        "compose_project": "delpi-hml",
        "service_id": "public-hub",
        "container_name": "delpi-hml-public-hub",
        "container_id": container.container_id,
        "image_id": container.image_id,
        "running": container.running,
        "healthy": container.healthy,
        "observed_at": timestamp,
    }
    try:
        raw = json.dumps(
            document, separators=(",", ":"), sort_keys=True, ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
        report = review_untrusted_snapshot(raw, now=observed_at)
    except (SnapshotContractError, TypeError, ValueError, UnicodeError):
        raise HMLSnapshotPublishError("HML_SNAPSHOT_PRODUCER_INPUT_INVALID") from None
    if report.prepare_eligible or report.can_execute or report.status != "blocked":
        raise HMLSnapshotPublishError("HML_SNAPSHOT_AUTHORIZATION_DENIED")
    return raw


def _dir_identity(value: os.stat_result) -> tuple[int, int, int, int, int]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_uid,
        value.st_gid,
        stat.S_IMODE(value.st_mode),
    )


def _validate_destination(
    dir_fd: int, *, parent: os.stat_result, uid: int, gid: int,
) -> None:
    """Refuse to overwrite unsafe existing names; absence is allowed."""
    try:
        current = os.stat(
            _FILENAME, dir_fd=dir_fd, follow_symlinks=False,
        )
    except FileNotFoundError:
        return
    if (
        not stat.S_ISREG(current.st_mode)
        or current.st_dev != parent.st_dev
        or current.st_uid != uid
        or current.st_gid != gid
        or stat.S_IMODE(current.st_mode) != _FILE_MODE
        or current.st_nlink != 1
    ):
        raise HMLSnapshotPublishError("HML_SNAPSHOT_DESTINATION_UNSAFE")


def _publish_in_review_directory(
    directory: Path, *, raw: bytes, owner_uid: int,
    expected_gid: int, now: datetime,
) -> None:
    """Internal fixture-capable atomic handoff, without any fixed host writer.

    Caller must hold the directory privileges and bear independent-review
    responsibility. No production code calls this function.
    """
    if (
        not isinstance(directory, Path)
        or not directory.is_absolute()
        or type(raw) is not bytes
        or type(owner_uid) is not int or owner_uid < 0
        or type(expected_gid) is not int or expected_gid < 0
        or type(now) is not datetime
        or now.tzinfo is None or now.utcoffset() is None
        or not all(hasattr(os, flag) for flag in (
            "O_NOFOLLOW", "O_DIRECTORY", "O_CLOEXEC", "O_EXCL",
        ))
    ):
        raise HMLSnapshotPublishError("HML_SNAPSHOT_PUBLISH_INPUT_INVALID")

    try:
        # Validate before filesystem writes; do not trust source/clock as proof.
        report = review_untrusted_snapshot(raw, now=now)
    except SnapshotContractError as exc:
        raise HMLSnapshotPublishError(exc.code) from None
    if (
        len(raw) > _MAX_PAYLOAD or report.status != "blocked"
        or report.can_execute or report.prepare_eligible
    ):
        raise HMLSnapshotPublishError("HML_SNAPSHOT_PUBLISH_INPUT_INVALID")

    directory_fd = -1
    staged_fd = -1
    staged_name: str | None = None
    try:
        directory_fd = os.open(
            directory,
            os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
        )
        parent = os.fstat(directory_fd)
        if (
            not stat.S_ISDIR(parent.st_mode)
            or parent.st_uid != owner_uid
            or parent.st_gid != expected_gid
            or stat.S_IMODE(parent.st_mode) != _DIRECTORY_MODE
        ):
            raise HMLSnapshotPublishError("HML_SNAPSHOT_DIRECTORY_UNSAFE")

        _validate_destination(
            directory_fd, parent=parent, uid=owner_uid, gid=expected_gid,
        )
        staged_name = _STAGE_PREFIX + secrets.token_hex(12)
        staged_fd = os.open(
            staged_name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
            0o600,
            dir_fd=directory_fd,
        )
        stage = os.fstat(staged_fd)
        if (
            not stat.S_ISREG(stage.st_mode)
            or stage.st_uid != owner_uid
            or stage.st_nlink != 1
            or stage.st_dev != parent.st_dev
        ):
            raise HMLSnapshotPublishError("HML_SNAPSHOT_STAGE_UNSAFE")
        if stage.st_gid != expected_gid:
            os.fchown(staged_fd, owner_uid, expected_gid)
        os.fchmod(staged_fd, _FILE_MODE)
        stage = os.fstat(staged_fd)
        if (
            stage.st_uid != owner_uid
            or stage.st_gid != expected_gid
            or stat.S_IMODE(stage.st_mode) != _FILE_MODE
            or stage.st_nlink != 1
        ):
            raise HMLSnapshotPublishError("HML_SNAPSHOT_STAGE_UNSAFE")

        offset = 0
        while offset < len(raw):
            written = os.write(staged_fd, raw[offset:])
            if written <= 0:
                raise HMLSnapshotPublishError("HML_SNAPSHOT_WRITE_FAILED")
            offset += written

        os.fsync(staged_fd)
        stage_after = os.fstat(staged_fd)
        if stage_after.st_size != len(raw):
            raise HMLSnapshotPublishError("HML_SNAPSHOT_STAGE_UNSAFE")

        # Check the existing name again; this is NOT an anti-root TOCTOU proof.
        _validate_destination(
            directory_fd, parent=parent, uid=owner_uid, gid=expected_gid,
        )
        os.replace(
            staged_name, _FILENAME,
            src_dir_fd=directory_fd, dst_dir_fd=directory_fd,
        )
        staged_name = None
        os.fsync(directory_fd)

        after = os.stat(
            _FILENAME, dir_fd=directory_fd, follow_symlinks=False,
        )
        path_parent = os.stat(directory, follow_symlinks=False)
        if (
            not stat.S_ISREG(after.st_mode)
            or after.st_dev != stage_after.st_dev
            or after.st_ino != stage_after.st_ino
            or after.st_size != stage_after.st_size
            or after.st_uid != owner_uid
            or after.st_gid != expected_gid
            or stat.S_IMODE(after.st_mode) != _FILE_MODE
            or _dir_identity(path_parent) != _dir_identity(parent)
        ):
            raise HMLSnapshotPublishError("HML_SNAPSHOT_PUBLISHED_STATE_UNVERIFIED")

    except HMLSnapshotPublishError:
        raise
    except (OSError, ValueError, OverflowError, TypeError):
        raise HMLSnapshotPublishError("HML_SNAPSHOT_PUBLISH_UNAVAILABLE") from None
    finally:
        if staged_fd >= 0:
            os.close(staged_fd)
        if staged_name is not None and directory_fd >= 0:
            try:
                os.unlink(staged_name, dir_fd=directory_fd)
            except OSError:
                pass
        if directory_fd >= 0:
            os.close(directory_fd)

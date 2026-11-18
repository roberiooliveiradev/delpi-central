"""Persistent, fail-closed HML snapshot continuity store (disposable dirs only).

Atomic rename + fsync candidate for anti-replay across simulated restarts.
Operates only on caller-supplied absolute temporary directories. Never touches
/run, Docker, systemd, MCP or host production paths. Corruption, truncated
writes, counter regression and concurrent writers fail closed.
"""
from __future__ import annotations

import fcntl
import json
import os
import secrets
import stat
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .atlas_hml_posix_acl_review import has_no_extended_posix_acl

_SCHEMA = "atlas.hml.continuity-state.v1"
_FILENAME = "continuity-state.v1.json"
_STAGE_PREFIX = ".atlas-hml-cont-stage-"
_DIR_MODE = 0o750
_FILE_MODE = 0o640
_MAX_BYTES = 2048
_FIELDS = frozenset({
    "schema", "environment", "service_id", "generation", "digest",
    "observed_at", "container_id", "image_id", "updated_at",
})


class HMLContinuityStoreError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class HMLContinuityRecord:
    generation: int
    digest: str
    observed_at: datetime
    container_id: str
    image_id: str
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class HMLContinuityCommitResult:
    record: HMLContinuityRecord
    status: str = "blocked"
    persistent_anti_replay_host_attested: bool = False
    prepare_eligible: bool = False
    can_execute: bool = False


def _unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    out: dict[str, object] = {}
    for key, value in pairs:
        if key in out:
            raise HMLContinuityStoreError("HML_CONTINUITY_STORE_DUPLICATE")
        out[key] = value
    return out


def _reject_constant(_: str) -> object:
    raise HMLContinuityStoreError("HML_CONTINUITY_STORE_JSON_INVALID")


def _parse_record(raw: bytes) -> HMLContinuityRecord:
    if type(raw) is not bytes or not 1 <= len(raw) <= _MAX_BYTES or b"\x00" in raw:
        raise HMLContinuityStoreError("HML_CONTINUITY_STORE_CORRUPT")
    try:
        document = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_unique,
            parse_constant=_reject_constant,
        )
    except HMLContinuityStoreError:
        raise
    except (ValueError, UnicodeError, TypeError, RecursionError):
        raise HMLContinuityStoreError("HML_CONTINUITY_STORE_CORRUPT") from None
    if type(document) is not dict or set(document) != _FIELDS:
        raise HMLContinuityStoreError("HML_CONTINUITY_STORE_CORRUPT")
    if (
        document["schema"] != _SCHEMA
        or document["environment"] != "hml"
        or document["service_id"] != "public-hub"
        or type(document["generation"]) is not int
        or document["generation"] < 1
        or type(document["digest"]) is not str
        or len(document["digest"]) != 64
        or any(c not in "0123456789abcdef" for c in document["digest"])
        or type(document["container_id"]) is not str
        or type(document["image_id"]) is not str
        or type(document["observed_at"]) is not str
        or type(document["updated_at"]) is not str
    ):
        raise HMLContinuityStoreError("HML_CONTINUITY_STORE_CORRUPT")
    try:
        observed = datetime.fromisoformat(
            document["observed_at"].replace("Z", "+00:00"),
        )
        updated = datetime.fromisoformat(
            document["updated_at"].replace("Z", "+00:00"),
        )
    except ValueError:
        raise HMLContinuityStoreError("HML_CONTINUITY_STORE_CORRUPT") from None
    if observed.tzinfo is None or updated.tzinfo is None:
        raise HMLContinuityStoreError("HML_CONTINUITY_STORE_CORRUPT")
    return HMLContinuityRecord(
        generation=document["generation"],
        digest=document["digest"],
        observed_at=observed,
        container_id=document["container_id"],
        image_id=document["image_id"],
        updated_at=updated,
    )


def _encode(record: HMLContinuityRecord) -> bytes:
    document = {
        "schema": _SCHEMA,
        "environment": "hml",
        "service_id": "public-hub",
        "generation": record.generation,
        "digest": record.digest,
        "observed_at": record.observed_at.astimezone(timezone.utc)
        .isoformat().replace("+00:00", "Z"),
        "container_id": record.container_id,
        "image_id": record.image_id,
        "updated_at": record.updated_at.astimezone(timezone.utc)
        .isoformat().replace("+00:00", "Z"),
    }
    return json.dumps(
        document, separators=(",", ":"), sort_keys=True, ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


class HMLContinuityStore:
    """Disposable-only FD-safe continuity store; no host operational entrypoint.

    Each read and read-modify-write is covered by a nonblocking advisory flock
    on the SAME verified directory descriptor. A competing cooperating process
    fails closed rather than racing a generation. An attacker with root or a
    process ignoring advisory locking still defeats this boundary.
    """

    def __init__(self, directory: Path, *, owner_uid: int, expected_gid: int) -> None:
        if (
            type(directory) is not type(Path("/")) or not directory.is_absolute()
            or type(owner_uid) is not int or owner_uid < 0
            or type(expected_gid) is not int or expected_gid < 0
            or not all(hasattr(os, flag) for flag in (
                "O_NOFOLLOW", "O_DIRECTORY", "O_CLOEXEC", "O_NONBLOCK", "O_EXCL",
            ))
        ):
            raise HMLContinuityStoreError("HML_CONTINUITY_STORE_INPUT_INVALID")
        self._directory = directory
        self._uid = owner_uid
        self._gid = expected_gid
        self._fault: str | None = None
        self._seen_existing = False

    def _halt(self, code: str) -> None:
        if self._fault is None:
            self._fault = code
        raise HMLContinuityStoreError(self._fault)

    @property
    def halted(self) -> bool:
        return self._fault is not None

    @staticmethod
    def _signature(meta: os.stat_result) -> tuple[int, ...]:
        return (
            meta.st_dev, meta.st_ino, meta.st_uid, meta.st_gid,
            meta.st_mode, meta.st_nlink, meta.st_size,
            meta.st_mtime_ns, meta.st_ctime_ns,
        )

    @staticmethod
    def _directory_identity(meta: os.stat_result) -> tuple[int, ...]:
        # Renaming/writing a child legitimately changes directory mtime/ctime.
        return (
            meta.st_dev, meta.st_ino, meta.st_uid, meta.st_gid,
            meta.st_mode, meta.st_nlink,
        )

    @contextmanager
    def _locked_directory(self):
        """One checked descriptor for both the read and atomic replacement."""
        fd = -1
        try:
            fd = os.open(
                self._directory,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
            )
            parent = os.fstat(fd)
            if (
                not stat.S_ISDIR(parent.st_mode)
                or parent.st_uid != self._uid
                or parent.st_gid != self._gid
                or stat.S_IMODE(parent.st_mode) != _DIR_MODE
                or not has_no_extended_posix_acl(fd, directory=True)
            ):
                self._halt("HML_CONTINUITY_STORE_DIR_UNSAFE")
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                self._halt("HML_CONTINUITY_STORE_BUSY")
            if self._directory_identity(parent) != self._directory_identity(
                os.stat(self._directory, follow_symlinks=False)
            ):
                self._halt("HML_CONTINUITY_STORE_DIR_CHANGED")
            yield fd, parent
            if (
                self._directory_identity(parent) != self._directory_identity(os.fstat(fd))
                or self._directory_identity(parent) != self._directory_identity(
                    os.stat(self._directory, follow_symlinks=False)
                )
                or not has_no_extended_posix_acl(fd, directory=True)
            ):
                self._halt("HML_CONTINUITY_STORE_DIR_CHANGED")
        except HMLContinuityStoreError:
            raise
        except (OSError, ValueError, TypeError, OverflowError):
            self._halt("HML_CONTINUITY_STORE_UNAVAILABLE")
        finally:
            if fd >= 0:
                os.close(fd)

    def _read_locked(self, directory_fd: int, parent: os.stat_result) -> HMLContinuityRecord | None:
        file_fd = -1
        try:
            try:
                file_fd = os.open(
                    _FILENAME,
                    os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
                    dir_fd=directory_fd,
                )
            except FileNotFoundError:
                if self._seen_existing:
                    self._halt("HML_CONTINUITY_STORE_STATE_LOST")
                return None
            before = os.fstat(file_fd)
            if (
                not stat.S_ISREG(before.st_mode)
                or before.st_uid != self._uid
                or before.st_gid != self._gid
                or stat.S_IMODE(before.st_mode) != _FILE_MODE
                or before.st_nlink != 1
                or before.st_dev != parent.st_dev
                or not 1 <= before.st_size <= _MAX_BYTES
                or not has_no_extended_posix_acl(file_fd, directory=False)
            ):
                self._halt("HML_CONTINUITY_STORE_FILE_UNSAFE")
            raw = os.read(file_fd, _MAX_BYTES + 1)
            after = os.fstat(file_fd)
            current = os.stat(_FILENAME, dir_fd=directory_fd, follow_symlinks=False)
            if (
                len(raw) != before.st_size
                or self._signature(before) != self._signature(after)
                or self._signature(before) != self._signature(current)
                or not has_no_extended_posix_acl(file_fd, directory=False)
            ):
                self._halt("HML_CONTINUITY_STORE_FILE_CHANGED")
            try:
                record = _parse_record(raw)
            except HMLContinuityStoreError:
                self._halt("HML_CONTINUITY_STORE_CORRUPT")
            self._seen_existing = True
            return record
        except HMLContinuityStoreError:
            raise
        except (OSError, ValueError, TypeError, OverflowError):
            self._halt("HML_CONTINUITY_STORE_FILE_UNSAFE")
        finally:
            if file_fd >= 0:
                os.close(file_fd)

    def load(self) -> HMLContinuityRecord | None:
        """FD-safe load; a vanished state after a prior read is terminal.

        A brand-new process cannot distinguish lost state from first boot.
        Independent bootstrapping/rollback protection is a future SEC gate.
        """
        if self._fault is not None:
            raise HMLContinuityStoreError(self._fault)
        with self._locked_directory() as (fd, parent):
            return self._read_locked(fd, parent)

    def commit(self, candidate: HMLContinuityRecord) -> HMLContinuityCommitResult:
        """Serialized monotonic update inside the SAME directory lock."""
        if self._fault is not None:
            raise HMLContinuityStoreError(self._fault)
        if type(candidate) is not HMLContinuityRecord:
            self._halt("HML_CONTINUITY_STORE_INPUT_INVALID")
        if (
            type(candidate.generation) is not int
            or not 1 <= candidate.generation <= (2**63 - 1)
            or type(candidate.digest) is not str or len(candidate.digest) != 64
            or any(c not in "0123456789abcdef" for c in candidate.digest)
            or type(candidate.container_id) is not str or len(candidate.container_id) != 64
            or any(c not in "0123456789abcdef" for c in candidate.container_id)
            or type(candidate.image_id) is not str
            or not candidate.image_id.startswith("sha256:")
            or len(candidate.image_id) != 71
            or any(c not in "0123456789abcdef" for c in candidate.image_id[7:])
            or type(candidate.observed_at) is not datetime
            or candidate.observed_at.tzinfo is None
            or candidate.observed_at.utcoffset() is None
            or type(candidate.updated_at) is not datetime
            or candidate.updated_at.tzinfo is None
            or candidate.updated_at.utcoffset() is None
        ):
            self._halt("HML_CONTINUITY_STORE_INPUT_INVALID")
        with self._locked_directory() as (fd, parent):
            previous = self._read_locked(fd, parent)
            if previous is not None:
                if candidate.generation < previous.generation:
                    self._halt("HML_CONTINUITY_STORE_COUNTER_REGRESSION")
                if candidate.generation == previous.generation:
                    if candidate.digest == previous.digest:
                        self._halt("HML_CONTINUITY_STORE_REPLAY")
                    self._halt("HML_CONTINUITY_STORE_GENERATION_CONFLICT")
                if candidate.generation != previous.generation + 1:
                    self._halt("HML_CONTINUITY_STORE_COUNTER_GAP")
                if candidate.observed_at <= previous.observed_at:
                    self._halt("HML_CONTINUITY_STORE_TIME_REGRESSION")
                if (
                    candidate.container_id != previous.container_id
                    or candidate.image_id != previous.image_id
                ):
                    self._halt("HML_CONTINUITY_STORE_IDENTITY_CHANGED")
            elif candidate.generation != 1:
                self._halt("HML_CONTINUITY_STORE_COUNTER_GAP")
            self._write_locked(fd, parent, candidate)
        return HMLContinuityCommitResult(record=candidate)

    def _write_locked(
        self, directory_fd: int, parent: os.stat_result, record: HMLContinuityRecord,
    ) -> None:
        raw = _encode(record)
        if len(raw) > _MAX_BYTES:
            self._halt("HML_CONTINUITY_STORE_INPUT_INVALID")
        staged_fd = -1
        staged_name: str | None = None
        try:
            staged_name = _STAGE_PREFIX + secrets.token_hex(8)
            staged_fd = os.open(
                staged_name,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
                0o600,
                dir_fd=directory_fd,
            )
            metadata = os.fstat(staged_fd)
            if metadata.st_gid != self._gid:
                os.fchown(staged_fd, self._uid, self._gid)
            os.fchmod(staged_fd, _FILE_MODE)
            metadata = os.fstat(staged_fd)
            if (
                not stat.S_ISREG(metadata.st_mode)
                or metadata.st_uid != self._uid
                or metadata.st_gid != self._gid
                or metadata.st_nlink != 1
                or metadata.st_dev != parent.st_dev
                or stat.S_IMODE(metadata.st_mode) != _FILE_MODE
                or not has_no_extended_posix_acl(staged_fd, directory=False)
            ):
                self._halt("HML_CONTINUITY_STORE_STAGE_UNSAFE")
            offset = 0
            while offset < len(raw):
                written = os.write(staged_fd, raw[offset:])
                if written <= 0:
                    self._halt("HML_CONTINUITY_STORE_WRITE_FAILED")
                offset += written
            os.fsync(staged_fd)
            metadata = os.fstat(staged_fd)
            if metadata.st_size != len(raw):
                self._halt("HML_CONTINUITY_STORE_STAGE_UNSAFE")
            staged_path = os.stat(
                staged_name, dir_fd=directory_fd, follow_symlinks=False
            )
            if (
                self._signature(metadata) != self._signature(staged_path)
                or not has_no_extended_posix_acl(staged_fd, directory=False)
            ):
                self._halt("HML_CONTINUITY_STORE_STAGE_UNSAFE")
            os.replace(
                staged_name, _FILENAME,
                src_dir_fd=directory_fd, dst_dir_fd=directory_fd,
            )
            staged_name = None
            os.fsync(directory_fd)
            observed = self._read_locked(directory_fd, parent)
            if observed != record:
                self._halt("HML_CONTINUITY_STORE_WRITE_FAILED")
        except HMLContinuityStoreError:
            raise
        except (OSError, ValueError, TypeError, OverflowError):
            self._halt("HML_CONTINUITY_STORE_WRITE_FAILED")
        finally:
            if staged_fd >= 0:
                os.close(staged_fd)
            if staged_name is not None:
                try:
                    os.unlink(staged_name, dir_fd=directory_fd)
                except OSError:
                    pass

"""Volatile, fail-stop snapshot file session for ATLAS B HML source-only CI.

Consumes records already opened/checked by the FD-safe snapshot reader.
A repeated read of the SAME immutable inode is legitimate while TTL holds.
Recreated/replaced inodes require strictly newer, nonconflicting generations.
No persistent anti-replay, origin authentication, Docker, systemd, MCP or CLI.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from .atlas_hml_snapshot_candidate import (
    SnapshotContractError, SnapshotDiagnostic, review_untrusted_snapshot,
)
from .atlas_hml_snapshot_file_reader import HMLSnapshotFileRecord

_FAULTS = frozenset({
    "HML_SESSION_PRODUCER_FAILED", "HML_SESSION_PUBLISH_FAILED",
    "HML_SESSION_SNAPSHOT_UNAVAILABLE", "HML_SESSION_PROCESS_UNSAFE",
    "HML_SESSION_SHUTDOWN_REQUESTED",
})
_BLOCKS = (
    "SESSION_HISTORY_VOLATILE",
    "SNAPSHOT_ORIGIN_NOT_AUTHENTICATED",
    "ROOT_DOCKER_PRODUCER_HOST_EQUIVALENT",
    "ROLLBACK_AND_HOST_ISOLATION_NOT_ATTESTED",
    "SEC_01_TO_10_PENDING", "PREPARE_DISABLED", "ACT_DISABLED",
)
_MAX_GENERATIONS = 64


class HMLSnapshotSessionError(Exception):
    """Sanitized denial code only, never include snapshot or host metadata."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class HMLSnapshotSessionResult:
    diagnostic: SnapshotDiagnostic
    status: str = "blocked"
    fixture_continuity_ok: bool = False
    host_attested: bool = False
    producer_authenticated: bool = False
    replay_protection_persistent: bool = False
    prepare_eligible: bool = False
    can_execute: bool = False
    blocks: tuple[str, ...] = _BLOCKS


@dataclass(frozen=True, slots=True)
class _ObservedGeneration:
    dev: int
    inode: int
    mtime_ns: int
    ctime_ns: int
    digest: bytes
    observed_at: datetime
    container_id: str
    image_id: str
    wall_clock: datetime
    monotonic_ns: int


class HMLSnapshotFileSession:
    """In-memory fixture state machine. Failure latches; no automatic reset.

    Not thread-safe and intentionally not connected to an HTTP handler.
    Restarts reset history, so this is not operational anti-replay or attestation.
    """

    def __init__(self) -> None:
        self._last: _ObservedGeneration | None = None
        self._digests: list[bytes] = []
        self._fault: str | None = None

    def _stop(self, code: str) -> None:
        if self._fault is None:
            self._fault = code
        raise HMLSnapshotSessionError(self._fault)

    def observe(
        self, record: HMLSnapshotFileRecord, *,
        now: datetime, monotonic_ns: int,
    ) -> HMLSnapshotSessionResult:
        """Accept same file read; deny replay or change without fresh generation."""
        if self._fault is not None:
            raise HMLSnapshotSessionError(self._fault)
        if (
            type(record) is not HMLSnapshotFileRecord
            or type(record.raw) is not bytes
            or type(record.device) is not int or record.device < 0
            or type(record.inode) is not int or record.inode <= 0
            or type(record.mtime_ns) is not int or record.mtime_ns <= 0
            or type(record.ctime_ns) is not int or record.ctime_ns <= 0
            or type(now) is not datetime or now.tzinfo is None
            or now.utcoffset() is None
            or type(monotonic_ns) is not int or monotonic_ns < 0
        ):
            self._stop("HML_SESSION_INPUT_DENIED")
        try:
            check = review_untrusted_snapshot(record.raw, now=now)
            if (
                type(record.diagnostic) is not SnapshotDiagnostic
                or record.diagnostic != check
                or check.status != "blocked"
                or check.prepare_eligible or check.can_execute
            ):
                self._stop("HML_SESSION_RECORD_INCONSISTENT")
            observed_at = datetime.fromisoformat(
                check.observed_at_untrusted.replace("Z", "+00:00")
            )
        except SnapshotContractError:
            self._stop("HML_SESSION_SNAPSHOT_UNAVAILABLE")
        except (ValueError, TypeError, OverflowError):
            self._stop("HML_SESSION_RECORD_INCONSISTENT")
        new = _ObservedGeneration(
            dev=record.device, inode=record.inode,
            mtime_ns=record.mtime_ns, ctime_ns=record.ctime_ns,
            digest=hashlib.sha256(record.raw).digest(),
            observed_at=observed_at, container_id=check.container_id,
            image_id=check.image_id,
            wall_clock=now.astimezone(timezone.utc), monotonic_ns=monotonic_ns,
        )
        previous = self._last
        if previous is not None:
            if new.monotonic_ns <= previous.monotonic_ns:
                self._stop("HML_SESSION_MONOTONIC_REGRESSION")
            if new.wall_clock + timedelta(seconds=5) < previous.wall_clock:
                self._stop("HML_SESSION_CLOCK_REGRESSION")
            same_inode = (new.dev, new.inode) == (previous.dev, previous.inode)
            if same_inode:
                if (
                    new.digest != previous.digest
                    or new.mtime_ns != previous.mtime_ns
                    or new.ctime_ns != previous.ctime_ns
                    or new.observed_at != previous.observed_at
                ):
                    self._stop("HML_SESSION_INPLACE_MUTATION")
            else:
                if (
                    new.observed_at <= previous.observed_at
                    or new.digest in self._digests
                    or new.mtime_ns <= previous.mtime_ns
                ):
                    self._stop("HML_SESSION_REPLAY_OR_REGRESSION")
                if (
                    new.container_id != previous.container_id
                    or new.image_id != previous.image_id
                ):
                    self._stop("HML_SESSION_UNREVIEWED_IDENTITY_CHANGE")
                self._digests.append(new.digest)
                if len(self._digests) > _MAX_GENERATIONS:
                    self._digests.pop(0)
        else:
            self._digests.append(new.digest)
        self._last = new
        return HMLSnapshotSessionResult(diagnostic=check, fixture_continuity_ok=True)

    def mark_failure(self, code: str) -> None:
        """Latch an upstream/process/shutdown fault, never stop any real service."""
        if type(code) is not str or code not in _FAULTS:
            self._stop("HML_SESSION_FAULT_INVALID")
        self._stop(code)

    @property
    def halted(self) -> bool:
        return self._fault is not None

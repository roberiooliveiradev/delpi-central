"""Pure candidate for monotonic HML snapshot observation, not origin attestation.

This is an in-memory, caller-held state machine. It does not read/write
files, persist counters, operate Docker, or grant an authorization.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256

from .atlas_hml_snapshot_candidate import (
    SnapshotContractError, SnapshotDiagnostic, review_untrusted_snapshot,
)


class HMLSnapshotContinuityError(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class HMLSnapshotContinuityState:
    observed_at: datetime
    digest: str
    container_id: str
    image_id: str


@dataclass(frozen=True, slots=True)
class HMLSnapshotContinuityResult:
    diagnostic: SnapshotDiagnostic
    next_state: HMLSnapshotContinuityState
    status: str = "blocked"
    replay_attested: bool = False
    origin_attested: bool = False
    prepare_eligible: bool = False
    can_execute: bool = False


def review_snapshot_continuity(
    raw: bytes, *, now: datetime,
    previous: HMLSnapshotContinuityState | None = None,
) -> HMLSnapshotContinuityResult:
    """Return an uncommitted next state, or reject replay/conflict/regression.

    A caller MUST retain the previous state across invocations to obtain the
    stated guarantee; restart, replayed old state, root compromise, and wall
    clock rollback cannot be authenticated by this in-memory design.
    """
    if (type(now) is not datetime or now.tzinfo is None
            or now.utcoffset() is None
            or (previous is not None and type(previous)
                is not HMLSnapshotContinuityState)):
        raise HMLSnapshotContinuityError("HML_CONTINUITY_INPUT_INVALID")
    try:
        observation = review_untrusted_snapshot(raw, now=now)
    except SnapshotContractError as exc:
        raise HMLSnapshotContinuityError(exc.code) from None
    try:
        instant = datetime.fromisoformat(
            observation.observed_at_untrusted.replace("Z", "+00:00")
        ).astimezone(timezone.utc)
    except ValueError:
        raise HMLSnapshotContinuityError("HML_CONTINUITY_INPUT_INVALID") from None
    current = HMLSnapshotContinuityState(
        observed_at=instant,
        digest=sha256(raw).hexdigest(),
        container_id=observation.container_id,
        image_id=observation.image_id,
    )
    if previous is not None:
        if (type(previous.observed_at) is not datetime
                or previous.observed_at.tzinfo is None
                or previous.observed_at.utcoffset() is None
                or type(previous.digest) is not str
                or len(previous.digest) != 64
                or type(previous.container_id) is not str
                or type(previous.image_id) is not str):
            raise HMLSnapshotContinuityError("HML_CONTINUITY_STATE_UNTRUSTED")
        prior_time = previous.observed_at.astimezone(timezone.utc)
        if instant < prior_time:
            raise HMLSnapshotContinuityError("HML_CONTINUITY_TIME_REGRESSION")
        if instant == prior_time:
            if current.digest == previous.digest:
                raise HMLSnapshotContinuityError("HML_CONTINUITY_REPLAY")
            raise HMLSnapshotContinuityError("HML_CONTINUITY_GENERATION_CONFLICT")
        if (current.container_id != previous.container_id
                or current.image_id != previous.image_id):
            # The review candidate intentionally refuses deployments and
            # replacements until an external trusted generation is designed.
            raise HMLSnapshotContinuityError("HML_CONTINUITY_IDENTITY_CHANGED")
    return HMLSnapshotContinuityResult(observation, current)

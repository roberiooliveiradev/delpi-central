"""P2.2c: pure idempotent PREPARE journal decision, not persistent storage.

No approval, executor, SQL, or network. A future PostgreSQL UNIQUE constraint,
row lock and atomic event INSERT are mandatory before a real API may use this.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID

_SHA = re.compile(r"[0-9a-f]{40}\Z")
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_SERVICE = re.compile(r"[a-z][a-z0-9-]{1,63}\Z")
_MAX_TTL = timedelta(minutes=10)
_CLOCK_SKEW = timedelta(seconds=5)


@dataclass(frozen=True)
class PrepareRecord:
    request_id: str
    requester_subject: str
    environment: str
    service_id: str
    target_sha: str
    base_sha: str
    proposal_hash: str
    created_at: datetime
    expires_at: datetime
    status: str = "pending_approval"


@dataclass(frozen=True)
class PrepareDecision:
    state: str
    reason: str


def _uuid4(value: object) -> bool:
    if type(value) is not str:
        return False
    try:
        parsed = UUID(value)
    except (ValueError, AttributeError):
        return False
    return parsed.version == 4 and str(parsed) == value


def _utc(value: object) -> bool:
    return (isinstance(value, datetime) and value.tzinfo is not None
            and value.utcoffset() == timedelta(0))


def decide_prepare_insert(
    *, candidate: PrepareRecord, existing: PrepareRecord | None, now: datetime,
) -> PrepareDecision:
    """Classify one idempotency-key attempt, without mutating a journal.

    Backend must pass the only row selected under a DB transaction lock, never
    a caller-supplied 'existing'. No authorization is implied by CREATE.
    """
    if not _utc(now) or not isinstance(candidate, PrepareRecord):
        return PrepareDecision("blocked", "PREPARE_INPUT_INVALID")
    if (not _uuid4(candidate.request_id)
            or not _uuid4(candidate.requester_subject)
            or candidate.environment not in ("hml", "prod")
            or type(candidate.service_id) is not str or _SERVICE.fullmatch(candidate.service_id) is None
            or type(candidate.target_sha) is not str or _SHA.fullmatch(candidate.target_sha) is None
            or type(candidate.base_sha) is not str or _SHA.fullmatch(candidate.base_sha) is None
            or type(candidate.proposal_hash) is not str or _DIGEST.fullmatch(candidate.proposal_hash) is None
            or candidate.target_sha == candidate.base_sha
            or candidate.status != "pending_approval"
            or not _utc(candidate.created_at) or not _utc(candidate.expires_at)):
        return PrepareDecision("blocked", "PREPARE_INPUT_INVALID")
    if (candidate.created_at - now > _CLOCK_SKEW
            or candidate.expires_at <= now
            or candidate.expires_at <= candidate.created_at
            or candidate.expires_at - candidate.created_at > _MAX_TTL):
        return PrepareDecision("blocked", "PREPARE_EXPIRED_OR_INVALID_TTL")
    if existing is None:
        return PrepareDecision("create_candidate", "PREPARE_CAN_INSERT_WITH_DB_GUARDS")
    if not isinstance(existing, PrepareRecord):
        return PrepareDecision("blocked", "JOURNAL_ROW_INVALID")
    if existing.requester_subject != candidate.requester_subject or existing.request_id != candidate.request_id:
        return PrepareDecision("blocked", "JOURNAL_IDENTITY_MISMATCH")
    if existing != candidate:
        return PrepareDecision("conflict", "IDEMPOTENCY_PAYLOAD_MISMATCH")
    return PrepareDecision("replay_pending", "IDEMPOTENT_REPLAY_NO_NEW_WRITE")

"""ATLAS P2.2h.2p: independently read one journal challenge without mutation.

Private diagnostic only. No API route, MCP tool, role provisioning, nonce
issuance, reservation, PREPARE, approval or ACT. A fresh SELECT is never a
one-shot consume: callers MUST NOT treat this result as write permission.
Requires an explicitly supplied backend-managed SELECT-only connection.
The existing atlas_journal_reader role has NO challenge-table SELECT grant.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable
from uuid import UUID

_NONCE = re.compile(r"[0-9a-f]{64}\Z")
_MAX_TTL = timedelta(seconds=90)
_SKEW = timedelta(seconds=5)
_SQL_INSPECT = """SELECT issued_at, expires_at, consumed_at,
 clock_timestamp() AS observed_at
FROM it_portal.atlas_deploy_challenges
WHERE requester_subject = %s
  AND environment = %s
  AND service_id = %s
  AND challenge_digest = %s"""


class ChallengeInspectionError(Exception):
    """Finite codes, with no SQL, nonce, digest, subject or credential details."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class UnreservedChallengeSnapshot:
    """Verified-at-read only. May be consumed or expire immediately afterward."""

    environment: str
    service_id: str
    issued_at: datetime
    expires_at: datetime
    observed_at: datetime
    status: str = "observed_not_reserved"
    one_shot_consumed: bool = False
    prepare_eligible: bool = False


def _uuid4(value: object) -> bool:
    if type(value) is not str:
        return False
    try:
        parsed = UUID(value)
    except (ValueError, TypeError, AttributeError):
        return False
    return parsed.version == 4 and str(parsed) == value


def _aware(value: object) -> bool:
    return (
        type(value) is datetime
        and value.tzinfo is not None
        and value.utcoffset() is not None
    )


def _validate_scope(
    *, requester_subject: str, environment: str,
    service_id: str, nonce: str,
) -> str:
    # The requester_subject must be the authenticated human Core identity
    # from the trusted backend, never a user-selected query parameter.
    if (
        not _uuid4(requester_subject)
        or type(environment) is not str or environment not in ("prod", "hml")
        or service_id != "public-hub"
        or type(nonce) is not str or _NONCE.fullmatch(nonce) is None
    ):
        raise ChallengeInspectionError("CHALLENGE_INSPECTION_SCOPE_INVALID")
    return hashlib.sha256(bytes.fromhex(nonce)).hexdigest()


def inspect_active_challenge(
    conn: Any, *, requester_subject: str,
    environment: str, service_id: str, nonce: str,
) -> UnreservedChallengeSnapshot:
    """Use READ ONLY SQL + PostgreSQL clock, not a mutable Python timestamp.

    This is an ephemeral view, *not* a reservation. Run again after all
    slow OCI verification work; only a future atomic UPDATE/INSERT is
    allowed to consume the challenge.
    """
    digest = _validate_scope(
        requester_subject=requester_subject, environment=environment,
        service_id=service_id, nonce=nonce,
    )
    try:
        with conn.transaction():
            conn.execute("SET TRANSACTION ISOLATION LEVEL READ COMMITTED READ ONLY")
            row = conn.execute(
                _SQL_INSPECT,
                (requester_subject, environment, service_id, digest),
            ).fetchone()
    except Exception:
        raise ChallengeInspectionError("CHALLENGE_INSPECTION_DB_UNAVAILABLE") from None

    if row is None:
        # One identical code for unknown nonce, wrong requester/target, and
        # consumed/expired challenges: callers cannot use this to enumerate.
        raise ChallengeInspectionError("CHALLENGE_INSPECTION_UNAVAILABLE")
    if type(row) not in (tuple, list) or len(row) != 4:
        raise ChallengeInspectionError("CHALLENGE_INSPECTION_ROW_INVALID")
    issued_at, expires_at, consumed_at, observed_at = row
    if (
        not _aware(issued_at)
        or not _aware(expires_at)
        or not _aware(observed_at)
        or (consumed_at is not None and not _aware(consumed_at))
    ):
        raise ChallengeInspectionError("CHALLENGE_INSPECTION_ROW_INVALID")
    if (
        expires_at <= issued_at
        or expires_at - issued_at > _MAX_TTL
        or issued_at > observed_at + _SKEW
    ):
        raise ChallengeInspectionError("CHALLENGE_INSPECTION_ROW_INVALID")
    if consumed_at is not None or observed_at >= expires_at:
        raise ChallengeInspectionError("CHALLENGE_INSPECTION_UNAVAILABLE")
    return UnreservedChallengeSnapshot(
        environment=environment,
        service_id=service_id,
        issued_at=issued_at.astimezone(timezone.utc),
        expires_at=expires_at.astimezone(timezone.utc),
        observed_at=observed_at.astimezone(timezone.utc),
    )


class ExplicitChallengeReadOnlyReader:
    """Disabled unless trusted backend explicitly configures its own connection.

    Do not reuse the current ATLAS journal UI role: it deliberately cannot
    SELECT challenges. Never expose a DSN, connection factory or nonce
    through MCP, browser input, logs or responses.
    """

    def __init__(
        self, *,
        connect: Callable[[], Any],
        enabled: Callable[[], bool] = lambda: False,
    ):
        self._connect = connect
        self._enabled = enabled

    def read(
        self, *, requester_subject: str,
        environment: str, service_id: str, nonce: str,
    ) -> UnreservedChallengeSnapshot:
        # Validate before connection so malformed client-derived input
        # never triggers database work, even in future trusted composition.
        _validate_scope(
            requester_subject=requester_subject, environment=environment,
            service_id=service_id, nonce=nonce,
        )
        try:
            enabled = self._enabled()
        except Exception:
            raise ChallengeInspectionError("CHALLENGE_INSPECTION_DISABLED") from None
        if enabled is not True:
            raise ChallengeInspectionError("CHALLENGE_INSPECTION_DISABLED")
        try:
            conn = self._connect()
        except Exception:
            raise ChallengeInspectionError("CHALLENGE_INSPECTION_DB_UNAVAILABLE") from None
        try:
            return inspect_active_challenge(
                conn, requester_subject=requester_subject,
                environment=environment, service_id=service_id, nonce=nonce,
            )
        finally:
            try:
                conn.close()
            except Exception:
                pass

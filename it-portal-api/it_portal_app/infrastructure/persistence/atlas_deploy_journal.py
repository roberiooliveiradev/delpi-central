"""P2.2d: inert PostgreSQL journal access for deployment PREPARE and one-shot nonce.

NOT registered as an API route or wired to any service. A privileged backend
must independently authorize Core permissions and attest CI/host/rollback
before calling; this repository cannot grant those permissions. SQL schema is
only proposed in docs, NOT an auto-applied migration.

The transaction boundary and unique constraints are required for correctness;
never replace the storage with a per-process dict in production.
"""
from __future__ import annotations

import hashlib
import re
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID, uuid4

_SHA = re.compile(r"[0-9a-f]{40}\Z")
_HASH = re.compile(r"[0-9a-f]{64}\Z")
_SERVICE = re.compile(r"[a-z][a-z0-9-]{1,63}\Z")

# Static, parametrized SQL; never interpolate caller fields into SQL text.
_SQL_TIME = "SELECT clock_timestamp()"
_SQL_CHALLENGE = """INSERT INTO it_portal.atlas_deploy_challenges
(id, requester_subject, environment, service_id, challenge_digest, issued_at, expires_at)
VALUES (%s,%s,%s,%s,%s,%s,%s)"""
_SQL_CREATE = """INSERT INTO it_portal.atlas_deploy_proposals
(id, requester_subject, request_id, environment, service_id, target_sha,
 base_sha, proposal_hash, challenge_digest, created_at, expires_at, status)
VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'pending_approval')
ON CONFLICT (requester_subject, request_id) DO NOTHING RETURNING id"""
_SQL_CONSUME = """UPDATE it_portal.atlas_deploy_challenges
SET consumed_at = clock_timestamp()
WHERE requester_subject = %s AND environment = %s AND service_id = %s
  AND challenge_digest = %s AND consumed_at IS NULL
  AND expires_at > clock_timestamp()
RETURNING id"""
_SQL_EVENT = """INSERT INTO it_portal.atlas_deploy_events
(id, proposal_id, event_seq, event_type, actor_subject, occurred_at)
VALUES (%s,%s,1,'prepared',%s,clock_timestamp())"""
_SQL_READ = """SELECT id, requester_subject, request_id, environment, service_id,
 target_sha, base_sha, proposal_hash, challenge_digest, expires_at, status
FROM it_portal.atlas_deploy_proposals
WHERE requester_subject = %s AND request_id = %s FOR UPDATE"""


class JournalRejected(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class PrepareIntent:
    requester_subject: str
    request_id: str
    environment: str
    service_id: str
    target_sha: str
    base_sha: str
    proposal_hash: str


@dataclass(frozen=True)
class PrepareStored:
    proposal_id: str
    result: str


def _uuid4(x: object) -> bool:
    if type(x) is not str:
        return False
    try:
        u = UUID(x)
    except (ValueError, AttributeError):
        return False
    return u.version == 4 and str(u) == x


def _validate_intent(intent: PrepareIntent) -> None:
    if (not isinstance(intent, PrepareIntent) or not _uuid4(intent.requester_subject)
            or not _uuid4(intent.request_id)
            or type(intent.environment) is not str or intent.environment not in ('hml','prod')
            or type(intent.service_id) is not str or _SERVICE.fullmatch(intent.service_id) is None
            or type(intent.target_sha) is not str or _SHA.fullmatch(intent.target_sha) is None
            or type(intent.base_sha) is not str or _SHA.fullmatch(intent.base_sha) is None
            or intent.target_sha == intent.base_sha
            or type(intent.proposal_hash) is not str or _HASH.fullmatch(intent.proposal_hash) is None):
        raise JournalRejected('PREPARE_INVALID')


def _nonce_digest(nonce: object) -> str:
    if type(nonce) is not str or _HASH.fullmatch(nonce) is None:
        raise JournalRejected('CHALLENGE_INVALID')
    return hashlib.sha256(bytes.fromhex(nonce)).hexdigest()


def _db_now(conn: Any) -> datetime:
    row = conn.execute(_SQL_TIME).fetchone()
    if row is None or len(row) != 1 or not isinstance(row[0], datetime):
        raise JournalRejected('DATABASE_CLOCK_UNAVAILABLE')
    value = row[0]
    if value.tzinfo is None or value.utcoffset() is None:
        raise JournalRejected('DATABASE_CLOCK_UNAVAILABLE')
    return value.astimezone(timezone.utc)


def issue_challenge(conn: Any, *, requester_subject: str,
                    environment: str, service_id: str) -> str:
    """Register one random challenge for 90 seconds, in one DB transaction.

    Identity/environment/service MUST come from authenticated backend policy.
    The returned 64-hex challenge must not be put in logs, URLs or the model.
    """
    probe = PrepareIntent(requester_subject, str(uuid4()), environment, service_id,
                          'a'*40, 'b'*40, 'c'*64)
    _validate_intent(probe)
    nonce = secrets.token_hex(32)
    digest = _nonce_digest(nonce)
    try:
        with conn.transaction():
            now = _db_now(conn)
            conn.execute(_SQL_CHALLENGE, (str(uuid4()), requester_subject, environment,
                                          service_id, digest, now, now+timedelta(seconds=90)))
    except JournalRejected:
        raise
    except Exception:
        raise JournalRejected('JOURNAL_DATABASE_UNAVAILABLE') from None
    return nonce


def store_prepared(conn: Any, *, intent: PrepareIntent, signed_receipt_challenge: str) -> PrepareStored:
    """Create once or replay identically. Consume challenge atomically on CREATE.

    This is NOT an endpoint, approval or deploy; caller MUST complete trusted
    Core+GitHub+HostProof+policy checks before invocation.
    """
    _validate_intent(intent)
    digest = _nonce_digest(signed_receipt_challenge)
    try:
        with conn.transaction():
            now = _db_now(conn)
            created = conn.execute(_SQL_CREATE, (
                str(uuid4()), intent.requester_subject, intent.request_id,
                intent.environment, intent.service_id, intent.target_sha, intent.base_sha,
                intent.proposal_hash, digest, now, now+timedelta(minutes=10),
            )).fetchone()
            if created is not None:
                # If nonce is missing/expired/consumed, roll back the insertion.
                if conn.execute(_SQL_CONSUME, (
                    intent.requester_subject, intent.environment, intent.service_id,
                    digest,
                )).fetchone() is None:
                    raise JournalRejected('CHALLENGE_MISSING_OR_CONSUMED')
                proposal_id = str(created[0])
                conn.execute(_SQL_EVENT, (str(uuid4()), proposal_id, intent.requester_subject))
                return PrepareStored(proposal_id, 'created_pending_approval')
            existing = conn.execute(_SQL_READ, (intent.requester_subject, intent.request_id)).fetchone()
            if existing is None or len(existing) != 11:
                raise JournalRejected('JOURNAL_ROW_INCONSISTENT')
            (proposal_id, subject, request_id, env, service, sha, base, digest_saved,
             challenge_saved, expires_at, status) = existing
            if (str(subject) != intent.requester_subject or str(request_id) != intent.request_id
                    or env != intent.environment or service != intent.service_id
                    or sha != intent.target_sha or base != intent.base_sha
                    or digest_saved != intent.proposal_hash or challenge_saved != digest):
                raise JournalRejected('IDEMPOTENCY_PAYLOAD_CONFLICT')
            if not isinstance(expires_at, datetime) or expires_at <= now or status != 'pending_approval':
                raise JournalRejected('IDEMPOTENCY_ALREADY_CLOSED')
            # A retry must not consume another nonce or insert another event.
            return PrepareStored(str(proposal_id), 'replay_pending_approval')
    except JournalRejected:
        raise
    except Exception:
        raise JournalRejected('JOURNAL_DATABASE_UNAVAILABLE') from None

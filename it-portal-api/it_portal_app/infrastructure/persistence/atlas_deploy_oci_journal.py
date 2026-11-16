"""P2.2h.2b: inert atomic OCI binding + journal PREPARE candidate.

This module is deliberately NOT registered as a route, migration, approval or
deployment executor. It accepts evidence only from a future trusted backend
that independently authenticated Core, Sigstore and a challenged host reader.
Passing backend_policy_enabled=True or constructing dataclasses is NOT proof.
No callers are added in this increment. Never use from an MCP tool directly.
"""
from __future__ import annotations

import hmac
from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

from .atlas_deploy_journal import (
    JournalRejected,
    PrepareIntent,
    PrepareStored,
    _db_now,
    _nonce_digest,
    _validate_intent,
    _SQL_CONSUME,
    _SQL_EVENT,
    _SQL_LOCK,
    _SQL_READ,
)
from .atlas_deploy_oci_seal import (
    CIReleaseEvidence,
    HostRuntimeEvidence,
    OCIGateRejected,
    OCIProposalIntent,
    SealedOCICandidate,
    _fresh,
    _time,
    seal_oci_candidate,
)

# SQL is static/parameterized. Only the disposable candidate schema currently
# defines atlas_deploy_oci_bindings; production lacks it by design.
_SQL_CREATE_OCI = """INSERT INTO it_portal.atlas_deploy_proposals
(id, requester_subject, request_id, environment, service_id, target_sha,
 base_sha, proposal_hash, challenge_digest, created_at, expires_at, status)
VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'pending_approval')
ON CONFLICT (requester_subject, request_id) DO NOTHING RETURNING id"""

_SQL_BINDING_INSERT = """INSERT INTO it_portal.atlas_deploy_oci_bindings
(proposal_id, requester_subject, request_id, environment, service_id,
 target_sha, base_sha, signed_manifest_digest, release_image_id, base_image_id,
 rollback_image_id, ci_statement_sha256, host_challenge_sha256, preview_hash,
 sealed_binding_sha256, issued_at, expires_at)
VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""

_SQL_BINDING_READ = """SELECT requester_subject, request_id, environment, service_id,
 target_sha, base_sha, signed_manifest_digest, release_image_id, base_image_id,
 rollback_image_id, ci_statement_sha256, host_challenge_sha256, preview_hash,
 sealed_binding_sha256, issued_at, expires_at
FROM it_portal.atlas_deploy_oci_bindings
WHERE proposal_id = %s FOR UPDATE"""


def _expected_binding(intent: OCIProposalIntent,
                      candidate: SealedOCICandidate) -> tuple[object, ...]:
    return (
        intent.requester_subject, intent.request_id, intent.environment,
        intent.service_id, intent.target_commit_sha, intent.base_commit_sha,
        intent.manifest_digest, intent.target_image_id, intent.base_image_id,
        intent.rollback_image_id, intent.attestation_statement_sha256,
        intent.host_challenge_sha256, intent.preview_hash,
        candidate.binding_sha256, candidate.issued_at, candidate.expires_at,
    )


def _binding_equals(actual: object, expected: tuple[object, ...]) -> bool:
    if not isinstance(actual, (tuple, list)) or len(actual) != len(expected):
        return False
    for index, (value, wanted) in enumerate(zip(actual, expected)):
        if isinstance(wanted, datetime):
            if not _time(value) or value != wanted:
                return False
        elif index == 13:
            if type(value) is not str or not hmac.compare_digest(value, wanted):
                return False
        elif str(value) != wanted:
            # UUID from psycopg and UUID stored as canonical string are
            # interchangeable; other field types are textual by schema.
            return False
    return True


def _verify_at_db_clock(*, intent: OCIProposalIntent,
                        candidate: SealedOCICandidate,
                        ci: CIReleaseEvidence, host: HostRuntimeEvidence,
                        now: datetime) -> None:
    if not (isinstance(intent, OCIProposalIntent)
            and isinstance(candidate, SealedOCICandidate)
            and isinstance(ci, CIReleaseEvidence)
            and isinstance(host, HostRuntimeEvidence)):
        raise JournalRejected("OCI_CONTRACT_INVALID")
    if (candidate.status != "candidate_only" or candidate.version != 1
            or candidate.requester_subject != intent.requester_subject
            or candidate.environment != intent.environment
            or candidate.service_id != intent.service_id
            or not _time(candidate.issued_at) or not _time(candidate.expires_at)):
        raise JournalRejected("OCI_CANDIDATE_INVALID")
    if (candidate.issued_at > now + timedelta(seconds=5)
            or now >= candidate.expires_at
            or candidate.expires_at != candidate.issued_at + timedelta(minutes=10)):
        raise JournalRejected("OCI_CANDIDATE_EXPIRED")
    if not (_time(ci.verified_at) and _fresh(ci.verified_at, now)
            and _time(host.observed_at) and _fresh(host.observed_at, now)):
        raise JournalRejected("OCI_EVIDENCE_STALE")
    try:
        independently_recomputed = seal_oci_candidate(
            intent=intent, ci=ci, host=host, now=candidate.issued_at,
            backend_policy_enabled=True,
        )
    except OCIGateRejected as exc:
        raise JournalRejected(exc.code) from None
    if independently_recomputed != candidate:
        raise JournalRejected("OCI_BINDING_DRIFT")


def store_oci_prepared(
    conn: Any, *,
    intent: OCIProposalIntent,
    candidate: SealedOCICandidate,
    ci: CIReleaseEvidence,
    host: HostRuntimeEvidence,
    signed_receipt_challenge: str,
    backend_policy_enabled: bool = False,
) -> PrepareStored:
    """Persist one pending OCI binding, generic proposal and event atomically.

    Never approves or executes a deployment. Evidence MUST originate in a
    trusted backend, not in an MCP/user request. Fail-closed is the default.
    The existing generic journal is intentionally not modified.
    """
    if type(backend_policy_enabled) is not bool or not backend_policy_enabled:
        raise JournalRejected("OCI_POLICY_DISABLED")
    if not isinstance(intent, OCIProposalIntent) or not isinstance(candidate, SealedOCICandidate):
        raise JournalRejected("OCI_CONTRACT_INVALID")
    generic = PrepareIntent(
        requester_subject=intent.requester_subject, request_id=intent.request_id,
        environment=intent.environment, service_id=intent.service_id,
        target_sha=intent.target_commit_sha, base_sha=intent.base_commit_sha,
        proposal_hash=candidate.binding_sha256,
    )
    _validate_intent(generic)
    if generic.service_id != "public-hub":
        raise JournalRejected("OCI_TARGET_INVALID")
    digest = _nonce_digest(signed_receipt_challenge)

    try:
        with conn.transaction():
            # The lock and the UNIQUE(requester_subject, request_id) together
            # serialize identical requests from distinct backend instances.
            key = f"{generic.requester_subject}:{generic.request_id}"
            conn.execute(_SQL_LOCK, (key,)).fetchone()
            now = _db_now(conn)
            _verify_at_db_clock(
                intent=intent, candidate=candidate, ci=ci, host=host, now=now,
            )
            expected = _expected_binding(intent, candidate)
            existing = conn.execute(
                _SQL_READ, (generic.requester_subject, generic.request_id),
            ).fetchone()
            if existing is not None:
                if len(existing) != 11:
                    raise JournalRejected("JOURNAL_ROW_INCONSISTENT")
                (proposal_id, requester, request_id, env, service, target, base,
                 proposal_hash, old_digest, expires_at, status) = existing
                if (
                    str(requester) != generic.requester_subject
                    or str(request_id) != generic.request_id
                    or env != generic.environment
                    or service != generic.service_id
                    or target != generic.target_sha
                    or base != generic.base_sha
                    or old_digest != digest
                    or not hmac.compare_digest(str(proposal_hash), candidate.binding_sha256)
                    or expires_at != candidate.expires_at
                ):
                    raise JournalRejected("IDEMPOTENCY_PAYLOAD_CONFLICT")
                row = conn.execute(
                    _SQL_BINDING_READ, (str(proposal_id),),
                ).fetchone()
                if row is None:
                    raise JournalRejected("OCI_BINDING_MISSING")
                if not _binding_equals(row, expected):
                    raise JournalRejected("IDEMPOTENCY_PAYLOAD_CONFLICT")
                if status != "pending_approval" or expires_at <= now:
                    raise JournalRejected("IDEMPOTENCY_ALREADY_CLOSED")
                return PrepareStored(str(proposal_id), "replay_pending_approval")

            # Any failure below rolls the nonce consumption and both INSERTs
            # back in the same PostgreSQL transaction, including trigger errors.
            consumed = conn.execute(
                _SQL_CONSUME,
                (generic.requester_subject, generic.environment,
                 generic.service_id, digest),
            ).fetchone()
            if consumed is None:
                raise JournalRejected("CHALLENGE_MISSING_OR_CONSUMED")
            proposal = conn.execute(
                _SQL_CREATE_OCI,
                (str(uuid4()), generic.requester_subject, generic.request_id,
                 generic.environment, generic.service_id, generic.target_sha,
                 generic.base_sha, candidate.binding_sha256, digest,
                 candidate.issued_at, candidate.expires_at),
            ).fetchone()
            if proposal is None:
                raise JournalRejected("JOURNAL_CONCURRENT_WRITE")
            proposal_id = str(proposal[0])
            conn.execute(_SQL_BINDING_INSERT, (proposal_id, *expected))
            conn.execute(
                _SQL_EVENT, (str(uuid4()), proposal_id, generic.requester_subject),
            )
            return PrepareStored(proposal_id, "created_pending_approval")
    except JournalRejected:
        raise
    except Exception:
        # Never leak SQL, credentials, DSNs or evidence values to an MCP/UI.
        raise JournalRejected("OCI_JOURNAL_DATABASE_UNAVAILABLE") from None

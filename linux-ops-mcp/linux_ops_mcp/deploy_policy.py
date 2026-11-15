"""P2.1: pure, deny-by-default deployment *preview* policy.

No I/O, shell, Docker, SSH, Git, HTTP, database, or MCP exposure.
Evidence MUST come from trusted backend attestations, NEVER tool arguments.
An eligible preview is NOT a deploy approval, authorization, or command.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID

_SHA = re.compile(r"[0-9a-f]{40}\Z")
_SERVICE = re.compile(r"[a-z][a-z0-9-]{1,63}\Z")
_SUBJECT = re.compile(r"[A-Za-z0-9._:@-]{3,128}\Z")
_EVIDENCE_MAX_AGE = timedelta(seconds=120)
_FUTURE_SKEW = timedelta(seconds=5)
_PROPOSAL_TTL = timedelta(minutes=10)


@dataclass(frozen=True)
class DeploymentTarget:
    service_id: str
    environment: str
    enabled: bool = False
    requires_rollback: bool = True


@dataclass(frozen=True)
class DeploymentPolicy:
    enabled: bool = False
    allow_prod: bool = False
    targets: tuple[DeploymentTarget, ...] = ()


@dataclass(frozen=True)
class TrustedDeployEvidence:
    """Only backend-created evidence. Untrusted MCP arguments must never fill this."""

    approved_commit_sha: str | None = None
    deployed_commit_sha: str | None = None
    ci_passed: bool = False
    approved_ref_contains_commit: bool = False
    checkout_clean: bool = False
    health_passed: bool = False
    migrations_safe: bool = False
    rollback_ready: bool = False
    checked_at: datetime | None = None


@dataclass(frozen=True)
class DeploymentPreview:
    status: str
    blocks: tuple[str, ...]
    proposal_hash: str | None = None
    expires_at: str | None = None


def _valid_sha(value: object) -> bool:
    return type(value) is str and _SHA.fullmatch(value) is not None


def _utc_aware(value: object) -> bool:
    return isinstance(value, datetime) and value.tzinfo is not None and value.utcoffset() is not None


def _uuid4(value: object) -> bool:
    if type(value) is not str:
        return False
    try:
        parsed = UUID(value)
    except (ValueError, AttributeError):
        return False
    return parsed.version == 4 and str(parsed) == value


def evaluate_deployment_preview(
    *,
    policy: DeploymentPolicy,
    environment: str,
    service_id: str,
    commit_sha: str,
    requester_subject: str,
    request_id: str,
    evidence: TrustedDeployEvidence,
    now: datetime,
) -> DeploymentPreview:
    """Build a non-executable, sealed candidate or deny with safe reason codes.

    Backend must separately attest evidence, authorize PREPARE, persist the
    proposal, bind idempotency atomically and obtain human approval before ACT.
    This function alone cannot authorize or execute any operation.
    """
    blocks: list[str] = []
    if not isinstance(policy, DeploymentPolicy) or type(policy.enabled) is not bool or not policy.enabled:
        blocks.append("POLICY_DISABLED")
    if environment not in ("hml", "prod") or type(environment) is not str:
        blocks.append("ENVIRONMENT_INVALID")
    if type(service_id) is not str or _SERVICE.fullmatch(service_id) is None:
        blocks.append("SERVICE_INVALID")
    if not _valid_sha(commit_sha):
        blocks.append("COMMIT_SHA_INVALID")
    if type(requester_subject) is not str or _SUBJECT.fullmatch(requester_subject) is None:
        blocks.append("REQUESTER_INVALID")
    if not _uuid4(request_id):
        blocks.append("REQUEST_ID_INVALID")
    if not _utc_aware(now):
        blocks.append("CLOCK_INVALID")

    matches = []
    if isinstance(policy, DeploymentPolicy) and type(service_id) is str and type(environment) is str:
        matches = [
            target for target in policy.targets
            if isinstance(target, DeploymentTarget)
            and target.service_id == service_id
            and target.environment == environment
            and type(target.enabled) is bool
            and target.enabled
        ]
    if len(matches) != 1:
        blocks.append("TARGET_NOT_ALLOWLISTED")
    if environment == "prod" and (
        not isinstance(policy, DeploymentPolicy)
        or type(policy.allow_prod) is not bool
        or not policy.allow_prod
    ):
        blocks.append("PRODUCTION_LOCKED")

    if not isinstance(evidence, TrustedDeployEvidence):
        blocks.append("ATTESTATION_MISSING")
    else:
        if not (_utc_aware(evidence.checked_at) and _utc_aware(now)):
            blocks.append("ATTESTATION_STALE")
        else:
            age = now.astimezone(timezone.utc) - evidence.checked_at.astimezone(timezone.utc)
            if age > _EVIDENCE_MAX_AGE or age < -_FUTURE_SKEW:
                blocks.append("ATTESTATION_STALE")
        if type(evidence.ci_passed) is not bool or not evidence.ci_passed:
            blocks.append("CI_NOT_PASSED")
        if (
            type(evidence.approved_ref_contains_commit) is not bool
            or not evidence.approved_ref_contains_commit
            or not _valid_sha(evidence.approved_commit_sha)
            or evidence.approved_commit_sha != commit_sha
        ):
            blocks.append("COMMIT_NOT_APPROVED")
        if type(evidence.checkout_clean) is not bool or not evidence.checkout_clean:
            blocks.append("CHECKOUT_NOT_CLEAN")
        if not _valid_sha(evidence.deployed_commit_sha):
            blocks.append("DEPLOYED_REVISION_UNVERIFIED")
        elif evidence.deployed_commit_sha == commit_sha:
            blocks.append("ALREADY_DEPLOYED")
        if type(evidence.health_passed) is not bool or not evidence.health_passed:
            blocks.append("HEALTH_NOT_PASSED")
        if type(evidence.migrations_safe) is not bool or not evidence.migrations_safe:
            blocks.append("MIGRATION_UNSAFE")
        if matches and matches[0].requires_rollback and (
            type(evidence.rollback_ready) is not bool or not evidence.rollback_ready
        ):
            blocks.append("ROLLBACK_NOT_READY")

    if blocks:
        return DeploymentPreview(status="blocked", blocks=tuple(dict.fromkeys(blocks)))

    # Only trusted, fixed-shape fields. No freeform script, path or environment.
    issued = now.astimezone(timezone.utc)
    expires = issued + _PROPOSAL_TTL
    payload = {
        "version": 1,
        "environment": environment,
        "service_id": service_id,
        "commit_sha": commit_sha,
        "deployed_commit_sha": evidence.deployed_commit_sha,
        "requester_subject": requester_subject,
        "request_id": request_id,
        "issued_at": issued.isoformat(),
        "expires_at": expires.isoformat(),
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    return DeploymentPreview(status="eligible_for_preparation", blocks=(), proposal_hash=digest, expires_at=expires.isoformat())

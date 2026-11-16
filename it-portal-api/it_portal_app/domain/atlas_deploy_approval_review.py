"""ATLAS P2.2h.2c: inert Core/RBAC approval-review precondition contract.

NOT a Core grant, HTTP route, sign-off, or ACT ticket. Caller objects and flags
are not authentication. Only a future trusted Portal TI backend may build
inputs from fresh Core RBAC + immutable journal and CI/host evidence.
No database, Docker, CLI, network or external communication occurs.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID

ACCESS = "it-portal.access"
REVIEW_VIEW = "it-portal.deploy.view"
REVIEW_APPROVE = "it-portal.deploy.approve"

_SHA = re.compile(r"[0-9a-f]{40}\Z")
_DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")
_HASH = re.compile(r"[0-9a-f]{64}\Z")
_PERMISSION_TTL = timedelta(seconds=60)
_SKEW = timedelta(seconds=5)
_MAX_PROPOSAL_TTL = timedelta(minutes=10)


class ApprovalReviewRejected(Exception):
    """Finite public denial code, never carries PII, token or SQL details."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class CoreReviewerSnapshot:
    """Must originate in authenticated Core RBAC, not browser permissions."""

    subject: str
    principal_type: str
    permissions: tuple[str, ...]
    fetched_at: datetime
    core_available: bool
    active: bool


@dataclass(frozen=True, slots=True)
class PendingDeployReview:
    """Must originate from immutable, transactionally checked journal rows."""

    proposal_id: str
    requester_subject: str
    service_id: str
    environment: str
    status: str
    target_commit_sha: str
    signed_manifest_digest: str
    base_image_id: str
    target_image_id: str
    binding_sha256: str
    created_at: datetime
    expires_at: datetime
    revoked: bool
    approved_by: str | None


@dataclass(frozen=True, slots=True)
class ReadOnlyReviewResult:
    state: str
    proposal_id: str
    binding_sha256: str
    approval_enabled: bool = False
    execution_enabled: bool = False
    manual_deploy_blocked: bool = False


def _uuid4(value: object) -> bool:
    if type(value) is not str:
        return False
    try:
        result = UUID(value)
    except (TypeError, ValueError, AttributeError):
        return False
    return result.version == 4 and str(result) == value


def _aware(value: object) -> bool:
    return type(value) is datetime and value.tzinfo is not None and value.utcoffset() is not None


def _age_is_fresh(*, observed: datetime, now: datetime) -> bool:
    elapsed = now.astimezone(timezone.utc) - observed.astimezone(timezone.utc)
    return -_SKEW <= elapsed <= _PERMISSION_TTL


def prepare_readonly_review(
    *, actor: CoreReviewerSnapshot, proposal: PendingDeployReview,
    now: datetime, backend_policy_enabled: bool = False,
) -> ReadOnlyReviewResult:
    """Return only a view-ready candidate, NEVER grant approval or execution.

    backend_policy_enabled is an offline test gate, not a security authority.
    A real backend must authenticate the user, query Core fresh, check journal,
    image signature and host independently before calling.
    """
    if type(backend_policy_enabled) is not bool or not backend_policy_enabled:
        raise ApprovalReviewRejected("ATLAS_APPROVAL_DISABLED")
    if (not isinstance(actor, CoreReviewerSnapshot)
            or not isinstance(proposal, PendingDeployReview)
            or not _aware(now)):
        raise ApprovalReviewRejected("ATLAS_REVIEW_INVALID")
    if (actor.principal_type != "user"
            or type(actor.active) is not bool or not actor.active
            or type(actor.core_available) is not bool or not actor.core_available
            or not _uuid4(actor.subject)):
        raise ApprovalReviewRejected("ATLAS_CORE_IDENTITY_DENIED")
    if not _aware(actor.fetched_at) or not _age_is_fresh(observed=actor.fetched_at, now=now):
        raise ApprovalReviewRejected("ATLAS_CORE_STALE")
    if (type(actor.permissions) is not tuple
            or not all(type(p) is str for p in actor.permissions)
            or not {ACCESS, REVIEW_VIEW, REVIEW_APPROVE}.issubset(set(actor.permissions))):
        raise ApprovalReviewRejected("ATLAS_CORE_PERMISSION_DENIED")
    if not (_uuid4(proposal.proposal_id) and _uuid4(proposal.requester_subject)):
        raise ApprovalReviewRejected("ATLAS_PROPOSAL_ID_INVALID")
    # Single-operator IT: the requester may explicitly review their own proposal.
    # Authorization still requires fresh, separately granted Core permissions.
    if proposal.service_id != "public-hub" or proposal.environment not in ("hml", "prod"):
        raise ApprovalReviewRejected("ATLAS_REVIEW_TARGET_DENIED")
    if (type(proposal.target_commit_sha) is not str
            or _SHA.fullmatch(proposal.target_commit_sha) is None
            or type(proposal.signed_manifest_digest) is not str
            or _DIGEST.fullmatch(proposal.signed_manifest_digest) is None
            or type(proposal.base_image_id) is not str
            or _DIGEST.fullmatch(proposal.base_image_id) is None
            or type(proposal.target_image_id) is not str
            or _DIGEST.fullmatch(proposal.target_image_id) is None
            or proposal.base_image_id == proposal.target_image_id
            or type(proposal.binding_sha256) is not str
            or _HASH.fullmatch(proposal.binding_sha256) is None):
        raise ApprovalReviewRejected("ATLAS_REVIEW_BINDING_INVALID")
    if (proposal.status != "pending_approval"
            or type(proposal.revoked) is not bool or proposal.revoked
            or proposal.approved_by is not None):
        raise ApprovalReviewRejected("ATLAS_REVIEW_NOT_PENDING")
    if not (_aware(proposal.created_at) and _aware(proposal.expires_at)):
        raise ApprovalReviewRejected("ATLAS_REVIEW_TIME_INVALID")
    if (proposal.expires_at <= proposal.created_at
            or proposal.expires_at - proposal.created_at > _MAX_PROPOSAL_TTL
            or now >= proposal.expires_at
            or proposal.created_at > now + _SKEW):
        raise ApprovalReviewRejected("ATLAS_REVIEW_EXPIRED")
    return ReadOnlyReviewResult(
        state="review_candidate_only",
        proposal_id=proposal.proposal_id,
        binding_sha256=proposal.binding_sha256,
    )

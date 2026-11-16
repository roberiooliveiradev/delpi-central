"""ATLAS P2.2h.2a: pure OCI release proposal/approval binding. INERT.

Not an endpoint, credential, signer, approval service, database migration, or
executor. Inputs labelled as verified MUST be constructed by backend readers,
never from MCP/user arguments. These shapes alone cannot establish authenticity.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID

REPOSITORY = "roberiooliveiradev/delpi-central"
IMAGE = "ghcr.io/roberiooliveiradev/delpi-public-hub"
WORKFLOW = f"{REPOSITORY}/.github/workflows/atlas-public-hub-oci.yml"
SOURCE_REF = "refs/heads/main"
CONTAINER = {"prod": ("delpi-public-hub", "infra"), "hml": ("delpi-hml-public-hub", "delpi-hml")}
_SHA = re.compile(r"[0-9a-f]{40}\Z")
_DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")
_HEX64 = re.compile(r"[0-9a-f]{64}\Z")
_AGE = timedelta(seconds=120)
_SKEW = timedelta(seconds=5)
_TTL = timedelta(minutes=10)


class OCIGateRejected(Exception):
    """Public, finite error code only, never include raw evidence or secrets."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class CIReleaseEvidence:
    """Identity from an independently verified SLSA/Sigstore attestation reader."""

    repository: str
    image: str
    workflow: str
    source_ref: str
    commit_sha: str
    manifest_digest: str
    image_config_id: str
    statement_sha256: str
    verified_at: datetime
    signature_verified: bool


@dataclass(frozen=True, slots=True)
class HostRuntimeEvidence:
    """Fresh challenge-bound host snapshot, not stdout of a shell command."""

    environment: str
    service_id: str
    container_name: str
    compose_project: str
    commit_sha: str
    running_image_id: str
    observed_at: datetime
    challenge_verified: bool
    challenge_sha256: str
    running: bool
    healthy: bool
    checkout_clean: bool


@dataclass(frozen=True, slots=True)
class OCIProposalIntent:
    requester_subject: str
    request_id: str
    environment: str
    service_id: str
    target_commit_sha: str
    base_commit_sha: str
    manifest_digest: str
    target_image_id: str
    base_image_id: str
    attestation_statement_sha256: str
    host_challenge_sha256: str
    preview_hash: str
    rollback_image_id: str
    rollback_ready: bool


@dataclass(frozen=True, slots=True)
class SealedOCICandidate:
    """Hash is diagnostic binding, NOT approval, host attestation or ACT ticket."""

    status: str
    binding_sha256: str
    expires_at: datetime
    issued_at: datetime
    requester_subject: str
    environment: str
    service_id: str
    version: int = 1


@dataclass(frozen=True, slots=True)
class ApprovalEvidence:
    """Future backend portal readback; never accept directly from an MCP tool."""

    proposal_id: str
    binding_sha256: str
    requester_subject: str
    approver_subject: str
    environment: str
    service_id: str
    state: str
    approved_at: datetime
    expires_at: datetime
    permission_fresh: bool
    permissions_checked_at: datetime
    approved_in_portal: bool
    revoked: bool
    already_consumed: bool


def _uuid(value: object) -> bool:
    if type(value) is not str:
        return False
    try:
        parsed = UUID(value)
    except (ValueError, TypeError, AttributeError):
        return False
    return parsed.version == 4 and str(parsed) == value


def _time(value: object) -> bool:
    return (type(value) is datetime and value.tzinfo is not None
            and value.utcoffset() is not None)


def _fresh(observed: datetime, now: datetime) -> bool:
    age = now.astimezone(timezone.utc) - observed.astimezone(timezone.utc)
    return -_SKEW <= age <= _AGE


def _hash(payload: dict[str, object]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=True).encode("utf-8")).hexdigest()


def seal_oci_candidate(*, intent: OCIProposalIntent, ci: CIReleaseEvidence,
                       host: HostRuntimeEvidence, now: datetime,
                       backend_policy_enabled: bool = False) -> SealedOCICandidate:
    """Return an exact-image proposal hash only after independent evidence gates.

    This is still a PREPARE candidate, not approval. The backend must store this
    full payload transactionally and independently verify identity/CI/host.
    """
    if not (isinstance(intent, OCIProposalIntent) and isinstance(ci, CIReleaseEvidence)
            and isinstance(host, HostRuntimeEvidence) and _time(now)):
        raise OCIGateRejected("OCI_CONTRACT_INVALID")
    if type(backend_policy_enabled) is not bool or not backend_policy_enabled:
        raise OCIGateRejected("OCI_POLICY_DISABLED")
    if (not _uuid(intent.requester_subject) or not _uuid(intent.request_id)
            or intent.service_id != "public-hub" or intent.environment not in CONTAINER):
        raise OCIGateRejected("OCI_TARGET_INVALID")
    if not all(type(value) is str and _SHA.fullmatch(value) for value in
               (intent.target_commit_sha, intent.base_commit_sha)):
        raise OCIGateRejected("OCI_COMMIT_INVALID")
    if intent.target_commit_sha == intent.base_commit_sha:
        raise OCIGateRejected("OCI_ALREADY_DEPLOYED")
    if not all(type(value) is str and _DIGEST.fullmatch(value) for value in
               (intent.manifest_digest, intent.target_image_id, intent.base_image_id,
                intent.rollback_image_id)):
        raise OCIGateRejected("OCI_DIGEST_INVALID")
    if (intent.base_image_id == intent.target_image_id
            or intent.rollback_image_id != intent.base_image_id):
        raise OCIGateRejected("OCI_ROLLBACK_IMAGE_INVALID")
    if not (type(intent.attestation_statement_sha256) is str
            and _HEX64.fullmatch(intent.attestation_statement_sha256)
            and type(intent.host_challenge_sha256) is str
            and _HEX64.fullmatch(intent.host_challenge_sha256)
            and type(intent.preview_hash) is str and _HEX64.fullmatch(intent.preview_hash)):
        raise OCIGateRejected("OCI_BINDING_FIELDS_INVALID")
    if type(intent.rollback_ready) is not bool or not intent.rollback_ready:
        raise OCIGateRejected("OCI_ROLLBACK_NOT_READY")

    if (ci.repository != REPOSITORY or ci.image != IMAGE or ci.workflow != WORKFLOW
            or ci.source_ref != SOURCE_REF or type(ci.signature_verified) is not bool
            or not ci.signature_verified):
        raise OCIGateRejected("OCI_ATTESTATION_INVALID")
    if (ci.commit_sha != intent.target_commit_sha
            or ci.manifest_digest != intent.manifest_digest
            or ci.image_config_id != intent.target_image_id
            or ci.statement_sha256 != intent.attestation_statement_sha256):
        raise OCIGateRejected("OCI_ATTESTATION_DRIFT")
    if not (type(ci.verified_at) is datetime and _time(ci.verified_at)
            and _fresh(ci.verified_at, now)):
        raise OCIGateRejected("OCI_ATTESTATION_STALE")

    container, project = CONTAINER[intent.environment]
    if (host.environment != intent.environment or host.service_id != intent.service_id
            or host.container_name != container or host.compose_project != project
            or host.commit_sha != intent.base_commit_sha
            or host.running_image_id != intent.base_image_id
            or host.challenge_sha256 != intent.host_challenge_sha256):
        raise OCIGateRejected("OCI_HOST_DRIFT")
    if (type(host.challenge_verified) is not bool or not host.challenge_verified
            or type(host.running) is not bool or not host.running
            or type(host.healthy) is not bool or not host.healthy
            or type(host.checkout_clean) is not bool or not host.checkout_clean):
        raise OCIGateRejected("OCI_HOST_UNTRUSTED")
    if not (type(host.observed_at) is datetime and _time(host.observed_at)
            and _fresh(host.observed_at, now)):
        raise OCIGateRejected("OCI_HOST_STALE")

    payload = {
        "version": 1,
        "repository": REPOSITORY,
        "image": IMAGE,
        "workflow": WORKFLOW,
        "source_ref": SOURCE_REF,
        "environment": intent.environment,
        "service_id": intent.service_id,
        "container_name": container,
        "compose_project": project,
        "requester_subject": intent.requester_subject,
        "request_id": intent.request_id,
        "target_commit_sha": intent.target_commit_sha,
        "base_commit_sha": intent.base_commit_sha,
        "signed_manifest_digest": intent.manifest_digest,
        "signed_release_image_id": intent.target_image_id,
        "expected_base_image_id": intent.base_image_id,
        "rollback_image_id": intent.rollback_image_id,
        "attestation_statement_sha256": intent.attestation_statement_sha256,
        "host_challenge_sha256": intent.host_challenge_sha256,
        "preview_hash": intent.preview_hash,
        "issued_at": now.astimezone(timezone.utc).isoformat(),
        "expires_at": (now + _TTL).astimezone(timezone.utc).isoformat(),
    }
    return SealedOCICandidate(
        status="candidate_only", binding_sha256=_hash(payload),
        expires_at=now + _TTL, issued_at=now,
        requester_subject=intent.requester_subject,
        environment=intent.environment, service_id=intent.service_id,
    )


def evaluate_portal_approval(*, candidate: SealedOCICandidate,
                             approval: ApprovalEvidence, now: datetime,
                             backend_policy_enabled: bool = False) -> str:
    """Return 'approval_evidence_shape_only', NEVER authorize ACT.

    A separate backend must compare immutable DB fields and reauthorize Core;
    this function cannot authenticate who constructed ApprovalEvidence.
    """
    if not (isinstance(candidate, SealedOCICandidate)
            and isinstance(approval, ApprovalEvidence) and _time(now)):
        raise OCIGateRejected("OCI_APPROVAL_INVALID")
    if type(backend_policy_enabled) is not bool or not backend_policy_enabled:
        raise OCIGateRejected("OCI_POLICY_DISABLED")
    if (candidate.status != "candidate_only" or candidate.version != 1
            or not isinstance(candidate.binding_sha256, str)
            or _HEX64.fullmatch(candidate.binding_sha256) is None):
        raise OCIGateRejected("OCI_APPROVAL_INVALID")
    if not (_uuid(approval.proposal_id) and _uuid(approval.requester_subject)
            and _uuid(approval.approver_subject)):
        raise OCIGateRejected("OCI_APPROVAL_IDENTITY_INVALID")
    # Requester and approver may be the same named human, but the approval
    # must still be an explicit, current portal decision tied to this binding.
    if (approval.requester_subject != candidate.requester_subject
            or approval.environment != candidate.environment
            or approval.service_id != candidate.service_id):
        raise OCIGateRejected("OCI_APPROVAL_TARGET_MISMATCH")
    if (type(approval.binding_sha256) is not str
            or not hmac.compare_digest(candidate.binding_sha256, approval.binding_sha256)):
        raise OCIGateRejected("OCI_APPROVAL_BINDING_DRIFT")
    if not (_time(approval.approved_at) and _time(approval.expires_at)
            and _time(candidate.expires_at) and _time(candidate.issued_at)):
        raise OCIGateRejected("OCI_APPROVAL_TIME_INVALID")
    if (approval.expires_at != candidate.expires_at
            or approval.approved_at < candidate.issued_at
            or approval.approved_at > now + _SKEW
            or now >= approval.expires_at or approval.approved_at > approval.expires_at):
        raise OCIGateRejected("OCI_APPROVAL_EXPIRED")
    if (not _time(approval.permissions_checked_at)
            or not _fresh(approval.permissions_checked_at, now)):
        raise OCIGateRejected("OCI_APPROVAL_PERMISSION_STALE")
    if (approval.state != "approved" or type(approval.permission_fresh) is not bool
            or not approval.permission_fresh or type(approval.approved_in_portal) is not bool
            or not approval.approved_in_portal or type(approval.revoked) is not bool
            or approval.revoked or type(approval.already_consumed) is not bool
            or approval.already_consumed):
        raise OCIGateRejected("OCI_APPROVAL_NOT_ACTIVE")
    return "approval_evidence_shape_only"

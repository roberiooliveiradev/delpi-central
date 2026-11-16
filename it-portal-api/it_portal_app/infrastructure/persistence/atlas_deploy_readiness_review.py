"""ATLAS P2.2h.2q–2r: read-only CI + one-shot journal readiness review.

Strictly private and default disabled. Does NOT reserve/consume a nonce,
create a candidate, approve an operation, set Core RBAC, or call Docker.
The release reader checks GitHub attestation and GHCR image identity; the
journal reader queries a separately scoped read-only PostgreSQL role twice,
before and after slow upstream verification. That reduces TOCTOU risk but
does NOT eliminate races. Even exact matches return status='blocked'.
No new HTTP endpoints/MCP tools, permissions, grants or deploy commands.
"""
from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID

from .atlas_deploy_challenge_inspection import (
    ChallengeInspectionError, ExplicitChallengeReadOnlyReader,
    UnreservedChallengeSnapshot,
)
from .atlas_deploy_oci_release_evidence import (
    OCIReleaseEvidenceReader,
)
from .atlas_deploy_oci_seal import (
    CIReleaseEvidence, IMAGE, REPOSITORY, SOURCE_REF, WORKFLOW,
)

_SHA40 = re.compile(r"[0-9a-f]{40}\Z")
_IMAGEID = re.compile(r"sha256:[0-9a-f]{64}\Z")
_HEX64 = re.compile(r"[0-9a-f]{64}\Z")
_MAX_AGE = timedelta(seconds=120)
_CLOCK_SKEW = timedelta(seconds=5)
_UNMET = (
    "HOST_DOCKER_AND_GIT_WITNESSES_NOT_BACKEND_VERIFIED",
    "HOST_COLLECTOR_IDENTITY_NOT_ATTESTED",
    "CHECKOUT_AND_IGNORED_FILES_NOT_ATTESTED",
    "CHALLENGE_OBSERVED_NOT_CONSUMED",
    "ROLLBACK_AND_BACKUP_NOT_ATTESTED",
    "MIGRATIONS_NOT_ATTESTED",
    "CORE_HUMAN_PERMISSION_NOT_CHECKED",
    "PREPARE_DISABLED",
    "ACT_DISABLED",
)


class ReadinessReviewError(Exception):
    """Finite internal codes. Never expose raw SQL, token, GHCR or nonce."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class TargetReleaseReview:
    """Only identity expectations from trusted backend; not attested input."""

    requester_subject: str
    environment: str
    service_id: str
    target_commit_sha: str
    manifest_digest: str
    target_image_id: str
    statement_sha256: str


@dataclass(frozen=True, slots=True)
class BlockedReadinessReport:
    """Immutable diagnostic, not an approved OCI proposal or rollout ticket."""

    status: str
    blocks: tuple[str, ...]
    environment: str
    service_id: str
    target_commit_sha: str
    target_image_id: str
    manifest_digest: str
    statement_sha256: str
    release_verified_at: datetime
    challenge_checked_at: datetime
    challenge_expires_at: datetime
    ci_signature_verified: bool
    challenge_reserved: bool = False
    challenge_consumed: bool = False
    host_authenticated: bool = False
    rollback_ready: bool = False
    migrations_safe: bool = False
    core_permission_verified: bool = False
    prepare_eligible: bool = False
    can_execute: bool = False
    challenge_issued_at: datetime | None = None


def _target_valid(target: object) -> bool:
    if type(target) is not TargetReleaseReview:
        return False
    try:
        parsed = UUID(target.requester_subject)
        subject_ok = parsed.version == 4 and str(parsed) == target.requester_subject
    except (ValueError, TypeError, AttributeError):
        return False
    return (
        subject_ok
        and target.environment in ("hml", "prod")
        and target.service_id == "public-hub"
        and type(target.target_commit_sha) is str
        and _SHA40.fullmatch(target.target_commit_sha) is not None
        and type(target.manifest_digest) is str
        and _IMAGEID.fullmatch(target.manifest_digest) is not None
        and type(target.target_image_id) is str
        and _IMAGEID.fullmatch(target.target_image_id) is not None
        and type(target.statement_sha256) is str
        and _HEX64.fullmatch(target.statement_sha256) is not None
    )


class ReadOnlyReleaseReadinessReviewer:
    """Only a future trusted BFF may construct this from concrete readers.

    In production DIAGNOSTICS are off by default and there is no route
    or caller to enable them. If a separate owner later enables diagnostic
    access, it must supply fresh Core RBAC and dedicated DB SELECT grants.
    """

    def __init__(
        self, *,
        challenge_reader: ExplicitChallengeReadOnlyReader,
        release_reader: OCIReleaseEvidenceReader,
        diagnostics_enabled: bool = False,
    ):
        self._challenge = challenge_reader
        self._release = release_reader
        self._enabled = diagnostics_enabled is True

    async def read(
        self, *, target: TargetReleaseReview, challenge: str,
    ) -> BlockedReadinessReport:
        if not self._enabled:
            raise ReadinessReviewError("ATLAS_READINESS_DISABLED")
        if not _target_valid(target):
            raise ReadinessReviewError("ATLAS_READINESS_TARGET_INVALID")

        scope = {
            "requester_subject": target.requester_subject,
            "environment": target.environment,
            "service_id": target.service_id,
            "nonce": challenge,
        }
        # Validate nonce and owner FIRST through the scoped database reader.
        # A fake/offline CI proof must not trigger network work on an
        # expired/consumed/cross-owner challenge.
        try:
            before = await asyncio.to_thread(self._challenge.read, **scope)
        except ChallengeInspectionError:
            raise ReadinessReviewError("ATLAS_READINESS_CHALLENGE_UNAVAILABLE") from None
        except Exception:
            raise ReadinessReviewError("ATLAS_READINESS_CHALLENGE_UNAVAILABLE") from None
        if type(before) is not UnreservedChallengeSnapshot:
            raise ReadinessReviewError("ATLAS_READINESS_CHALLENGE_INVALID")

        try:
            release = await self._release.read(
                manifest_digest=target.manifest_digest,
                commit_sha=target.target_commit_sha,
            )
        except Exception:
            raise ReadinessReviewError("ATLAS_READINESS_RELEASE_UNAVAILABLE") from None
        if type(release) is not CIReleaseEvidence:
            raise ReadinessReviewError("ATLAS_READINESS_RELEASE_INVALID")
        if (
            release.repository != REPOSITORY
            or release.image != IMAGE
            or release.workflow != WORKFLOW
            or release.source_ref != SOURCE_REF
            or release.commit_sha != target.target_commit_sha
            or release.manifest_digest != target.manifest_digest
            or release.image_config_id != target.target_image_id
            or release.statement_sha256 != target.statement_sha256
        ):
            raise ReadinessReviewError("ATLAS_READINESS_RELEASE_DRIFT")
        if release.signature_verified is not True:
            raise ReadinessReviewError("ATLAS_READINESS_RELEASE_UNTRUSTED")

        # Database clock is authoritative; no stale challenge may be
        # reinterpreted as eligible after GitHub/GHCR verification delays.
        try:
            after = await asyncio.to_thread(self._challenge.read, **scope)
        except Exception:
            raise ReadinessReviewError("ATLAS_READINESS_CHALLENGE_UNAVAILABLE") from None
        if type(after) is not UnreservedChallengeSnapshot:
            raise ReadinessReviewError("ATLAS_READINESS_CHALLENGE_INVALID")
        if (
            before.status != "observed_not_reserved"
            or after.status != "observed_not_reserved"
            or before.one_shot_consumed is not False
            or after.one_shot_consumed is not False
            or before.environment != target.environment
            or after.environment != target.environment
            or before.service_id != target.service_id
            or after.service_id != target.service_id
            or before.issued_at != after.issued_at
            or before.expires_at != after.expires_at
            or before.observed_at > after.observed_at
        ):
            raise ReadinessReviewError("ATLAS_READINESS_CHALLENGE_DRIFT")

        timestamp = release.verified_at
        now = after.observed_at
        if (
            type(timestamp) is not datetime
            or timestamp.tzinfo is None
            or timestamp.utcoffset() is None
            or type(now) is not datetime
            or now.tzinfo is None
            or now.utcoffset() is None
        ):
            raise ReadinessReviewError("ATLAS_READINESS_CLOCK_INVALID")
        age = now.astimezone(timezone.utc) - timestamp.astimezone(timezone.utc)
        if age < -_CLOCK_SKEW or age > _MAX_AGE:
            raise ReadinessReviewError("ATLAS_READINESS_RELEASE_STALE")
        return BlockedReadinessReport(
            status="blocked", blocks=_UNMET,
            environment=target.environment, service_id=target.service_id,
            target_commit_sha=target.target_commit_sha,
            target_image_id=target.target_image_id,
            manifest_digest=target.manifest_digest,
            statement_sha256=target.statement_sha256,
            release_verified_at=timestamp.astimezone(timezone.utc),
            challenge_checked_at=now.astimezone(timezone.utc),
            challenge_expires_at=after.expires_at.astimezone(timezone.utc),
            challenge_issued_at=after.issued_at.astimezone(timezone.utc),
            ci_signature_verified=True,
        )

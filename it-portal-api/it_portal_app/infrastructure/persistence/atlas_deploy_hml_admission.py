"""ATLAS P2.2h.2w: HML-only, default-OFF admission diagnostic.

Connect a fresh human Core /me lookup, the existing signed OCI + host +
journal reviewer, and a second fresh Core /me lookup after slow verification.
This is a read-only, fail-closed HML pilot diagnostic. It cannot grant
PREPARE/ACT, issue or consume nonce, certify restore, or mint a host identity.
No HTTP routes, MCP tools, migrations, connection provisioning or write role.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from .atlas_deploy_core_gate import (
    AtlasCoreGateError, FreshCorePrepareInspector, FreshCoreGrantObservation,
    TrustedHumanActor,
)
from .atlas_deploy_full_readiness import (
    FullReadOnlyReadinessReviewer, FullReadinessBlocked,
)
from .atlas_deploy_host_receipt_bridge import (
    ExpectedBaseRelease, PinnedHostTarget, SignedReceiptWire,
)
from .atlas_deploy_readiness_review import TargetReleaseReview

_MAX_CORE_RECHECK = timedelta(seconds=60)
_UNVERIFIED = (
    "HOST_COLLECTOR_TRANSPORT_NOT_ATTESTED",
    "BACKUP_RESTORE_TEST_NOT_ATTESTED",
    "ROLLBACK_REHEARSAL_NOT_ATTESTED",
    "MIGRATION_REVERSIBILITY_NOT_ATTESTED",
    "POSTGRES_ONE_SHOT_WRITER_NOT_APPROVED",
    "PREPARE_DISABLED",
    "ACT_DISABLED",
)


class HMLAdmissionError(Exception):
    """Sanitized, finite error code, never Core token or nonce."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class HMLPilotBlockedDiagnostic:
    """Operator-facing safe subset, never a proposal, approval or ACT token."""

    status: str
    blocks: tuple[str, ...]
    environment: str
    service_id: str
    base_commit_sha: str
    target_commit_sha: str
    core_checked_at: datetime
    journal_checked_at: datetime
    core_explicit_grants_observed: bool = True
    collector_identity_attested: bool = False
    recovery_verified: bool = False
    migrations_verified: bool = False
    challenge_consumed: bool = False
    prepare_eligible: bool = False
    can_execute: bool = False


class HMLReadOnlyAdmissionReviewer:
    """Trusted composition only; never expose inputs to a client request.

    Signatures/DB queries are performed by existing backend readers,
    and human Core identity is read fresh before AND after those operations.
    All outputs stay blocked regardless of grant or receipt validity.
    """

    def __init__(
        self, *,
        core: FreshCorePrepareInspector,
        full: FullReadOnlyReadinessReviewer,
        enabled: bool = False,
    ):
        self._core = core
        self._full = full
        self._enabled = enabled is True

    async def review(
        self, *,
        actor: TrustedHumanActor,
        release: TargetReleaseReview,
        host: PinnedHostTarget,
        base: ExpectedBaseRelease,
        runtime_receipt: SignedReceiptWire,
        checkout_receipt: SignedReceiptWire,
        challenge: str,
    ) -> HMLPilotBlockedDiagnostic:
        if not self._enabled:
            raise HMLAdmissionError("ATLAS_HML_ADMISSION_DISABLED")
        if (
            type(actor) is not TrustedHumanActor
            or type(release) is not TargetReleaseReview
            or type(host) is not PinnedHostTarget
            or type(base) is not ExpectedBaseRelease
            or release.environment != "hml"
            or host.environment != "hml"
            or release.service_id != "public-hub"
            or host.service_id != "public-hub"
            or release.requester_subject != actor.subject
        ):
            raise HMLAdmissionError("ATLAS_HML_ACTOR_OR_TARGET_DENIED")
        try:
            core_before = await self._core.read(actor=actor)
        except AtlasCoreGateError:
            raise HMLAdmissionError("ATLAS_HML_CORE_UNAVAILABLE_OR_DENIED") from None
        except Exception:
            raise HMLAdmissionError("ATLAS_HML_CORE_UNAVAILABLE_OR_DENIED") from None
        if (
            type(core_before) is not FreshCoreGrantObservation
            or core_before.subject != actor.subject
            or core_before.required_grants_present is not True
            or core_before.prepare_eligible is not False
            or core_before.can_execute is not False
        ):
            raise HMLAdmissionError("ATLAS_HML_CORE_CONTRACT_INVALID")

        try:
            verified = await self._full.read(
                target=release, host=host, base=base,
                runtime_receipt=runtime_receipt,
                checkout_receipt=checkout_receipt,
                challenge=challenge,
            )
        except Exception:
            raise HMLAdmissionError("ATLAS_HML_RELEASE_HOST_OR_JOURNAL_DENIED") from None
        if (
            type(verified) is not FullReadinessBlocked
            or verified.status != "blocked"
            or verified.environment != "hml"
            or verified.service_id != "public-hub"
            or verified.target_commit_sha != release.target_commit_sha
            or verified.target_image_id != release.target_image_id
            or verified.base_commit_sha != base.commit_sha
            or verified.base_image_id != base.image_id
            or verified.host_id != host.host_id
            or verified.ci_signature_verified is not True
            or verified.host_receipt_integrity_verified is not True
            or verified.host_collector_identity_attested is not False
            or verified.git_checkout_integrity_attested is not False
            or verified.one_shot_challenge_consumed is not False
            or verified.core_permission_verified is not False
            or verified.backup_and_rollback_verified is not False
            or verified.migrations_safe is not False
            or verified.prepare_eligible is not False
            or verified.can_execute is not False
            or "PREPARE_DISABLED" not in verified.blocks
            or "ACT_DISABLED" not in verified.blocks
        ):
            raise HMLAdmissionError("ATLAS_HML_UPSTREAM_CONTRACT_INVALID")

        # Force-refresh Core RBAC after network and host verification to
        # detect a revoked grant. This does not eliminate all races.
        try:
            core_after = await self._core.read(actor=actor)
        except Exception:
            raise HMLAdmissionError("ATLAS_HML_CORE_RECHECK_DENIED") from None
        if (
            type(core_after) is not FreshCoreGrantObservation
            or core_after.subject != core_before.subject
            or core_after.required_grants_present is not True
            or core_after.prepare_eligible is not False
            or core_after.can_execute is not False
            or not isinstance(core_before.checked_at, datetime)
            or not isinstance(core_after.checked_at, datetime)
            or core_before.checked_at.tzinfo is None
            or core_after.checked_at.tzinfo is None
            or core_before.checked_at.utcoffset() is None
            or core_after.checked_at.utcoffset() is None
            or not timedelta(0) <=
                core_after.checked_at - core_before.checked_at <= _MAX_CORE_RECHECK
        ):
            raise HMLAdmissionError("ATLAS_HML_CORE_RECHECK_DRIFT")
        return HMLPilotBlockedDiagnostic(
            status="blocked",
            blocks=tuple(dict.fromkeys((*verified.blocks, *_UNVERIFIED))),
            environment="hml",
            service_id="public-hub",
            base_commit_sha=base.commit_sha,
            target_commit_sha=release.target_commit_sha,
            core_checked_at=core_after.checked_at.astimezone(timezone.utc),
            journal_checked_at=verified.challenge_checked_at,
        )

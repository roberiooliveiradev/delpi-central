"""ATLAS P2.2h.2aa: compose a signed S2S client, human review and recovery.

Future HML-only offline/read-only admission *diagnostic*. No HTTP route,
MCP tool, socket, host connection, Keycloak client creation, journal write,
candidate persistence or deploy. Authenticated Keycloak client != OS host
attestation; recovery references != actual restore/rollback proofs.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from .atlas_deploy_core_gate import TrustedHumanActor
from .atlas_deploy_hml_admission import (
    HMLPilotBlockedDiagnostic, HMLReadOnlyAdmissionReviewer,
)
from .atlas_deploy_hml_recovery_review import (
    RecoveryArtifactMetadata, HMLRecoveryMetadataReport,
    inspect_hml_recovery_metadata,
)
from .atlas_deploy_hml_s2s_collector import (
    HMLCollectorClientObservation, HMLCollectorS2SVerifier,
)
from .atlas_deploy_host_receipt_bridge import (
    PinnedHostTarget, ExpectedBaseRelease, SignedReceiptWire,
)
from .atlas_deploy_readiness_review import TargetReleaseReview

_CLOCK_SKEW = timedelta(seconds=5)
_MAX_PIPELINE_AGE = timedelta(seconds=90)
_UNPROVEN = (
    "KEYCLOAK_CLIENT_NOT_OS_PROCESS_ATTESTATION",
    "COLLECTOR_TRANSPORT_MUTUAL_AUTH_UNPROVEN",
    "READ_ONLY_DOCKER_PROXY_NOT_PROVEN",
    "JOURNAL_CHALLENGE_NOT_CONSUMED",
    "PREPARE_DISABLED",
    "ACT_DISABLED",
)


class HMLTechnicalAdmissionError(Exception):
    """Finite sanitized code; no token, challenge or HMAC body."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class HMLTechnicalAdmissionBlocked:
    status: str
    blocks: tuple[str, ...]
    environment: str
    service_id: str
    host_id: str
    collector_client_id: str
    source_commit_sha: str
    target_commit_sha: str
    inspected_at: datetime
    keycloak_client_token_verified: bool = True
    host_process_attested: bool = False
    host_transport_attested: bool = False
    backup_restored: bool = False
    rollback_tested: bool = False
    migrations_safe: bool = False
    core_prepare_authorized: bool = False
    challenge_consumed: bool = False
    prepare_eligible: bool = False
    can_execute: bool = False


class HMLTechnicalReadinessReviewer:
    """Opaque S2S raw token is validated here; never trust caller's DTO.

    The Keycloak service credential MUST be supplied by trusted backend
    transport, not from a user-facing request body or ChatGPT/MCP.
    """

    def __init__(
        self, *,
        s2s: HMLCollectorS2SVerifier,
        human_and_ci: HMLReadOnlyAdmissionReviewer,
        enabled: bool = False,
    ):
        self._s2s = s2s
        self._hml = human_and_ci
        self._enabled = enabled is True

    async def read(
        self, *,
        service_token: str,
        actor: TrustedHumanActor,
        release: TargetReleaseReview,
        host: PinnedHostTarget,
        base: ExpectedBaseRelease,
        runtime_receipt: SignedReceiptWire,
        checkout_receipt: SignedReceiptWire,
        challenge: str,
        recovery: RecoveryArtifactMetadata | None = None,
    ) -> HMLTechnicalAdmissionBlocked:
        if not self._enabled:
            raise HMLTechnicalAdmissionError("ATLAS_HML_TECHNICAL_DISABLED")
        if (
            type(host) is not PinnedHostTarget
            or host.environment != "hml"
            or host.service_id != "public-hub"
            or type(actor) is not TrustedHumanActor
            or actor.principal_type != "user"
            or type(release) is not TargetReleaseReview
            or release.environment != "hml"
            or release.service_id != "public-hub"
            or release.requester_subject != actor.subject
            or type(base) is not ExpectedBaseRelease
        ):
            raise HMLTechnicalAdmissionError("ATLAS_HML_TECHNICAL_SCOPE_DENIED")

        # Verify S2S identity before making expensive Core/OCI/journal calls.
        try:
            collector = await asyncio.to_thread(
                self._s2s.verify, service_token=service_token, host=host,
            )
        except Exception:
            raise HMLTechnicalAdmissionError("ATLAS_HML_TECHNICAL_S2S_DENIED") from None
        if (
            type(collector) is not HMLCollectorClientObservation
            or collector.host_id != host.host_id
            or collector.keycloak_client_verified is not True
            or collector.host_process_attested is not False
            or collector.transport_mutual_auth_attested is not False
            or collector.prepare_eligible is not False
            or collector.can_execute is not False
        ):
            raise HMLTechnicalAdmissionError("ATLAS_HML_TECHNICAL_S2S_CONTRACT_INVALID")

        try:
            human = await self._hml.review(
                actor=actor, release=release, host=host, base=base,
                runtime_receipt=runtime_receipt,
                checkout_receipt=checkout_receipt, challenge=challenge,
            )
        except Exception:
            raise HMLTechnicalAdmissionError("ATLAS_HML_TECHNICAL_READINESS_DENIED") from None
        if (
            type(human) is not HMLPilotBlockedDiagnostic
            or human.status != "blocked"
            or human.environment != "hml"
            or human.service_id != "public-hub"
            or human.target_commit_sha != release.target_commit_sha
            or human.base_commit_sha != base.commit_sha
            or human.core_explicit_grants_observed is not True
            or human.collector_identity_attested is not False
            or human.recovery_verified is not False
            or human.migrations_verified is not False
            or human.challenge_consumed is not False
            or human.prepare_eligible is not False
            or human.can_execute is not False
            or "PREPARE_DISABLED" not in human.blocks
            or "ACT_DISABLED" not in human.blocks
        ):
            raise HMLTechnicalAdmissionError("ATLAS_HML_TECHNICAL_READINESS_CONTRACT_INVALID")

        # Token must remain valid after the slow CI/DB/Core checks.
        at = human.core_checked_at
        if (
            type(at) is not datetime
            or at.tzinfo is None or at.utcoffset() is None
            or type(collector.observed_at) is not datetime
            or collector.observed_at.tzinfo is None
            or collector.observed_at.utcoffset() is None
            or type(collector.token_expires_at) is not datetime
            or collector.token_expires_at.tzinfo is None
            or collector.token_expires_at.utcoffset() is None
        ):
            raise HMLTechnicalAdmissionError("ATLAS_HML_TECHNICAL_CLOCK_INVALID")
        gap = at.astimezone(timezone.utc) - collector.observed_at.astimezone(timezone.utc)
        if (
            gap < -_CLOCK_SKEW or gap > _MAX_PIPELINE_AGE
            or collector.token_expires_at.astimezone(timezone.utc)
                <= at.astimezone(timezone.utc) + _CLOCK_SKEW
        ):
            raise HMLTechnicalAdmissionError("ATLAS_HML_TECHNICAL_IDENTITY_STALE")

        try:
            recovered = inspect_hml_recovery_metadata(
                base=base, submitted=recovery, now=at,
            )
        except Exception:
            raise HMLTechnicalAdmissionError("ATLAS_HML_TECHNICAL_RECOVERY_INVALID") from None
        if (
            type(recovered) is not HMLRecoveryMetadataReport
            or recovered.status != "blocked"
            or recovered.actual_restore_verified is not False
            or recovered.actual_rollback_verified is not False
            or recovered.actual_migrations_verified is not False
            or recovered.independent_reviewer_verified is not False
            or recovered.prepare_eligible is not False
            or recovered.can_execute is not False
        ):
            raise HMLTechnicalAdmissionError("ATLAS_HML_TECHNICAL_RECOVERY_CONTRACT_INVALID")

        return HMLTechnicalAdmissionBlocked(
            status="blocked",
            blocks=tuple(dict.fromkeys((*human.blocks, *recovered.blocks, *_UNPROVEN))),
            environment="hml", service_id="public-hub",
            host_id=host.host_id, collector_client_id=collector.client_id,
            source_commit_sha=base.commit_sha,
            target_commit_sha=release.target_commit_sha,
            inspected_at=at.astimezone(timezone.utc),
        )

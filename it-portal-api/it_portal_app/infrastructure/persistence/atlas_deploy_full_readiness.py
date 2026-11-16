"""ATLAS P2.2h.2t: combine independently verified backend facts, ALWAYS BLOCK.

Private composition of journal challenge readback, CI release verification,
and two signed Linux host receipts (Docker v2 and Git v1). No transport or
key provisioning, HTTP route, MCP tool, persistence, permission grant,
approval, PREPARE or ACT. A valid MAC does NOT attest the OS collector identity.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime

from .atlas_deploy_challenge_inspection import (
    ExplicitChallengeReadOnlyReader, UnreservedChallengeSnapshot,
)
from .atlas_deploy_host_receipt_bridge import (
    ExpectedBaseRelease, HostReceiptBridgeError, PinnedHostTarget,
    SignedReceiptWire, verify_host_receipt_pair,
)
from .atlas_deploy_readiness_review import (
    BlockedReadinessReport, ReadOnlyReleaseReadinessReviewer, TargetReleaseReview,
)


class FullReadinessError(Exception):
    """Finite sanitized diagnostic error codes."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class FullReadinessBlocked:
    """Never a PREPARE candidate, authorization, approval or ACT ticket."""

    status: str
    blocks: tuple[str, ...]
    environment: str
    service_id: str
    target_commit_sha: str
    target_image_id: str
    base_commit_sha: str
    base_image_id: str
    host_id: str
    challenge_checked_at: datetime
    release_verified_at: datetime
    runtime_receipt_sha256: str
    git_receipt_sha256: str
    ci_signature_verified: bool = True
    host_receipt_integrity_verified: bool = True
    host_collector_identity_attested: bool = False
    git_checkout_integrity_attested: bool = False
    one_shot_challenge_consumed: bool = False
    core_permission_verified: bool = False
    backup_and_rollback_verified: bool = False
    migrations_safe: bool = False
    prepare_eligible: bool = False
    can_execute: bool = False


class FullReadOnlyReadinessReviewer:
    """Server-side, default-disabled, non-routable multi-source composition.

    The Core subject, pinned host, base image, nonce and keys must all come
    from independent trusted backend policy. Nothing about the shapes of
    the supplied dataclasses proves that origin.
    """

    def __init__(
        self, *,
        readiness: ReadOnlyReleaseReadinessReviewer,
        challenge_reader: ExplicitChallengeReadOnlyReader,
        runtime_key: bytes,
        checkout_key: bytes,
        diagnostics_enabled: bool = False,
    ):
        self._readiness = readiness
        self._challenges = challenge_reader
        self._runtime_key = runtime_key
        self._checkout_key = checkout_key
        self._enabled = diagnostics_enabled is True

    async def read(
        self, *,
        target: TargetReleaseReview,
        host: PinnedHostTarget,
        base: ExpectedBaseRelease,
        runtime_receipt: SignedReceiptWire,
        checkout_receipt: SignedReceiptWire,
        challenge: str,
    ) -> FullReadinessBlocked:
        if not self._enabled:
            raise FullReadinessError("ATLAS_FULL_REVIEW_DISABLED")
        if (
            type(target) is not TargetReleaseReview
            or type(host) is not PinnedHostTarget
            or type(base) is not ExpectedBaseRelease
            or target.environment != host.environment
            or target.service_id != host.service_id
            or target.target_commit_sha == base.commit_sha
            or target.target_image_id == base.image_id
        ):
            raise FullReadinessError("ATLAS_FULL_TARGET_MISMATCH")

        # The existing CI/journal reviewer already verifies the GitHub/GHCR
        # signed release and reads the Postgres challenge BEFORE and AFTER
        # potentially slow network verification.
        try:
            ci = await self._readiness.read(target=target, challenge=challenge)
        except Exception:
            raise FullReadinessError("ATLAS_FULL_RELEASE_OR_CHALLENGE_DENIED") from None
        if (
            type(ci) is not BlockedReadinessReport
            or ci.status != "blocked"
            or ci.ci_signature_verified is not True
            or ci.prepare_eligible is not False
            or ci.can_execute is not False
            or ci.environment != target.environment
            or ci.service_id != target.service_id
            or ci.target_commit_sha != target.target_commit_sha
            or ci.target_image_id != target.target_image_id
            or "ACT_DISABLED" not in ci.blocks
            or "PREPARE_DISABLED" not in ci.blocks
        ):
            raise FullReadinessError("ATLAS_FULL_RELEASE_CONTRACT_INVALID")

        # Verify raw signed bytes in BFF against keys stored independently
        # of the Linux collector's outgoing data. DB clock is authoritative.
        try:
            host_pair = verify_host_receipt_pair(
                runtime_receipt=runtime_receipt,
                git_receipt=checkout_receipt,
                runtime_key=self._runtime_key,
                git_key=self._checkout_key,
                target=host,
                base=base,
                nonce=challenge,
                now=ci.challenge_checked_at,
            )
        except HostReceiptBridgeError:
            raise FullReadinessError("ATLAS_FULL_HOST_EVIDENCE_DENIED") from None
        except Exception:
            raise FullReadinessError("ATLAS_FULL_HOST_EVIDENCE_UNAVAILABLE") from None
        if (
            host_pair.signature_integrity_verified is not True
            or host_pair.collector_identity_attested is not False
            or host_pair.checkout_integrity_attested is not False
            or host_pair.prepare_eligible is not False
        ):
            raise FullReadinessError("ATLAS_FULL_HOST_CONTRACT_INVALID")

        # Third SELECT after verifying both HMACs. Not a reservation: an
        # adversary can still consume it after this SELECT. Never authorize.
        try:
            checked = await asyncio.to_thread(
                self._challenges.read,
                requester_subject=target.requester_subject,
                environment=target.environment,
                service_id=target.service_id,
                nonce=challenge,
            )
        except Exception:
            raise FullReadinessError("ATLAS_FULL_CHALLENGE_FINAL_UNAVAILABLE") from None
        if (
            type(checked) is not UnreservedChallengeSnapshot
            or checked.status != "observed_not_reserved"
            or checked.one_shot_consumed is not False
            or checked.prepare_eligible is not False
            or checked.environment != target.environment
            or checked.service_id != target.service_id
            or checked.expires_at != ci.challenge_expires_at
            or checked.observed_at < ci.challenge_checked_at
        ):
            raise FullReadinessError("ATLAS_FULL_CHALLENGE_FINAL_DRIFT")
        return FullReadinessBlocked(
            status="blocked",
            blocks=tuple(dict.fromkeys((
                *ci.blocks, *host_pair.blocks,
                "COLLECTOR_TRANSPORT_IDENTITY_NOT_PROVEN",
                "ROLLBACK_BACKUP_MIGRATIONS_NOT_PROVEN",
                "CORE_PREPARE_GRANT_NOT_CHECKED",
                "ONE_SHOT_CHALLENGE_NOT_CONSUMED",
                "PREPARE_DISABLED",
                "ACT_DISABLED",
            ))),
            environment=target.environment, service_id=target.service_id,
            target_commit_sha=target.target_commit_sha,
            target_image_id=target.target_image_id,
            base_commit_sha=base.commit_sha,
            base_image_id=base.image_id,
            host_id=host.host_id,
            challenge_checked_at=checked.observed_at,
            release_verified_at=ci.release_verified_at,
            runtime_receipt_sha256=host_pair.runtime_receipt_sha256,
            git_receipt_sha256=host_pair.git_receipt_sha256,
        )

"""ATLAS P2.2h.2m: reconcile two separate signed host observations.

This module does NOT attest to a trusted collector or authorize PREPARE/ACT.
It combines the existing Docker-based OCI preflight (already fail-closed)
with the NEW signed Git checkout observation from an independent HMAC key.
Both must bind to exactly the same fresh PostgreSQL-issued challenge.
The database is not accessed and the one-shot nonce is NOT consumed here.
"""
from __future__ import annotations

import hmac
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from .deploy_git_checkout_witness import (
    GitCheckoutWitnessError, verify_git_checkout_witness,
)
from .deploy_host_oci_preflight import (
    HostOCIPreflightError, HostOCIIntentPreview,
    inspect_host_oci_preflight_v2,
)
from .deploy_host_receipt import SignedHostReceipt
from .deploy_host_source import RuntimeTarget

_MAX_GAP = timedelta(seconds=15)
_STILL_UNPROVEN = (
    "GIT_COLLECTOR_IDENTITY_NOT_ATTESTED",
    "GIT_IGNORED_FILES_NOT_MEASURED",
    "GIT_FILESYSTEM_SNAPSHOT_NOT_ATOMIC",
)


class HostEvidenceBundleError(Exception):
    """Finite, sanitized failure codes; no private Git/host bytes."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class HostEvidenceBundleReport:
    """Always blocked, not a Core grant, proposal, candidate or ACT ticket."""

    status: str
    blocks: tuple[str, ...]
    environment: str
    service_id: str
    observed_base_commit_sha: str
    observed_base_image_id: str
    checkout_head_sha: str
    checkout_observed_clean: bool
    host_observed_at: datetime
    checkout_observed_at: datetime
    challenge_sha256: str
    runtime_receipt_sha256: str
    checkout_receipt_sha256: str
    checkout_trust_approved: bool = False
    challenge_consumed: bool = False
    migrations_safe: bool = False
    rollback_ready: bool = False
    prepare_eligible: bool = False


def inspect_signed_host_checkout_bundle(
    *, signed_host: SignedHostReceipt,
    signed_checkout: SignedHostReceipt,
    runtime_host_key: bytes, git_checkout_key: bytes,
    target: RuntimeTarget, intent: HostOCIIntentPreview,
    expected_challenge: str, now: datetime,
) -> HostEvidenceBundleReport:
    """Verify two independent signed observations and reconcile identity.

    Signing credentials, target, intent and challenge must come from trusted
    server-side sources. An API client must never be able to construct them.
    Enforcing a separate checkout key avoids one witness forging the other
    kind of evidence. This is a diagnostic and is always status='blocked'.
    """
    if (
        type(runtime_host_key) is not bytes
        or type(git_checkout_key) is not bytes
        or len(runtime_host_key) < 32
        or len(git_checkout_key) < 32
        or hmac.compare_digest(runtime_host_key, git_checkout_key)
    ):
        raise HostEvidenceBundleError("HOST_BUNDLE_SEPARATE_KEYS_REQUIRED")
    try:
        host = inspect_host_oci_preflight_v2(
            signed_receipt=signed_host, host_key=runtime_host_key,
            target=target, expected_challenge=expected_challenge,
            intent=intent, now=now,
        )
    except HostOCIPreflightError:
        raise HostEvidenceBundleError("HOST_BUNDLE_RUNTIME_NOT_TRUSTED") from None
    except Exception:
        raise HostEvidenceBundleError("HOST_BUNDLE_RUNTIME_UNAVAILABLE") from None

    try:
        git = verify_git_checkout_witness(
            signed_checkout, verification_key=git_checkout_key,
            target=target, expected_challenge=expected_challenge, now=now,
        )
    except GitCheckoutWitnessError:
        raise HostEvidenceBundleError("HOST_BUNDLE_CHECKOUT_NOT_TRUSTED") from None
    except Exception:
        raise HostEvidenceBundleError("HOST_BUNDLE_CHECKOUT_UNAVAILABLE") from None

    if (
        not hmac.compare_digest(host.challenge_sha256, git.challenge_sha256)
        or host.environment != git.environment
        or host.service_id != git.service_id
    ):
        raise HostEvidenceBundleError("HOST_BUNDLE_CHALLENGE_OR_TARGET_DRIFT")
    if host.status != "blocked":
        # A future change in another component MUST NOT silently authorize.
        raise HostEvidenceBundleError("HOST_BUNDLE_RUNTIME_STATUS_INVALID")
    if git.signature_verified is not True or git.challenge_bound is not True:
        raise HostEvidenceBundleError("HOST_BUNDLE_CHECKOUT_NOT_TRUSTED")

    blocks = list(host.blocks)
    blocks.extend(_STILL_UNPROVEN)
    if git.branch != "main":
        blocks.append("GIT_CHECKOUT_BRANCH_NOT_MAIN")
    if not git.observed_clean:
        blocks.append("GIT_CHECKOUT_DIRTY")
    if git.head_sha != host.observed_base_commit_sha:
        blocks.append("GIT_CHECKOUT_RUNTIME_COMMIT_DRIFT")
    if git.head_sha != intent.base_commit_sha:
        blocks.append("GIT_CHECKOUT_EXPECTED_BASE_COMMIT_DRIFT")
    if abs(git.observed_at - host.observed_at) > _MAX_GAP:
        blocks.append("GIT_RUNTIME_OBSERVATION_GAP")

    return HostEvidenceBundleReport(
        status="blocked", blocks=tuple(blocks),
        environment=host.environment, service_id=host.service_id,
        observed_base_commit_sha=host.observed_base_commit_sha,
        observed_base_image_id=host.observed_base_image_id,
        checkout_head_sha=git.head_sha,
        checkout_observed_clean=git.observed_clean,
        host_observed_at=host.observed_at,
        checkout_observed_at=git.observed_at,
        challenge_sha256=host.challenge_sha256,
        runtime_receipt_sha256=host.signed_receipt_sha256,
        checkout_receipt_sha256=git.receipt_sha256,
    )

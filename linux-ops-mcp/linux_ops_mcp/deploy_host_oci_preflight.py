"""ATLAS P2.2h.2k: fail-closed read-only OCI / signed-host preflight.

This internal diagnostic is permanently BLOCKED. It is NOT an MCP tool,
HTTP endpoint, authorization, PREPARE writer, approval, or ACT executor.
The trusted backend must independently own the RuntimeTarget, issue the
one-shot nonce in PostgreSQL, obtain OCI release evidence and confirm Core
identity. Values in an expectation dataclass are *not* authenticated here.
"""
from __future__ import annotations

import hashlib
import hmac
import re
from dataclasses import dataclass
from datetime import datetime

from .deploy_host_receipt import SignedHostReceipt
from .deploy_host_runtime_v2 import (
    HostRuntimeV2Error,
    verify_host_runtime_receipt_v2,
)
from .deploy_host_source import RuntimeTarget, validate_target

_SHA = re.compile(r"[0-9a-f]{40}\Z")
_DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")
_HEX64 = re.compile(r"[0-9a-f]{64}\Z")
# Restrict this preview to the canonical ATLAS pilot service. The signer
# must independently validate the exact runtime target and Compose labels.
_TARGETS: dict[tuple[str, str], tuple[str, str]] = {
    ("hml", "public-hub"): ("delpi-hml-public-hub", "delpi-hml"),
    ("prod", "public-hub"): ("delpi-public-hub", "infra"),
}
_UNPROVEN_GATES = (
    "OCI_CI_RELEASE_NOT_REVERIFIED",
    "OCI_CHECKOUT_NOT_ATTESTED",
    "OCI_MIGRATIONS_NOT_ATTESTED",
    "OCI_ROLLBACK_NOT_ATTESTED",
    "OCI_CHALLENGE_NOT_CONSUMED",
    "OCI_CORE_AUTHORIZATION_MISSING",
)


class HostOCIPreflightError(Exception):
    """One of a finite set of sanitized failures, never upstream bytes."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class HostOCIIntentPreview:
    """Shape-only projection of an OCI intent; never trust a user projection."""

    environment: str
    service_id: str
    base_commit_sha: str
    base_image_id: str
    target_commit_sha: str
    target_image_id: str
    manifest_digest: str
    attestation_statement_sha256: str
    host_challenge_sha256: str
    rollback_image_id: str
    rollback_ready: bool


@dataclass(frozen=True, slots=True)
class HostOCIPreflightReport:
    """Diagnostic, never a candidate, approval, journal receipt or ACT ticket."""

    status: str
    blocks: tuple[str, ...]
    environment: str
    service_id: str
    observed_base_commit_sha: str
    observed_base_image_id: str
    signed_receipt_sha256: str
    challenge_sha256: str
    observed_at: datetime


def _valid_sha(value: object) -> bool:
    return type(value) is str and _SHA.fullmatch(value) is not None


def _valid_digest(value: object) -> bool:
    return type(value) is str and _DIGEST.fullmatch(value) is not None


def _valid_hex(value: object) -> bool:
    return type(value) is str and _HEX64.fullmatch(value) is not None


def _validate_expectation(intent: HostOCIIntentPreview, target: RuntimeTarget) -> None:
    if not validate_target(target):
        raise HostOCIPreflightError("OCI_PREFLIGHT_TARGET_INVALID")
    canonical = _TARGETS.get((target.environment, target.service_id))
    if (
        canonical is None
        or target.container_name != canonical[0]
        or target.compose_project != canonical[1]
    ):
        raise HostOCIPreflightError("OCI_PREFLIGHT_TARGET_NOT_ALLOWLISTED")
    if type(intent) is not HostOCIIntentPreview:
        raise HostOCIPreflightError("OCI_PREFLIGHT_INTENT_INVALID")
    if intent.environment != target.environment or intent.service_id != target.service_id:
        raise HostOCIPreflightError("OCI_PREFLIGHT_INTENT_TARGET_DRIFT")
    if not (
        _valid_sha(intent.base_commit_sha)
        and _valid_sha(intent.target_commit_sha)
        and _valid_digest(intent.base_image_id)
        and _valid_digest(intent.target_image_id)
        and _valid_digest(intent.rollback_image_id)
        and _valid_digest(intent.manifest_digest)
        and _valid_hex(intent.attestation_statement_sha256)
        and _valid_hex(intent.host_challenge_sha256)
        and type(intent.rollback_ready) is bool
    ):
        raise HostOCIPreflightError("OCI_PREFLIGHT_INTENT_INVALID")


def inspect_host_oci_preflight_v2(
    *, signed_receipt: SignedHostReceipt,
    host_key: bytes,
    target: RuntimeTarget,
    expected_challenge: str,
    intent: HostOCIIntentPreview,
    now: datetime,
) -> HostOCIPreflightReport:
    """Verify host receipt internally, then reconcile base image and nonce.

    This function NEVER marks PREPARE eligible. The caller must obtain
    intent/target/nonce/digest from trusted backend and DB queries.
    Concurrence of user-constructed dataclasses cannot establish CI, Core
    permission, checkout, migrations, rollback, or nonce consumption.
    """
    _validate_expectation(intent, target)
    if not _valid_hex(expected_challenge):
        raise HostOCIPreflightError("OCI_PREFLIGHT_CHALLENGE_INVALID")
    if (
        type(now) is not datetime
        or now.tzinfo is None
        or now.utcoffset() is None
    ):
        raise HostOCIPreflightError("OCI_PREFLIGHT_CLOCK_INVALID")

    # Hash the *nonce bytes*, not its ASCII representation, matching the
    # PostgreSQL journal's SHA256(bytes.fromhex(...)) convention.
    expected_digest = hashlib.sha256(bytes.fromhex(expected_challenge)).hexdigest()
    if not hmac.compare_digest(expected_digest, intent.host_challenge_sha256):
        raise HostOCIPreflightError("OCI_PREFLIGHT_CHALLENGE_DIGEST_DRIFT")

    try:
        snapshot = verify_host_runtime_receipt_v2(
            signed_receipt, secret=host_key, target=target,
            expected_challenge=expected_challenge, now=now,
        )
    except HostRuntimeV2Error as exc:
        # Finite code from our in-package verifier, not from untrusted JSON.
        raise HostOCIPreflightError("OCI_PREFLIGHT_HOST_" + exc.code) from None
    except Exception:
        raise HostOCIPreflightError("OCI_PREFLIGHT_HOST_UNAVAILABLE") from None

    if (
        snapshot.signature_verified is not True
        or snapshot.challenge_bound is not True
        or not hmac.compare_digest(snapshot.challenge_sha256, expected_digest)
    ):
        raise HostOCIPreflightError("OCI_PREFLIGHT_HOST_UNTRUSTED")

    # Every report stays blocked even if base image, health and nonce match.
    # These are independent security requirements NOT attested by Docker.
    blocks = list(_UNPROVEN_GATES)
    if snapshot.deployed_commit_sha != intent.base_commit_sha:
        blocks.append("OCI_BASE_COMMIT_DRIFT")
    if snapshot.running_image_id != intent.base_image_id:
        blocks.append("OCI_BASE_IMAGE_DRIFT")
    if not (snapshot.running and snapshot.healthy):
        blocks.append("OCI_HOST_NOT_HEALTHY")
    if intent.target_commit_sha == intent.base_commit_sha:
        blocks.append("OCI_TARGET_ALREADY_DEPLOYED")
    if intent.target_image_id == intent.base_image_id:
        blocks.append("OCI_TARGET_IMAGE_UNCHANGED")
    if intent.rollback_image_id != intent.base_image_id:
        blocks.append("OCI_ROLLBACK_IDENTITY_DRIFT")
    if intent.rollback_ready is not True:
        blocks.append("OCI_ROLLBACK_INTENT_UNREADY")

    return HostOCIPreflightReport(
        status="blocked",
        blocks=tuple(blocks),
        environment=target.environment,
        service_id=target.service_id,
        observed_base_commit_sha=snapshot.deployed_commit_sha,
        observed_base_image_id=snapshot.running_image_id,
        signed_receipt_sha256=snapshot.signed_receipt_sha256,
        challenge_sha256=snapshot.challenge_sha256,
        observed_at=snapshot.observed_at,
    )

"""P2.2c: verify a host-signed release observation, without Docker or shell access.

The signer must be a separate, trusted host collector which reads the LIVE
container image identity and a release record written by an approved executor.
This verifier cannot prove build provenance or migration/rollback readiness.
No signer, secret provisioning, API, or MCP tool is included here.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from .deploy_attestation import HostProof

_REPO = "roberiooliveiradev/delpi-central"
_SERVICE = re.compile(r"[a-z][a-z0-9-]{1,63}\Z")
_SHA = re.compile(r"[0-9a-f]{40}\Z")
_HEX = re.compile(r"[0-9a-f]{64}\Z")
_IMAGE = re.compile(r"sha256:[0-9a-f]{64}\Z")
_MAX_BYTES = 2048
_MAX_AGE = timedelta(seconds=90)
_SKEW = timedelta(seconds=5)
_FIELDS = frozenset((
    "version", "host_id", "repository", "environment", "service_id",
    "commit_sha", "release_image_id", "running_image_id", "container_id",
    "running", "healthy", "checkout_clean", "observed_at", "challenge",
))


class HostReceiptError(Exception):
    """Safe public error codes only. Never include receipt, key or raw JSON."""
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _unique_pairs(pairs: list[tuple[str, object]]) -> dict:
    result: dict = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON field")
        result[key] = value
    return result


def _sha256_hex(value: object) -> bool:
    return type(value) is str and _HEX.fullmatch(value) is not None


def _time(value: object) -> datetime | None:
    if type(value) is not str or not value.endswith("Z") or len(value) > 40:
        return None
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        return None
    return parsed.astimezone(timezone.utc)


@dataclass(frozen=True)
class SignedHostReceipt:
    body: bytes
    mac_hex: str


def verify_host_receipt(
    receipt: SignedHostReceipt, *, secret: bytes, expected_host_id: str,
    expected_environment: str, expected_service_id: str,
    expected_challenge: str, now: datetime,
) -> HostProof:
    """Convert one signed, challenge-bound host observation into a limited proof.

    Challenge MUST be freshly generated and checked/consumed by a future backend
    journal. This module is inert until a trusted signer and backend exist.
    """
    if (type(secret) is not bytes or len(secret) < 32
            or type(expected_host_id) is not str or not expected_host_id
            or expected_environment not in ("hml", "prod")
            or type(expected_service_id) is not str or _SERVICE.fullmatch(expected_service_id) is None
            or not _sha256_hex(expected_challenge)
            or not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None):
        raise HostReceiptError("HOST_VERIFIER_UNCONFIGURED")
    if (not isinstance(receipt, SignedHostReceipt)
            or type(receipt.body) is not bytes or not (1 <= len(receipt.body) <= _MAX_BYTES)
            or not _sha256_hex(receipt.mac_hex)):
        raise HostReceiptError("HOST_RECEIPT_INVALID")

    expected_mac = hmac.new(secret, receipt.body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected_mac, receipt.mac_hex):
        raise HostReceiptError("HOST_SIGNATURE_INVALID")
    try:
        payload = json.loads(receipt.body, object_pairs_hook=_unique_pairs,
                             parse_constant=lambda _: (_ for _ in ()).throw(ValueError("non-finite")))
    except (ValueError, UnicodeDecodeError, TypeError):
        raise HostReceiptError("HOST_RECEIPT_INVALID") from None
    if type(payload) is not dict or frozenset(payload) != _FIELDS:
        raise HostReceiptError("HOST_RECEIPT_INVALID")
    if (type(payload["version"]) is not int or payload["version"] != 1
            or payload["host_id"] != expected_host_id
            or payload["repository"] != _REPO
            or payload["environment"] != expected_environment
            or payload["service_id"] != expected_service_id
            or payload["challenge"] != expected_challenge):
        raise HostReceiptError("HOST_TARGET_MISMATCH")
    if (type(payload["commit_sha"]) is not str or _SHA.fullmatch(payload["commit_sha"]) is None
            or type(payload["release_image_id"]) is not str or _IMAGE.fullmatch(payload["release_image_id"]) is None
            or type(payload["running_image_id"]) is not str or _IMAGE.fullmatch(payload["running_image_id"]) is None
            or not _sha256_hex(payload["container_id"])):
        raise HostReceiptError("HOST_RELEASE_ID_INVALID")
    if payload["release_image_id"] != payload["running_image_id"]:
        raise HostReceiptError("HOST_IMAGE_DRIFT")
    if not all(type(payload[key]) is bool for key in ("running", "healthy", "checkout_clean")):
        raise HostReceiptError("HOST_RECEIPT_INVALID")
    observed_at = _time(payload["observed_at"])
    if observed_at is None:
        raise HostReceiptError("HOST_OBSERVATION_TIME_INVALID")
    age = now.astimezone(timezone.utc) - observed_at
    if age > _MAX_AGE or age < -_SKEW:
        raise HostReceiptError("HOST_OBSERVATION_STALE")
    return HostProof(
        environment=expected_environment, service_id=expected_service_id,
        repository=_REPO, deployed_commit_sha=payload["commit_sha"],
        checkout_clean=payload["checkout_clean"],
        service_healthy=payload["running"] and payload["healthy"],
        # These require separate CI/migration/backup/rollback authority.
        migrations_safe=False, rollback_ready=False, checked_at=observed_at,
    )

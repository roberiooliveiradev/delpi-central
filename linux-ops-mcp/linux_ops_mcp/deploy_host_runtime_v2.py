"""ATLAS P2.2h.2j: target-bound host runtime receipt v2 (INERT).

This module is NOT an MCP tool, endpoint, service, deployment executor or
authorization. It creates an offline versioned host receipt from the existing
release-record verifier and *read-only* Docker inspector, then verifies it.
The host key and target MUST be server-owned. A MAC protects the receipt,
but does not by itself prove safe migrations, git cleanliness or rollback.
No key/transport provisioning or journal nonce consumption happens here.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from .deploy_host_receipt import SignedHostReceipt, _time, _unique_pairs
from .deploy_host_signer import SignedReleaseRecord, issue_host_receipt
from .deploy_host_source import RuntimeInspector, RuntimeTarget, validate_target

_REPOSITORY = "roberiooliveiradev/delpi-central"
_DOMAIN = b"atlas:host-runtime-receipt:v2:\x00"
_HEX64 = re.compile(r"[0-9a-f]{64}\Z")
_SHA40 = re.compile(r"[0-9a-f]{40}\Z")
_IMAGEID = re.compile(r"sha256:[0-9a-f]{64}\Z")
_MAX_BYTES = 3072
_MAX_AGE = timedelta(seconds=90)
_SKEW = timedelta(seconds=5)
_FIELDS = frozenset((
    "version", "host_id", "repository", "environment", "service_id",
    "compose_project", "container_name", "commit_sha", "release_image_id",
    "running_image_id", "container_id", "running", "healthy",
    "checkout_clean", "observed_at", "challenge",
))


class HostRuntimeV2Error(Exception):
    """Finite error codes only; no signed bytes, key, token or upstream data."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class VerifiedHostRuntimeSnapshot:
    """Signed live-image observation, deliberately NOT a PREPARE permission."""

    host_id: str
    environment: str
    service_id: str
    compose_project: str
    container_name: str
    deployed_commit_sha: str
    running_image_id: str
    container_id: str
    observed_at: datetime
    challenge_sha256: str
    signed_receipt_sha256: str
    running: bool
    healthy: bool
    signature_verified: bool
    challenge_bound: bool
    checkout_clean: bool
    migrations_safe: bool
    rollback_ready: bool
    challenge_consumed: bool


def _valid_challenge(challenge: object) -> bool:
    return type(challenge) is str and _HEX64.fullmatch(challenge) is not None


async def issue_host_runtime_receipt_v2(
    *, target: RuntimeTarget, release_record: SignedReleaseRecord,
    inspector: RuntimeInspector, release_key: bytes, host_key: bytes,
    challenge: str, now: datetime,
) -> SignedHostReceipt:
    """Sign container/project identity along with existing Docker facts.

    The existing trusted signer verifies the separately sealed release
    record and reads the exact Docker container through a restricted
    inspector. It always sets checkout_clean=False, intentionally.
    This signer is not exposed to the ChatGPT-facing MCP process.
    """
    legacy = await issue_host_receipt(
        target=target, release_record=release_record,
        inspector=inspector, release_key=release_key, host_key=host_key,
        challenge=challenge, now=now,
    )
    # This JSON is created locally by issue_host_receipt above, not supplied
    # by a caller. Its immutable bytes are never returned from the verifier.
    fields = json.loads(legacy.body)
    fields["version"] = 2
    fields["compose_project"] = target.compose_project
    fields["container_name"] = target.container_name
    body = json.dumps(
        fields, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    ).encode("utf-8")
    return SignedHostReceipt(
        body, hmac.new(host_key, _DOMAIN + body, hashlib.sha256).hexdigest(),
    )


def verify_host_runtime_receipt_v2(
    receipt: SignedHostReceipt, *, secret: bytes, target: RuntimeTarget,
    expected_challenge: str, now: datetime,
) -> VerifiedHostRuntimeSnapshot:
    """Authenticate v2 host/container/project + challenge without DB writes.

    The expected target and nonce must come from server-side policy and a
    freshly issued journal challenge, NEVER from receipt/HTTP/MCP input.
    A match does not mean the one-shot challenge has been consumed.
    """
    if (not validate_target(target) or type(secret) is not bytes or len(secret) < 32
            or not _valid_challenge(expected_challenge)
            or type(now) is not datetime or now.tzinfo is None
            or now.utcoffset() is None):
        raise HostRuntimeV2Error("HOST_V2_VERIFIER_UNCONFIGURED")
    if (type(receipt) is not SignedHostReceipt
            or type(receipt.body) is not bytes
            or not (1 <= len(receipt.body) <= _MAX_BYTES)
            or type(receipt.mac_hex) is not str
            or _HEX64.fullmatch(receipt.mac_hex) is None):
        raise HostRuntimeV2Error("HOST_V2_RECEIPT_INVALID")

    mac = hmac.new(secret, _DOMAIN + receipt.body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(mac, receipt.mac_hex):
        raise HostRuntimeV2Error("HOST_V2_SIGNATURE_INVALID")
    try:
        fields = json.loads(
            receipt.body, object_pairs_hook=_unique_pairs,
            parse_constant=lambda _: (_ for _ in ()).throw(ValueError("non-finite JSON")),
        )
    except (ValueError, UnicodeError, TypeError):
        raise HostRuntimeV2Error("HOST_V2_RECEIPT_INVALID") from None
    if type(fields) is not dict or frozenset(fields) != _FIELDS:
        raise HostRuntimeV2Error("HOST_V2_RECEIPT_INVALID")

    if (type(fields["version"]) is not int or fields["version"] != 2
            or fields["repository"] != _REPOSITORY
            or fields["host_id"] != target.host_id
            or fields["environment"] != target.environment
            or fields["service_id"] != target.service_id
            or fields["compose_project"] != target.compose_project
            or fields["container_name"] != target.container_name
            or type(fields["challenge"]) is not str
            or not hmac.compare_digest(fields["challenge"], expected_challenge)):
        raise HostRuntimeV2Error("HOST_V2_TARGET_MISMATCH")

    if (type(fields["commit_sha"]) is not str
            or _SHA40.fullmatch(fields["commit_sha"]) is None
            or type(fields["release_image_id"]) is not str
            or _IMAGEID.fullmatch(fields["release_image_id"]) is None
            or type(fields["running_image_id"]) is not str
            or _IMAGEID.fullmatch(fields["running_image_id"]) is None
            or type(fields["container_id"]) is not str
            or _HEX64.fullmatch(fields["container_id"]) is None):
        raise HostRuntimeV2Error("HOST_V2_IMAGE_INVALID")
    if fields["release_image_id"] != fields["running_image_id"]:
        raise HostRuntimeV2Error("HOST_V2_IMAGE_DRIFT")
    if any(type(fields[key]) is not bool
           for key in ("running", "healthy", "checkout_clean")):
        raise HostRuntimeV2Error("HOST_V2_RECEIPT_INVALID")
    if fields["checkout_clean"] is not False:
        # The existing Docker-only signer cannot prove git workspace state.
        # Deny even a validly MACed forged claim that checkout is clean.
        raise HostRuntimeV2Error("HOST_V2_CHECKOUT_NOT_ATTESTED")
    observed_at = _time(fields["observed_at"])
    if observed_at is None:
        raise HostRuntimeV2Error("HOST_V2_OBSERVATION_INVALID")
    age = now.astimezone(timezone.utc) - observed_at
    if age < -_SKEW or age > _MAX_AGE:
        raise HostRuntimeV2Error("HOST_V2_OBSERVATION_STALE")

    return VerifiedHostRuntimeSnapshot(
        host_id=target.host_id, environment=target.environment,
        service_id=target.service_id,
        compose_project=target.compose_project,
        container_name=target.container_name,
        deployed_commit_sha=fields["commit_sha"],
        running_image_id=fields["running_image_id"],
        container_id=fields["container_id"], observed_at=observed_at,
        challenge_sha256=hashlib.sha256(
            bytes.fromhex(expected_challenge),
        ).hexdigest(),
        signed_receipt_sha256=hashlib.sha256(receipt.body).hexdigest(),
        running=fields["running"], healthy=fields["healthy"],
        signature_verified=True, challenge_bound=True,
        checkout_clean=False, migrations_safe=False, rollback_ready=False,
        challenge_consumed=False,
    )

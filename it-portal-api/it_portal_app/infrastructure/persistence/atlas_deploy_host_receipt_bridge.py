"""ATLAS P2.2h.2s: backend-only verification of both Linux host receipts.

This is a strict *wire contract* between the Linux collector and Portal TI.
Only the backend holds the two independently provisioned host keys and pins
host/target. Receipt HMAC proves payload integrity, NOT the host collector's
OS identity, git snapshot atomicity, backup safety, approval or nonce use.
No network, DB write, route, MCP tool, Docker socket or deploy operation.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

_REPO = "roberiooliveiradev/delpi-central"
_RUNTIME_DOMAIN = b"atlas:host-runtime-receipt:v2:\x00"
_GIT_DOMAIN = b"atlas:git-checkout-observation:v1:\x00"
_SHA = re.compile(r"[0-9a-f]{40}\Z")
_HEX = re.compile(r"[0-9a-f]{64}\Z")
_IMAGE = re.compile(r"sha256:[0-9a-f]{64}\Z")
_ID = re.compile(r"[a-z0-9][a-z0-9_.-]{1,100}\Z")
_BRANCH = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9._/-]{0,127}\Z")
_MAX_RECEIPT_BYTES = 3072
_MAX_AGE = timedelta(seconds=90)
_MAX_SKEW = timedelta(seconds=5)
_MAX_GAP = timedelta(seconds=15)
_CONTAINER = {
    "hml": ("delpi-hml-public-hub", "delpi-hml"),
    "prod": ("delpi-public-hub", "infra"),
}
_RUNTIME_FIELDS = frozenset({
    "version", "host_id", "repository", "environment", "service_id",
    "compose_project", "container_name", "commit_sha", "release_image_id",
    "running_image_id", "container_id", "running", "healthy",
    "checkout_clean", "observed_at", "challenge",
})
_GIT_FIELDS = frozenset({
    "version", "repository", "host_id", "environment", "service_id",
    "compose_project", "container_name", "branch", "head_sha",
    "tracked_and_untracked_clean", "observation_scope", "observed_at",
    "challenge",
})


class HostReceiptBridgeError(Exception):
    """Finite sanitized error codes. Never echo key, nonce or raw receipt."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class SignedReceiptWire:
    body: bytes
    mac_hex: str


@dataclass(frozen=True, slots=True)
class PinnedHostTarget:
    """Obtained only from BFF infrastructure configuration, not request JSON."""

    host_id: str
    environment: str
    service_id: str
    container_name: str
    compose_project: str


@dataclass(frozen=True, slots=True)
class ExpectedBaseRelease:
    """Exact base revision from authenticated backend journal/intent readback."""

    commit_sha: str
    image_id: str


@dataclass(frozen=True, slots=True)
class VerifiedWireHostPair:
    """Two valid HMACs, NOT an independently trusted host/checkout witness."""

    host_id: str
    environment: str
    service_id: str
    base_commit_sha: str
    base_image_id: str
    git_head_sha: str
    branch: str
    running: bool
    healthy: bool
    git_observed_clean: bool
    runtime_observed_at: datetime
    git_observed_at: datetime
    challenge_digest: str
    runtime_receipt_sha256: str
    git_receipt_sha256: str
    blocks: tuple[str, ...]
    signature_integrity_verified: bool = True
    collector_identity_attested: bool = False
    checkout_integrity_attested: bool = False
    challenge_consumed: bool = False
    prepare_eligible: bool = False


def _hex64(value: object) -> bool:
    return type(value) is str and _HEX.fullmatch(value) is not None


def _sha40(value: object) -> bool:
    return type(value) is str and _SHA.fullmatch(value) is not None


def _image(value: object) -> bool:
    return type(value) is str and _IMAGE.fullmatch(value) is not None


def _aware(value: object) -> bool:
    return (
        type(value) is datetime
        and value.tzinfo is not None
        and value.utcoffset() is not None
    )


def _timestamp(value: object, now: datetime) -> datetime:
    if type(value) is not str or not value.endswith("Z") or len(value) > 40:
        raise HostReceiptBridgeError("ATLAS_HOST_TIME_INVALID")
    try:
        ts = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        raise HostReceiptBridgeError("ATLAS_HOST_TIME_INVALID") from None
    if not _aware(ts) or ts.utcoffset() != timedelta(0):
        raise HostReceiptBridgeError("ATLAS_HOST_TIME_INVALID")
    age = now.astimezone(timezone.utc) - ts.astimezone(timezone.utc)
    if age < -_MAX_SKEW or age > _MAX_AGE:
        raise HostReceiptBridgeError("ATLAS_HOST_RECEIPT_STALE")
    return ts.astimezone(timezone.utc)


def _unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    out: dict[str, object] = {}
    for k, v in pairs:
        if k in out:
            raise ValueError("duplicate JSON key")
        out[k] = v
    return out


def _verify(
    receipt: SignedReceiptWire,
    *,
    key: bytes,
    domain: bytes,
    fields: frozenset[str],
    version: int,
    target: PinnedHostTarget,
    nonce: str,
) -> dict[str, object]:
    if (
        type(receipt) is not SignedReceiptWire
        or type(receipt.body) is not bytes
        or not 1 <= len(receipt.body) <= _MAX_RECEIPT_BYTES
        or not _hex64(receipt.mac_hex)
    ):
        raise HostReceiptBridgeError("ATLAS_HOST_RECEIPT_INVALID")
    mac = hmac.new(key, domain + receipt.body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(mac, receipt.mac_hex):
        raise HostReceiptBridgeError("ATLAS_HOST_SIGNATURE_INVALID")
    try:
        doc = json.loads(
            receipt.body, object_pairs_hook=_unique,
            parse_constant=lambda _: (_ for _ in ()).throw(ValueError("non-finite")),
        )
    except (UnicodeError, TypeError, ValueError):
        raise HostReceiptBridgeError("ATLAS_HOST_RECEIPT_INVALID") from None
    if type(doc) is not dict or frozenset(doc) != fields:
        raise HostReceiptBridgeError("ATLAS_HOST_RECEIPT_INVALID")
    if (
        type(doc["version"]) is not int
        or doc["version"] != version
        or doc["repository"] != _REPO
        or doc["host_id"] != target.host_id
        or doc["environment"] != target.environment
        or doc["service_id"] != target.service_id
        or doc["container_name"] != target.container_name
        or doc["compose_project"] != target.compose_project
        or type(doc["challenge"]) is not str
        or not hmac.compare_digest(doc["challenge"], nonce)
    ):
        raise HostReceiptBridgeError("ATLAS_HOST_TARGET_OR_NONCE_DRIFT")
    return doc


def verify_host_receipt_pair(
    *, runtime_receipt: SignedReceiptWire,
    git_receipt: SignedReceiptWire,
    runtime_key: bytes,
    git_key: bytes,
    target: PinnedHostTarget,
    base: ExpectedBaseRelease,
    nonce: str,
    now: datetime,
) -> VerifiedWireHostPair:
    """Check both signatures, same nonce, same host, base SHA/ImageID and age.

    This operation intentionally returns only blocked readiness diagnostics.
    The keys and target MUST be pinned in a trusted backend, and the nonce
    MUST originate from a Core-authorized, PostgreSQL-issued challenge.
    """
    if (
        type(target) is not PinnedHostTarget
        or type(target.host_id) is not str or _ID.fullmatch(target.host_id) is None
        or type(target.environment) is not str
        or target.environment not in _CONTAINER
        or type(target.service_id) is not str
        or target.service_id != "public-hub"
        or type(target.container_name) is not str
        or type(target.compose_project) is not str
        or (target.container_name, target.compose_project) != _CONTAINER[target.environment]
        or type(base) is not ExpectedBaseRelease
        or not _sha40(base.commit_sha)
        or not _image(base.image_id)
        or not _hex64(nonce)
        or not _aware(now)
        or type(runtime_key) is not bytes or len(runtime_key) < 32
        or type(git_key) is not bytes or len(git_key) < 32
        or hmac.compare_digest(runtime_key, git_key)
    ):
        raise HostReceiptBridgeError("ATLAS_HOST_BRIDGE_UNCONFIGURED")

    runtime = _verify(
        runtime_receipt, key=runtime_key, domain=_RUNTIME_DOMAIN,
        fields=_RUNTIME_FIELDS, version=2, target=target, nonce=nonce,
    )
    git = _verify(
        git_receipt, key=git_key, domain=_GIT_DOMAIN,
        fields=_GIT_FIELDS, version=1, target=target, nonce=nonce,
    )
    if (
        not _sha40(runtime["commit_sha"])
        or not _image(runtime["running_image_id"])
        or not _image(runtime["release_image_id"])
        or not _hex64(runtime["container_id"])
        or runtime["running_image_id"] != runtime["release_image_id"]
    ):
        raise HostReceiptBridgeError("ATLAS_HOST_RUNTIME_INVALID")
    if (
        runtime["commit_sha"] != base.commit_sha
        or runtime["running_image_id"] != base.image_id
    ):
        raise HostReceiptBridgeError("ATLAS_HOST_BASE_DRIFT")
    if (
        type(runtime["running"]) is not bool
        or type(runtime["healthy"]) is not bool
        or type(runtime["checkout_clean"]) is not bool
        or runtime["checkout_clean"] is not False
    ):
        raise HostReceiptBridgeError("ATLAS_HOST_RUNTIME_INVALID")
    if (
        not _sha40(git["head_sha"])
        or type(git["branch"]) is not str
        or _BRANCH.fullmatch(git["branch"]) is None
        or type(git["tracked_and_untracked_clean"]) is not bool
        or git["observation_scope"] != "tracked_and_untracked_nonignored"
    ):
        raise HostReceiptBridgeError("ATLAS_HOST_GIT_INVALID")

    runtime_at = _timestamp(runtime["observed_at"], now)
    git_at = _timestamp(git["observed_at"], now)
    blocks: list[str] = [
        "HOST_COLLECTOR_IDENTITY_NOT_ATTESTED",
        "GIT_IGNORED_FILES_NOT_ATTESTED",
        "GIT_FILESYSTEM_NOT_ATOMIC",
        "CHALLENGE_NOT_CONSUMED",
    ]
    if git["head_sha"] != runtime["commit_sha"]:
        blocks.append("GIT_RUNTIME_COMMIT_DRIFT")
    if git["branch"] != "main":
        blocks.append("GIT_CHECKOUT_NOT_MAIN")
    if git["tracked_and_untracked_clean"] is not True:
        blocks.append("GIT_CHECKOUT_DIRTY")
    if not (runtime["running"] and runtime["healthy"]):
        blocks.append("HOST_RUNTIME_UNHEALTHY")
    if abs(runtime_at - git_at) > _MAX_GAP:
        blocks.append("HOST_GIT_OBSERVATION_GAP")

    return VerifiedWireHostPair(
        host_id=target.host_id,
        environment=target.environment,
        service_id=target.service_id,
        base_commit_sha=base.commit_sha,
        base_image_id=base.image_id,
        git_head_sha=git["head_sha"],
        branch=git["branch"],
        running=runtime["running"],
        healthy=runtime["healthy"],
        git_observed_clean=git["tracked_and_untracked_clean"],
        runtime_observed_at=runtime_at,
        git_observed_at=git_at,
        challenge_digest=hashlib.sha256(bytes.fromhex(nonce)).hexdigest(),
        runtime_receipt_sha256=hashlib.sha256(runtime_receipt.body).hexdigest(),
        git_receipt_sha256=hashlib.sha256(git_receipt.body).hexdigest(),
        blocks=tuple(blocks),
    )

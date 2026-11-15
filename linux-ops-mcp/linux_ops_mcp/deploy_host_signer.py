"""P2.2d: offline host signer bound to an executor-sealed release and Docker GET.

Not an MCP tool, executable, CLI, endpoint, service unit, or key generator.
HML-only pilot must provide: a trusted release record signed by the separate
executor, a narrow read-only inspector, and two distinct externally managed
secret keys. By design, this proof NEVER sets checkout/migration/rollback true.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Protocol
from uuid import UUID

from .deploy_host_receipt import SignedHostReceipt
from .deploy_host_source import RuntimeInspector, RuntimeTarget, RuntimeContainer, HostSourceError, validate_target

_REPO = "roberiooliveiradev/delpi-central"
_HEX = re.compile(r"[a-f0-9]{64}\Z")
_SHA = re.compile(r"[a-f0-9]{40}\Z")
_IMAGE = re.compile(r"sha256:[a-f0-9]{64}\Z")
_RECORD_FIELDS = frozenset((
    "version", "repository", "host_id", "environment", "service_id",
    "execution_id", "commit_sha", "image_id",
))
_MAX_MANIFEST = 1024
_DOMAIN = b"atlas:executor-release-record:v1:\x00"


class HostSigningError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class SignedReleaseRecord:
    body: bytes
    mac_hex: str


def _object_unique(pairs: list[tuple[str, object]]) -> dict:
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError("duplicate json key")
        out[key] = value
    return out


def _valid_hex(x: object) -> bool:
    return type(x) is str and _HEX.fullmatch(x) is not None


def _valid_uuid4(x: object) -> bool:
    if type(x) is not str:
        return False
    try:
        u = UUID(x)
    except (ValueError, AttributeError):
        return False
    return u.version == 4 and str(u) == x


def verify_release_record(record: SignedReleaseRecord, *, key: bytes, target: RuntimeTarget) -> dict:
    if (not validate_target(target) or type(key) is not bytes or len(key) < 32):
        raise HostSigningError("SIGNER_NOT_CONFIGURED")
    if (not isinstance(record, SignedReleaseRecord) or type(record.body) is not bytes
            or len(record.body) < 2 or len(record.body) > _MAX_MANIFEST
            or not _valid_hex(record.mac_hex)):
        raise HostSigningError("RELEASE_RECORD_INVALID")
    expected = hmac.new(key, _DOMAIN + record.body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, record.mac_hex):
        raise HostSigningError("RELEASE_RECORD_UNTRUSTED")
    try:
        obj = json.loads(record.body, object_pairs_hook=_object_unique,
                         parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite")))
    except (ValueError, TypeError, UnicodeDecodeError):
        raise HostSigningError("RELEASE_RECORD_INVALID") from None
    if type(obj) is not dict or frozenset(obj) != _RECORD_FIELDS:
        raise HostSigningError("RELEASE_RECORD_INVALID")
    if (type(obj["version"]) is not int or obj["version"] != 1
            or obj["repository"] != _REPO or obj["host_id"] != target.host_id
            or obj["environment"] != target.environment or obj["service_id"] != target.service_id):
        raise HostSigningError("RELEASE_RECORD_TARGET_MISMATCH")
    if (not _valid_uuid4(obj["execution_id"]) or type(obj["commit_sha"]) is not str
            or _SHA.fullmatch(obj["commit_sha"]) is None
            or type(obj["image_id"]) is not str or _IMAGE.fullmatch(obj["image_id"]) is None):
        raise HostSigningError("RELEASE_RECORD_INVALID")
    return obj


async def issue_host_receipt(
    *, target: RuntimeTarget, release_record: SignedReleaseRecord,
    inspector: RuntimeInspector, release_key: bytes, host_key: bytes,
    challenge: str, now: datetime,
) -> SignedHostReceipt:
    """Get one running container's image ID and sign a restricted observation.

    Caller must enforce one-shot challenges in the PostgreSQL journal; signing
    without that independent check does NOT prevent replay.
    """
    if (not validate_target(target) or not _valid_hex(challenge)
            or type(release_key) is not bytes or len(release_key) < 32
            or type(host_key) is not bytes or len(host_key) < 32
            or hmac.compare_digest(release_key, host_key)
            or not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None):
        raise HostSigningError("SIGNER_NOT_CONFIGURED")
    record = verify_release_record(release_record, key=release_key, target=target)
    try:
        running = await inspector.inspect(target)
    except HostSourceError:
        raise HostSigningError("RUNTIME_INSPECTION_FAILED") from None
    except Exception:
        # The exception may include secrets or raw Docker inspect JSON.
        raise HostSigningError("RUNTIME_INSPECTION_FAILED") from None
    if (not isinstance(running, RuntimeContainer)
            or type(running.running) is not bool or type(running.healthy) is not bool
            or type(running.image_id) is not str or _IMAGE.fullmatch(running.image_id) is None
            or not _valid_hex(running.container_id)):
        raise HostSigningError("RUNTIME_OBSERVATION_INVALID")
    if (running.image_id != record["image_id"]):
        raise HostSigningError("RUNNING_IMAGE_NOT_APPROVED")
    observed = now.astimezone(timezone.utc)
    body = {
        "version": 1, "host_id": target.host_id, "repository": _REPO,
        "environment": target.environment, "service_id": target.service_id,
        "commit_sha": record["commit_sha"],
        "release_image_id": record["image_id"],
        "running_image_id": running.image_id,
        "container_id": running.container_id,
        "running": running.running, "healthy": running.healthy,
        # Docker does not attest to git working-tree state.
        "checkout_clean": False,
        "observed_at": observed.isoformat(timespec="seconds").replace("+00:00", "Z"),
        "challenge": challenge,
    }
    encoded = json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return SignedHostReceipt(encoded, hmac.new(host_key, encoded, hashlib.sha256).hexdigest())

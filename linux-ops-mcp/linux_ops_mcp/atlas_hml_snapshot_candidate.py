"""Provisional ATLAS HML snapshot contract for architecture review ONLY.

Pure parser and validator. No Docker, filesystem, socket, Keycloak, Git,
subprocess, HTTP, service, authorization, PREPARE or ACT integration.
A parsed snapshot is NEVER independent proof of its producer or host.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

_SCHEMA = "atlas.hml.inspect.v1"
_SOURCE = "root-one-shot-snapshot-claim-untrusted"
_ENVIRONMENT = "hml"
_PROJECT = "delpi-hml"
_SERVICE = "public-hub"
_CONTAINER = "delpi-hml-public-hub"
_HEX64 = re.compile(r"[0-9a-f]{64}\Z")
_IMAGE = re.compile(r"sha256:[0-9a-f]{64}\Z")
_UTC_TS = re.compile(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{1,6})?Z\Z")
_MAX_PAYLOAD = 2048
_MAX_AGE = timedelta(seconds=60)
_MAX_FUTURE_SKEW = timedelta(seconds=5)
_FIELDS = frozenset({
    "schema", "source", "environment", "compose_project",
    "service_id", "container_name", "container_id", "image_id",
    "running", "healthy", "observed_at",
})
_ALWAYS_BLOCKED = (
    "SNAPSHOT_ORIGIN_NOT_INDEPENDENTLY_ATTESTED",
    "SNAPSHOT_FILE_DAC_AND_ATOMICITY_NOT_ATTESTED",
    "UPSTREAM_DOCKER_PRIVILEGE_NOT_INDEPENDENTLY_ATTESTED",
    "SNAPSHOT_TIMESTAMP_CLAIM_ONLY",
    "HML_PROXY_POLICY_NOT_INDEPENDENTLY_ATTESTED",
    "HOST_OS_IDENTITY_NOT_ATTESTED",
    "JOURNAL_CHALLENGE_NOT_CONSUMED",
    "BACKUP_RESTORE_AND_ROLLBACK_NOT_ATTESTED",
    "CORE_PREPARE_NOT_AUTHORIZED",
    "PREPARE_DISABLED",
    "ACT_DISABLED",
)


class SnapshotContractError(ValueError):
    """A finite, sanitized error code, never the supplied data."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class SnapshotDiagnostic:
    status: str
    environment: str
    service_id: str
    container_id: str
    image_id: str
    running: bool
    healthy: bool
    observed_at_untrusted: str
    blocks: tuple[str, ...]
    snapshot_origin_attested: bool = False
    docker_access_boundary_attested: bool = False
    proxy_policy_independently_attested: bool = False
    host_identity_attested: bool = False
    checkout_integrity_attested: bool = False
    challenge_consumed: bool = False
    prepare_eligible: bool = False
    can_execute: bool = False


def _no_duplicate_fields(pairs: list[tuple[str, object]]) -> dict[str, object]:
    out: dict[str, object] = {}
    for key, value in pairs:
        if key in out:
            raise SnapshotContractError("HML_SNAPSHOT_DUPLICATE_FIELD")
        out[key] = value
    return out


def _no_constants(_: str) -> object:
    raise SnapshotContractError("HML_SNAPSHOT_JSON_INVALID")


def review_untrusted_snapshot(raw: bytes, *, now: datetime) -> SnapshotDiagnostic:
    """Validate shape/freshness claims without trusting or opening the origin.

    This is not an authorization or cryptographic verification function.
    All input fields are untrusted even when the parser accepts them.
    """
    if (
        type(raw) is not bytes
        or not 1 <= len(raw) <= _MAX_PAYLOAD
        or b"\x00" in raw
        or type(now) is not datetime
        or now.tzinfo is None
        or now.utcoffset() is None
    ):
        raise SnapshotContractError("HML_SNAPSHOT_INPUT_INVALID")
    try:
        document = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_no_duplicate_fields,
            parse_constant=_no_constants,
        )
    except SnapshotContractError:
        raise
    except (ValueError, UnicodeError, TypeError, RecursionError):
        raise SnapshotContractError("HML_SNAPSHOT_JSON_INVALID") from None

    if type(document) is not dict or set(document) != _FIELDS:
        raise SnapshotContractError("HML_SNAPSHOT_SCHEMA_INVALID")

    claims = {
        "schema": _SCHEMA,
        "source": _SOURCE,
        "environment": _ENVIRONMENT,
        "compose_project": _PROJECT,
        "service_id": _SERVICE,
        "container_name": _CONTAINER,
    }
    if any(type(document[k]) is not str or document[k] != v for k, v in claims.items()):
        raise SnapshotContractError("HML_SNAPSHOT_TARGET_DENIED")

    container_id = document["container_id"]
    image_id = document["image_id"]
    if (
        type(container_id) is not str
        or _HEX64.fullmatch(container_id) is None
        or type(image_id) is not str
        or _IMAGE.fullmatch(image_id) is None
        or type(document["running"]) is not bool
        or type(document["healthy"]) is not bool
    ):
        raise SnapshotContractError("HML_SNAPSHOT_CONTENT_INVALID")

    timestamp = document["observed_at"]
    if type(timestamp) is not str or _UTC_TS.fullmatch(timestamp) is None:
        raise SnapshotContractError("HML_SNAPSHOT_TIMESTAMP_INVALID")
    try:
        moment = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        raise SnapshotContractError("HML_SNAPSHOT_TIMESTAMP_INVALID") from None
    age = now.astimezone(timezone.utc) - moment
    if not -_MAX_FUTURE_SKEW <= age <= _MAX_AGE:
        raise SnapshotContractError("HML_SNAPSHOT_EXPIRED_OR_FUTURE")

    blocks = list(_ALWAYS_BLOCKED)
    if not document["running"] or not document["healthy"]:
        blocks.append("HML_CONTAINER_NOT_HEALTHY")

    return SnapshotDiagnostic(
        status="blocked",
        environment="hml",
        service_id="public-hub",
        container_id=container_id,
        image_id=image_id,
        running=document["running"],
        healthy=document["healthy"],
        observed_at_untrusted=timestamp,
        blocks=tuple(blocks),
    )

"""Versioned HML snapshot envelope for architecture B (source-only).

Wraps an already-validated inspect claim with generation, target identity and
content digest. This is NOT independent authenticity: a compromised root
producer that also holds signing material can forge envelopes. Legacy bare
JSON claims are never accepted as authenticated envelopes.
"""
from __future__ import annotations

import base64
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone

from .atlas_hml_snapshot_candidate import (
    SnapshotContractError,
    SnapshotDiagnostic,
    review_untrusted_snapshot,
)

_SCHEMA = "atlas.hml.snapshot-envelope.v1"
_TARGET_ENV = "hml"
_TARGET_PROJECT = "delpi-hml"
_TARGET_SERVICE = "public-hub"
_TARGET_CONTAINER = "delpi-hml-public-hub"
_HEX64 = re.compile(r"[0-9a-f]{64}\Z")
_KEY_ID = re.compile(r"[0-9a-f]{16,64}\Z")
_UTC_TS = re.compile(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{1,6})?Z\Z")
_MAX_ENVELOPE = 8192
_MAX_GENERATION = 2**63 - 1
_FIELDS = frozenset({
    "schema", "environment", "compose_project", "service_id",
    "container_name", "generation", "produced_at", "payload_sha256",
    "payload_b64", "key_id", "signature_b64",
})
_BLOCKS = (
    "ENVELOPE_ORIGIN_BOUND_TO_PRODUCER_KEY_DOMAIN",
    "ROOT_PRODUCER_WITH_KEY_ACCESS_CAN_FORGE",
    "LEGACY_BARE_JSON_NOT_AUTHENTICATED",
    "SEC_01_TO_10_PENDING",
    "PREPARE_DISABLED",
    "ACT_DISABLED",
)


class HMLSnapshotEnvelopeError(ValueError):
    """Finite sanitized code; never echo raw envelope bytes."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class HMLSnapshotEnvelopeReview:
    diagnostic: SnapshotDiagnostic
    generation: int
    produced_at: datetime
    payload_sha256: str
    key_id: str
    signed_message: bytes
    signature: bytes
    status: str = "blocked"
    envelope_schema_ok: bool = True
    authenticity_independent: bool = False
    prepare_eligible: bool = False
    can_execute: bool = False
    blocks: tuple[str, ...] = _BLOCKS


def _unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    out: dict[str, object] = {}
    for key, value in pairs:
        if key in out:
            raise HMLSnapshotEnvelopeError("HML_ENVELOPE_DUPLICATE_FIELD")
        out[key] = value
    return out


def _reject_constant(_: str) -> object:
    raise HMLSnapshotEnvelopeError("HML_ENVELOPE_JSON_INVALID")


def signing_message(
    *,
    generation: int,
    produced_at: str,
    payload_sha256: str,
    key_id: str,
    payload: bytes,
) -> bytes:
    """Canonical bytes covered by Ed25519; domain-separated."""
    if (
        type(generation) is not int or not 1 <= generation <= _MAX_GENERATION
        or type(produced_at) is not str or _UTC_TS.fullmatch(produced_at) is None
        or type(payload_sha256) is not str or _HEX64.fullmatch(payload_sha256) is None
        or type(key_id) is not str or _KEY_ID.fullmatch(key_id) is None
        or type(payload) is not bytes or not payload
    ):
        raise HMLSnapshotEnvelopeError("HML_ENVELOPE_SIGNING_INPUT_INVALID")
    header = {
        "schema": _SCHEMA,
        "environment": _TARGET_ENV,
        "compose_project": _TARGET_PROJECT,
        "service_id": _TARGET_SERVICE,
        "container_name": _TARGET_CONTAINER,
        "generation": generation,
        "produced_at": produced_at,
        "payload_sha256": payload_sha256,
        "key_id": key_id,
    }
    encoded = json.dumps(
        header, separators=(",", ":"), sort_keys=True, ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    return b"atlas.hml.snapshot-envelope.v1\x00" + encoded + b"\x00" + payload


def build_unsigned_envelope_document(
    payload: bytes, *, generation: int, produced_at: datetime, key_id: str,
) -> dict[str, object]:
    """Build envelope fields without signature; caller must sign separately."""
    if (
        type(payload) is not bytes or not 1 <= len(payload) <= 2048
        or b"\x00" in payload
        or type(generation) is not int or not 1 <= generation <= _MAX_GENERATION
        or type(produced_at) is not datetime or produced_at.tzinfo is None
        or produced_at.utcoffset() is None
        or type(key_id) is not str or _KEY_ID.fullmatch(key_id) is None
    ):
        raise HMLSnapshotEnvelopeError("HML_ENVELOPE_BUILD_INPUT_INVALID")
    stamp = (
        produced_at.astimezone(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
    digest = hashlib.sha256(payload).hexdigest()
    return {
        "schema": _SCHEMA,
        "environment": _TARGET_ENV,
        "compose_project": _TARGET_PROJECT,
        "service_id": _TARGET_SERVICE,
        "container_name": _TARGET_CONTAINER,
        "generation": generation,
        "produced_at": stamp,
        "payload_sha256": digest,
        "payload_b64": base64.b64encode(payload).decode("ascii"),
        "key_id": key_id,
        "signature_b64": "",
    }


def seal_envelope_document(
    document: dict[str, object], *, signature: bytes,
) -> bytes:
    """Serialize a fully signed envelope; refuse empty/oversized signatures."""
    if (
        type(document) is not dict or set(document) != _FIELDS
        or type(signature) is not bytes or not 64 <= len(signature) <= 128
    ):
        raise HMLSnapshotEnvelopeError("HML_ENVELOPE_SEAL_INPUT_INVALID")
    sealed = dict(document)
    sealed["signature_b64"] = base64.b64encode(signature).decode("ascii")
    raw = json.dumps(
        sealed, separators=(",", ":"), sort_keys=True, ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    if not 1 <= len(raw) <= _MAX_ENVELOPE:
        raise HMLSnapshotEnvelopeError("HML_ENVELOPE_SEAL_INPUT_INVALID")
    return raw


def review_snapshot_envelope(raw: bytes, *, now: datetime) -> HMLSnapshotEnvelopeReview:
    """Parse/validate envelope shape and inner claim; does NOT verify signature.

    Signature verification belongs to atlas_hml_b_snapshot_trust. Legacy bare
    inspect JSON is rejected here (wrong schema), never silently upgraded.
    """
    if (
        type(raw) is not bytes or not 1 <= len(raw) <= _MAX_ENVELOPE
        or b"\x00" in raw
        or type(now) is not datetime or now.tzinfo is None
        or now.utcoffset() is None
    ):
        raise HMLSnapshotEnvelopeError("HML_ENVELOPE_INPUT_INVALID")
    try:
        document = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_unique,
            parse_constant=_reject_constant,
        )
    except HMLSnapshotEnvelopeError:
        raise
    except (ValueError, UnicodeError, TypeError, RecursionError):
        raise HMLSnapshotEnvelopeError("HML_ENVELOPE_JSON_INVALID") from None
    if type(document) is not dict or set(document) != _FIELDS:
        raise HMLSnapshotEnvelopeError("HML_ENVELOPE_SCHEMA_INVALID")
    if any(
        type(document[key]) is not str or document[key] != value
        for key, value in {
            "schema": _SCHEMA,
            "environment": _TARGET_ENV,
            "compose_project": _TARGET_PROJECT,
            "service_id": _TARGET_SERVICE,
            "container_name": _TARGET_CONTAINER,
        }.items()
    ):
        raise HMLSnapshotEnvelopeError("HML_ENVELOPE_TARGET_DENIED")
    generation = document["generation"]
    if type(generation) is not int or not 1 <= generation <= _MAX_GENERATION:
        raise HMLSnapshotEnvelopeError("HML_ENVELOPE_GENERATION_INVALID")
    produced_at = document["produced_at"]
    payload_sha256 = document["payload_sha256"]
    key_id = document["key_id"]
    payload_b64 = document["payload_b64"]
    signature_b64 = document["signature_b64"]
    if (
        type(produced_at) is not str or _UTC_TS.fullmatch(produced_at) is None
        or type(payload_sha256) is not str or _HEX64.fullmatch(payload_sha256) is None
        or type(key_id) is not str or _KEY_ID.fullmatch(key_id) is None
        or type(payload_b64) is not str or not 1 <= len(payload_b64) <= 4096
        or type(signature_b64) is not str or not 1 <= len(signature_b64) <= 512
    ):
        raise HMLSnapshotEnvelopeError("HML_ENVELOPE_FIELD_INVALID")
    try:
        payload = base64.b64decode(payload_b64, validate=True)
        signature = base64.b64decode(signature_b64, validate=True)
    except (ValueError, TypeError):
        raise HMLSnapshotEnvelopeError("HML_ENVELOPE_ENCODING_INVALID") from None
    if hashlib.sha256(payload).hexdigest() != payload_sha256:
        raise HMLSnapshotEnvelopeError("HML_ENVELOPE_DIGEST_MISMATCH")
    if len(signature) != 64:
        raise HMLSnapshotEnvelopeError("HML_ENVELOPE_SIGNATURE_INVALID")
    try:
        diagnostic = review_untrusted_snapshot(payload, now=now)
    except SnapshotContractError as exc:
        raise HMLSnapshotEnvelopeError(exc.code) from None
    try:
        moment = datetime.fromisoformat(produced_at.replace("Z", "+00:00"))
    except ValueError:
        raise HMLSnapshotEnvelopeError("HML_ENVELOPE_FIELD_INVALID") from None
    message = signing_message(
        generation=generation,
        produced_at=produced_at,
        payload_sha256=payload_sha256,
        key_id=key_id,
        payload=payload,
    )
    return HMLSnapshotEnvelopeReview(
        diagnostic=diagnostic,
        generation=generation,
        produced_at=moment,
        payload_sha256=payload_sha256,
        key_id=key_id,
        signed_message=message,
        signature=signature,
    )

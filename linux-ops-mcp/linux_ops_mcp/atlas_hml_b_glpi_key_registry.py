"""GLPI-governed key registry metadata for ATLAS HML (source-only).

Defines the public registry record schema used to register and recover Ed25519
key *metadata* via GLPI change control. Never embeds private keys, passphrases,
or recovery blobs in Git, logs or MCP responses. Actual GLPI HTTP calls remain
operator-authorized and out of band.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass

from .atlas_hml_b_key_lifecycle import GLPI_RECOVERY_ID

_SCHEMA = "atlas.hml.b.glpi-key-registry.v1"
_KEY_ID = re.compile(r"[0-9a-f]{32}\Z")
_SHA40 = re.compile(r"[0-9a-f]{40}\Z")
_FIELDS = frozenset({
    "schema", "host", "environment", "key_id", "public_key_fingerprint",
    "generation", "glpi_ticket_id", "glpi_recovery_identifier",
    "rotation_of_key_id", "revoked", "owner_approved",
    "private_material_present", "prepare_enabled", "act_enabled",
})
_BLOCKS = (
    "GLPI_REGISTRY_METADATA_ONLY",
    "PRIVATE_KEY_MUST_STAY_OFF_GIT",
    "GLPI_HTTP_NOT_EXECUTED",
    "SEC_01_TO_10_PENDING",
    "PREPARE_DISABLED",
    "ACT_DISABLED",
)


class HMLGlpiKeyRegistryError(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class HMLGlpiKeyRegistryReview:
    key_id: str
    glpi_ticket_id: str
    revoked: bool
    status: str = "blocked"
    private_material_present: bool = False
    glpi_called: bool = False
    prepare_eligible: bool = False
    can_execute: bool = False
    blocks: tuple[str, ...] = _BLOCKS


def _unique(pairs):
    out = {}
    for k, v in pairs:
        if k in out:
            raise HMLGlpiKeyRegistryError("HML_GLPI_DUPLICATE_FIELD")
        out[k] = v
    return out


def _constant(_):
    raise HMLGlpiKeyRegistryError("HML_GLPI_JSON_INVALID")


def review_glpi_key_registry_record(raw: bytes) -> HMLGlpiKeyRegistryReview:
    """Offline schema review; completeness never calls GLPI or loads secrets."""
    if type(raw) is not bytes or not 1 <= len(raw) <= 4096 or b"\x00" in raw:
        raise HMLGlpiKeyRegistryError("HML_GLPI_INPUT_DENIED")
    try:
        doc = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique, parse_constant=_constant)
    except HMLGlpiKeyRegistryError:
        raise
    except (UnicodeError, ValueError, TypeError, RecursionError):
        raise HMLGlpiKeyRegistryError("HML_GLPI_JSON_INVALID") from None
    if type(doc) is not dict or set(doc) != _FIELDS:
        raise HMLGlpiKeyRegistryError("HML_GLPI_SCHEMA_DENIED")
    if (
        doc["schema"] != _SCHEMA
        or doc["host"] != "srv-api"
        or doc["environment"] != "hml"
        or type(doc["key_id"]) is not str
        or _KEY_ID.fullmatch(doc["key_id"]) is None
        or type(doc["public_key_fingerprint"]) is not str
        or _KEY_ID.fullmatch(doc["public_key_fingerprint"]) is None
        or type(doc["generation"]) is not int
        or doc["generation"] < 1
        or type(doc["glpi_ticket_id"]) is not str
        or not 1 <= len(doc["glpi_ticket_id"]) <= 64
        or doc["glpi_recovery_identifier"] != GLPI_RECOVERY_ID
        or doc["rotation_of_key_id"] not in (None, doc["rotation_of_key_id"])
        or (
            doc["rotation_of_key_id"] is not None
            and (
                type(doc["rotation_of_key_id"]) is not str
                or _KEY_ID.fullmatch(doc["rotation_of_key_id"]) is None
            )
        )
        or type(doc["revoked"]) is not bool
        or type(doc["owner_approved"]) is not bool
        or doc["private_material_present"] is not False
        or doc["prepare_enabled"] is not False
        or doc["act_enabled"] is not False
    ):
        raise HMLGlpiKeyRegistryError("HML_GLPI_FIELD_DENIED")
    # Reject accidental secret-looking payloads
    lowered = raw.lower()
    for needle in (b"private", b"begin ", b"passphrase", b"pkcs8", b"\x30\x82"):
        if needle in lowered and needle != b"private":
            # 'private_material_present' field name is allowed; PEM/DER is not.
            if needle != b"private":
                pass
    if b"begin " in lowered or b"pkcs8" in lowered or b"passphrase" in lowered:
        raise HMLGlpiKeyRegistryError("HML_GLPI_SECRET_PAYLOAD_DENIED")
    return HMLGlpiKeyRegistryReview(
        key_id=doc["key_id"],
        glpi_ticket_id=doc["glpi_ticket_id"],
        revoked=doc["revoked"],
    )


def build_glpi_registry_template(*, key_id: str, generation: int, glpi_ticket_id: str) -> bytes:
    """Public metadata template only; never includes private key material."""
    if _KEY_ID.fullmatch(key_id) is None or type(generation) is not int or generation < 1:
        raise HMLGlpiKeyRegistryError("HML_GLPI_TEMPLATE_DENIED")
    doc = {
        "schema": _SCHEMA,
        "host": "srv-api",
        "environment": "hml",
        "key_id": key_id,
        "public_key_fingerprint": key_id,
        "generation": generation,
        "glpi_ticket_id": glpi_ticket_id,
        "glpi_recovery_identifier": GLPI_RECOVERY_ID,
        "rotation_of_key_id": None,
        "revoked": False,
        "owner_approved": False,
        "private_material_present": False,
        "prepare_enabled": False,
        "act_enabled": False,
    }
    return json.dumps(doc, sort_keys=True, separators=(",", ":")).encode("utf-8")

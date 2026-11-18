"""Controlled generation-1 bootstrap candidate for ATLAS HML (source-only).

Absence of a checkpoint file is NEVER proof of first use. Operational genesis
requires an external anchor dossier, change record, target/key fingerprints and
an explicit owner approval flag. This module only validates an untrusted dossier
and may emit an approval-pending or blocked result. It never writes host state,
never sets disposable_genesis, never generates real keys, never calls GLPI.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass

_SCHEMA = "atlas.hml.b.bootstrap-control.v1"
_SHA40 = re.compile(r"[0-9a-f]{40}\Z")
_KEY = re.compile(r"[0-9a-f]{32}\Z")
_FIELDS = frozenset({
    "schema", "host", "environment", "target", "revision_sha",
    "artifact_version", "key_fingerprint", "change_record_id",
    "external_anchor_id", "external_anchor_kind", "owner_approved",
    "checkpoint_absent_claimed", "prior_generation_known",
    "disposable_fixture", "prepare_enabled", "act_enabled",
})
_ANCHORS = frozenset({
    "glpi_change", "signed_operator_receipt", "offline_quorum_minutes",
})
_BLOCKS = (
    "BOOTSTRAP_DOSSIER_UNTRUSTED",
    "CHECKPOINT_ABSENCE_IS_NOT_GENESIS_PROOF",
    "EXTERNAL_ANCHOR_REQUIRED",
    "HOST_BOOTSTRAP_NOT_EXECUTED",
    "SEC_01_TO_10_PENDING",
    "PREPARE_DISABLED",
    "ACT_DISABLED",
)


class HMLBootstrapControlError(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class HMLBootstrapControlReview:
    status: str = "blocked"
    approval_pending: bool = True
    genesis_authorized: bool = False
    absence_treated_as_genesis: bool = False
    disposable_fixture: bool = False
    prepare_eligible: bool = False
    can_execute: bool = False
    blocks: tuple[str, ...] = _BLOCKS


def _unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    out: dict[str, object] = {}
    for key, value in pairs:
        if key in out:
            raise HMLBootstrapControlError("HML_BOOTSTRAP_DUPLICATE_FIELD")
        out[key] = value
    return out


def _constant(_: str) -> object:
    raise HMLBootstrapControlError("HML_BOOTSTRAP_JSON_INVALID")


def review_untrusted_bootstrap_dossier(raw: bytes) -> HMLBootstrapControlReview:
    """Offline review. Completeness never authorizes host genesis."""
    if type(raw) is not bytes or not 1 <= len(raw) <= 8192 or b"\x00" in raw:
        raise HMLBootstrapControlError("HML_BOOTSTRAP_INPUT_DENIED")
    try:
        doc = json.loads(
            raw.decode("utf-8"), object_pairs_hook=_unique, parse_constant=_constant,
        )
    except HMLBootstrapControlError:
        raise
    except (UnicodeError, ValueError, TypeError, RecursionError):
        raise HMLBootstrapControlError("HML_BOOTSTRAP_JSON_INVALID") from None
    if type(doc) is not dict or set(doc) != _FIELDS:
        raise HMLBootstrapControlError("HML_BOOTSTRAP_SCHEMA_DENIED")
    if (
        doc["schema"] != _SCHEMA
        or doc["host"] != "srv-api"
        or doc["environment"] != "hml"
        or doc["target"] != "delpi-hml-public-hub"
        or type(doc["revision_sha"]) is not str
        or _SHA40.fullmatch(doc["revision_sha"]) is None
        or type(doc["artifact_version"]) is not str
        or not 1 <= len(doc["artifact_version"]) <= 64
        or type(doc["key_fingerprint"]) is not str
        or _KEY.fullmatch(doc["key_fingerprint"]) is None
        or type(doc["change_record_id"]) is not str
        or not 1 <= len(doc["change_record_id"]) <= 128
        or type(doc["external_anchor_id"]) is not str
        or not 1 <= len(doc["external_anchor_id"]) <= 128
        or doc["external_anchor_kind"] not in _ANCHORS
        or type(doc["owner_approved"]) is not bool
        or type(doc["checkpoint_absent_claimed"]) is not bool
        or type(doc["prior_generation_known"]) is not bool
        or type(doc["disposable_fixture"]) is not bool
        or doc["prepare_enabled"] is not False
        or doc["act_enabled"] is not False
    ):
        raise HMLBootstrapControlError("HML_BOOTSTRAP_SCOPE_DENIED")

    # Hard rule: claiming absence is never enough for genesis.
    if doc["checkpoint_absent_claimed"] is True and doc["prior_generation_known"] is False:
        if not (
            doc["owner_approved"] is True
            and doc["external_anchor_id"]
            and doc["change_record_id"]
        ):
            return HMLBootstrapControlReview(
                status="blocked",
                approval_pending=True,
                genesis_authorized=False,
                absence_treated_as_genesis=False,
                disposable_fixture=bool(doc["disposable_fixture"]),
            )

    if doc["disposable_fixture"] is True:
        # Fixture-only path mirrors disposable_genesis; still blocked operationally.
        return HMLBootstrapControlReview(
            status="blocked",
            approval_pending=False,
            genesis_authorized=False,
            absence_treated_as_genesis=False,
            disposable_fixture=True,
        )

    if (
        doc["owner_approved"] is True
        and doc["prior_generation_known"] is False
        and doc["checkpoint_absent_claimed"] is True
    ):
        # Even a complete dossier remains approval_pending until host execution
        # under separate operational authorization. Never auto-authorize.
        return HMLBootstrapControlReview(
            status="blocked",
            approval_pending=True,
            genesis_authorized=False,
            absence_treated_as_genesis=False,
            disposable_fixture=False,
        )

    return HMLBootstrapControlReview(
        status="blocked",
        approval_pending=True,
        genesis_authorized=False,
        absence_treated_as_genesis=False,
        disposable_fixture=False,
    )


def reject_absence_as_genesis() -> None:
    """Explicit API: ENOENT/missing checkpoint is never genesis proof."""
    raise HMLBootstrapControlError("HML_BOOTSTRAP_ABSENCE_NOT_GENESIS")

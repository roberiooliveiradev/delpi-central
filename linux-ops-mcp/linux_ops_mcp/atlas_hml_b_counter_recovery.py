"""Counter recovery / rollback decision candidate for ATLAS HML (source-only).

Reviews untrusted incident dossiers and decides BLOCKED + reconciliation
required. Never restores a lower generation from backup, never mutates host
checkpoint files, never enables PREPARE/ACT.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

_SCHEMA = "atlas.hml.b.counter-recovery.v1"
_FIELDS = frozenset({
    "schema", "incident", "local_generation", "anchor_generation",
    "backup_generation", "checkpoint_present", "checkpoint_corrupt",
    "signature_returned", "reservation_persisted", "concurrent_writers",
    "operator_reconcile_approved", "prepare_enabled", "act_enabled",
})
_INCIDENTS = frozenset({
    "crash_before_persist",
    "crash_after_reserve_before_return",
    "normal_restart",
    "checkpoint_corrupt",
    "checkpoint_absent",
    "restore_old_backup",
    "concurrent_processes",
    "anchor_divergence",
    "key_rotation",
    "key_revocation",
})
_BLOCKS = (
    "COUNTER_RECOVERY_UNTRUSTED_DOSSIER",
    "NEVER_SILENTLY_REGRESS_GENERATION",
    "HOST_RECOVERY_NOT_EXECUTED",
    "SEC_01_TO_10_PENDING",
    "PREPARE_DISABLED",
    "ACT_DISABLED",
)


class HMLCounterRecoveryError(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class HMLCounterRecoveryReview:
    incident: str
    decision: str
    required_generation_floor: int
    status: str = "blocked"
    silent_regression_prevented: bool = True
    prepare_eligible: bool = False
    can_execute: bool = False
    blocks: tuple[str, ...] = _BLOCKS


def _unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    out: dict[str, object] = {}
    for key, value in pairs:
        if key in out:
            raise HMLCounterRecoveryError("HML_RECOVERY_DUPLICATE_FIELD")
        out[key] = value
    return out


def _constant(_: str) -> object:
    raise HMLCounterRecoveryError("HML_RECOVERY_JSON_INVALID")


def review_untrusted_counter_recovery(raw: bytes) -> HMLCounterRecoveryReview:
    if type(raw) is not bytes or not 1 <= len(raw) <= 4096 or b"\x00" in raw:
        raise HMLCounterRecoveryError("HML_RECOVERY_INPUT_DENIED")
    try:
        doc = json.loads(
            raw.decode("utf-8"), object_pairs_hook=_unique, parse_constant=_constant,
        )
    except HMLCounterRecoveryError:
        raise
    except (UnicodeError, ValueError, TypeError, RecursionError):
        raise HMLCounterRecoveryError("HML_RECOVERY_JSON_INVALID") from None
    if type(doc) is not dict or set(doc) != _FIELDS:
        raise HMLCounterRecoveryError("HML_RECOVERY_SCHEMA_DENIED")
    if (
        doc["schema"] != _SCHEMA
        or doc["incident"] not in _INCIDENTS
        or type(doc["local_generation"]) is not int
        or type(doc["anchor_generation"]) is not int
        or type(doc["backup_generation"]) is not int
        or doc["local_generation"] < 0
        or doc["anchor_generation"] < 0
        or doc["backup_generation"] < 0
        or any(
            type(doc[k]) is not bool for k in (
                "checkpoint_present", "checkpoint_corrupt", "signature_returned",
                "reservation_persisted", "concurrent_writers",
                "operator_reconcile_approved",
            )
        )
        or doc["prepare_enabled"] is not False
        or doc["act_enabled"] is not False
    ):
        raise HMLCounterRecoveryError("HML_RECOVERY_SCOPE_DENIED")

    floor = max(doc["local_generation"], doc["anchor_generation"], doc["backup_generation"])
    incident = doc["incident"]

    # Old backup must never lower the floor.
    if incident == "restore_old_backup" and doc["backup_generation"] < floor:
        return HMLCounterRecoveryReview(
            incident=incident,
            decision="BLOCKED_RECONCILE_REQUIRED",
            required_generation_floor=floor,
        )

    if incident in {
        "checkpoint_corrupt", "checkpoint_absent", "anchor_divergence",
        "concurrent_processes", "crash_after_reserve_before_return",
    }:
        return HMLCounterRecoveryReview(
            incident=incident,
            decision="BLOCKED_RECONCILE_REQUIRED",
            required_generation_floor=floor,
        )

    if incident == "normal_restart" and doc["checkpoint_present"] and not doc["checkpoint_corrupt"]:
        if doc["local_generation"] >= doc["anchor_generation"]:
            return HMLCounterRecoveryReview(
                incident=incident,
                decision="BLOCKED_WARM_START_OK_SOURCE_ONLY",
                required_generation_floor=doc["local_generation"],
            )

    if incident == "crash_before_persist":
        return HMLCounterRecoveryReview(
            incident=incident,
            decision="BLOCKED_RETRY_SAME_GENERATION",
            required_generation_floor=max(doc["local_generation"], doc["anchor_generation"]),
        )

    if incident in {"key_rotation", "key_revocation"}:
        if not doc["operator_reconcile_approved"]:
            return HMLCounterRecoveryReview(
                incident=incident,
                decision="BLOCKED_RECONCILE_REQUIRED",
                required_generation_floor=floor,
            )
        return HMLCounterRecoveryReview(
            incident=incident,
            decision="BLOCKED_KEY_EVENT_PENDING_HOST",
            required_generation_floor=floor,
        )

    return HMLCounterRecoveryReview(
        incident=incident,
        decision="BLOCKED_RECONCILE_REQUIRED",
        required_generation_floor=floor,
    )


def assert_generation_floor(*, proposed: int, floor: int) -> None:
    if type(proposed) is not int or type(floor) is not int or proposed < 1 or floor < 0:
        raise HMLCounterRecoveryError("HML_RECOVERY_FLOOR_INPUT_DENIED")
    if proposed < floor:
        raise HMLCounterRecoveryError("HML_RECOVERY_GENERATION_REGRESSION")

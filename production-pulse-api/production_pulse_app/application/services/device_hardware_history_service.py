"""Hardware history API payloads for a logical device."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from production_pulse_app.core.serialize import json_safe
from production_pulse_app.infrastructure.persistence.repositories.postgres_device_hardware_assignment_repository import (
    PostgresDeviceHardwareAssignmentRepository,
)
from production_pulse_app.infrastructure.persistence.repositories.postgres_device_repository import (
    DeviceNotFoundError,
    PostgresDeviceRepository,
)
from production_pulse_app.infrastructure.persistence.repositories.postgres_hardware_unit_repository import (
    PostgresHardwareUnitRepository,
)

_ALLOWED_REASONS = frozenset(
    {
        "electronic_failure",
        "preventive_maintenance",
        "hardware_upgrade",
        "test",
        "other",
    }
)


def _iso(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()
    return str(value)


def _assignment_to_api(row: dict[str, Any], *, unit: dict[str, Any] | None = None) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    effective_from = row.get("effective_from")
    effective_to = row.get("effective_to")
    installed_seconds = None
    if isinstance(effective_from, datetime):
        end = effective_to if isinstance(effective_to, datetime) else now
        if getattr(effective_from, "tzinfo", None) is None:
            effective_from = effective_from.replace(tzinfo=timezone.utc)
        if getattr(end, "tzinfo", None) is None:
            end = end.replace(tzinfo=timezone.utc)
        installed_seconds = max(0, int((end - effective_from).total_seconds()))

    return json_safe(
        {
            "assignmentId": str(row["id"]),
            "hardwareUnitId": str(row["hardware_unit_id"]),
            "hardwareUid": row.get("hardware_uid_snapshot")
            or (unit.get("hardware_uid") if unit else None),
            "macAddress": row.get("mac_address_snapshot")
            or (unit.get("current_mac_address") if unit else None),
            "controllerCode": row.get("controller_code_snapshot")
            or (unit.get("controller_code") if unit else None),
            "identityConfidence": row.get("identity_confidence"),
            "ipAddress": str(row["ip_address_snapshot"]) if row.get("ip_address_snapshot") else None,
            "effectiveFrom": _iso(row.get("effective_from")),
            "effectiveTo": _iso(row.get("effective_to")),
            "active": row.get("effective_to") is None,
            "firstFirmwareVersion": row.get("first_firmware_version"),
            "lastFirmwareVersion": row.get("last_firmware_version"),
            "counterDelta": int(row.get("counter_delta_total") or 0),
            "onlineSeconds": int(row.get("online_seconds_total") or 0),
            "installedSeconds": installed_seconds,
            "rebootCount": int(row.get("reboot_count") or 0),
            "replacementReason": row.get("replacement_reason"),
            "replacementNotes": row.get("replacement_notes"),
            "firstCounterRaw": row.get("first_counter_raw"),
            "lastCounterRaw": row.get("last_counter_raw"),
            "logicalCounterAtStart": row.get("logical_counter_at_start"),
            "logicalCounterAtEnd": row.get("logical_counter_at_end"),
        }
    )


class DeviceHardwareHistoryService:
    def __init__(
        self,
        devices: PostgresDeviceRepository | None = None,
        assignments: PostgresDeviceHardwareAssignmentRepository | None = None,
        units: PostgresHardwareUnitRepository | None = None,
    ) -> None:
        self._devices = devices or PostgresDeviceRepository()
        self._assignments = assignments or PostgresDeviceHardwareAssignmentRepository()
        self._units = units or PostgresHardwareUnitRepository()

    def get_history(self, device_id: UUID) -> dict[str, Any]:
        device = self._devices.get_by_id(device_id)
        if device is None:
            raise DeviceNotFoundError(str(device_id))

        rows = self._assignments.list_for_device(device_id)
        history: list[dict[str, Any]] = []
        current: dict[str, Any] | None = None
        for row in rows:
            unit = self._units.get_by_id(UUID(str(row["hardware_unit_id"])))
            item = _assignment_to_api(row, unit=unit)
            if item["active"]:
                current = item
            history.append(item)

        counts = self._assignments.count_for_device(device_id)
        legacy_counter = self._assignments.sum_legacy_counter_before_traceability(device_id)
        traceability_started = None
        if history:
            # oldest effective_from
            oldest = min(
                (h["effectiveFrom"] for h in history if h.get("effectiveFrom")),
                default=None,
            )
            traceability_started = oldest

        events = [
            json_safe(
                {
                    "id": str(ev["id"]),
                    "eventType": ev["event_type"],
                    "assignmentId": str(ev["assignment_id"]) if ev.get("assignment_id") else None,
                    "hardwareUnitId": str(ev["hardware_unit_id"]) if ev.get("hardware_unit_id") else None,
                    "payload": ev.get("payload") or {},
                    "createdAt": _iso(ev.get("created_at")),
                }
            )
            for ev in self._assignments.list_events(device_id)
        ]

        return {
            "deviceId": str(device_id),
            "current": current,
            "history": history,
            "summary": {
                "hardwareCount": counts["hardwareUnits"],
                "macCount": counts["macs"],
                "replacementCount": counts["replacements"],
                "assignmentCount": counts["assignments"],
                "legacyUnidentifiedCounterDelta": legacy_counter,
                "traceabilityStartedAt": traceability_started,
            },
            "events": events,
        }

    def patch_assignment(
        self,
        device_id: UUID,
        assignment_id: UUID,
        *,
        replacement_reason: str | None,
        replacement_notes: str | None,
        actor_sub: str | None,
    ) -> dict[str, Any]:
        device = self._devices.get_by_id(device_id)
        if device is None:
            raise DeviceNotFoundError(str(device_id))
        row = self._assignments.get_by_id(assignment_id)
        if row is None or UUID(str(row["device_id"])) != device_id:
            raise DeviceNotFoundError(str(assignment_id))
        if replacement_reason is not None and replacement_reason not in _ALLOWED_REASONS:
            from production_pulse_app.domain.errors import ContentCodedError

            raise ContentCodedError("invalidReplacementReason")
        updated = self._assignments.patch_metadata(
            assignment_id,
            replacement_reason=replacement_reason,
            replacement_notes=replacement_notes,
            actor_sub=actor_sub,
        )
        if updated is None:
            raise DeviceNotFoundError(str(assignment_id))
        if replacement_reason is not None:
            self._assignments.insert_event(
                device_id=device_id,
                event_type="replacement_confirmed",
                assignment_id=assignment_id,
                hardware_unit_id=UUID(str(updated["hardware_unit_id"])),
                payload={
                    "replacementReason": replacement_reason,
                    "replacementNotes": replacement_notes,
                },
                actor_sub=actor_sub,
            )
        unit = self._units.get_by_id(UUID(str(updated["hardware_unit_id"])))
        return _assignment_to_api(updated, unit=unit)

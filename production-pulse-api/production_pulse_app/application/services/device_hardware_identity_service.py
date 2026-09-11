"""Resolve physical hardware identity before counter continuity."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from production_pulse_app.domain.services.hardware_identity_normalize_service import (
    classify_identity,
    extract_identity_fields,
    normalize_controller_code,
    normalize_hardware_uid,
    normalize_mac_address,
)
from production_pulse_app.domain.services.hardware_identity_types import (
    HardwareIdentityOutcome,
    HardwareResolutionResult,
    ObservedHardwareIdentity,
)
from production_pulse_app.infrastructure.persistence.repositories.postgres_device_hardware_assignment_repository import (
    PostgresDeviceHardwareAssignmentRepository,
)
from production_pulse_app.infrastructure.persistence.repositories.postgres_device_repository import (
    PostgresDeviceRepository,
)
from production_pulse_app.infrastructure.persistence.repositories.postgres_firmware_repository import (
    PostgresFirmwareUpdateJobRepository,
)
from production_pulse_app.infrastructure.persistence.repositories.postgres_hardware_unit_repository import (
    PostgresHardwareUnitRepository,
)

logger = logging.getLogger(__name__)

_OPEN_OTA = ("pending", "authorized", "downloading", "applying")


def _as_int(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def observed_from_meta(meta: dict[str, Any] | None, *, device_ip: str | None = None) -> ObservedHardwareIdentity:
    fields = extract_identity_fields(meta if isinstance(meta, dict) else None)
    kind, confidence, source = classify_identity(
        hardware_uid=fields["hardware_uid"],
        controller_code=fields["controller_code"],
        mac_address=fields["mac_address"],
    )
    del kind
    fw = None
    uptime = None
    if isinstance(meta, dict):
        if meta.get("firmwareVersion") is not None:
            fw = str(meta.get("firmwareVersion")).strip() or None
        uptime = _as_int(meta.get("uptimeMs"))
    return ObservedHardwareIdentity(
        hardware_uid=fields["hardware_uid"],
        controller_code=fields["controller_code"],
        mac_address=fields["mac_address"],
        identity_confidence=confidence,
        identity_source=source or "legacy",
        firmware_version=fw,
        uptime_ms=uptime,
        ip_address=device_ip,
    )


class DeviceHardwareIdentityService:
    def __init__(
        self,
        units: PostgresHardwareUnitRepository | None = None,
        assignments: PostgresDeviceHardwareAssignmentRepository | None = None,
        devices: PostgresDeviceRepository | None = None,
        jobs: PostgresFirmwareUpdateJobRepository | None = None,
    ) -> None:
        self._units = units or PostgresHardwareUnitRepository()
        self._assignments = assignments or PostgresDeviceHardwareAssignmentRepository()
        self._devices = devices or PostgresDeviceRepository()
        self._jobs = jobs or PostgresFirmwareUpdateJobRepository()

    def resolve_for_poll(
        self,
        device: dict[str, Any],
        *,
        reading_meta: dict[str, Any],
        counter_raw: int | None,
        logical_counter: int | None,
        actor_sub: str | None = None,
    ) -> HardwareResolutionResult:
        device_id = UUID(str(device["id"]))
        observed = observed_from_meta(
            reading_meta,
            device_ip=str(device.get("ip_address") or "") or None,
        )
        active = self._assignments.get_active_for_device(device_id)

        if (
            not observed.hardware_uid
            and not observed.controller_code
            and not observed.mac_address
        ):
            logger.info(
                "hardware_identity_observed device_id=%s outcome=legacy_unknown",
                device_id,
            )
            return HardwareResolutionResult(
                outcome=HardwareIdentityOutcome.LEGACY_UNKNOWN,
                assignment_id=UUID(str(active["id"])) if active else None,
                hardware_unit_id=UUID(str(active["hardware_unit_id"])) if active else None,
                observed=observed,
                allow_counter_restore=True,
                meta={"identityConfidence": "legacy_unknown"},
            )

        unit = self._resolve_or_create_unit(observed, hardware_family=str(device.get("driver_key") or ""))
        unit_id = UUID(str(unit["id"]))

        if active is None:
            opened = self._open_new(
                device_id=device_id,
                unit_id=unit_id,
                observed=observed,
                counter_raw=counter_raw,
                logical_counter=logical_counter,
                actor_sub=actor_sub,
                event_type="hardware_detected",
            )
            self._sync_device_controller_cache(device_id, observed.controller_code)
            logger.info(
                "hardware_first_assignment device_id=%s hardware_unit_id=%s assignment_id=%s",
                device_id,
                unit_id,
                opened["id"],
            )
            return HardwareResolutionResult(
                outcome=HardwareIdentityOutcome.FIRST_OBSERVATION,
                assignment_id=UUID(str(opened["id"])),
                hardware_unit_id=unit_id,
                observed=observed,
                allow_counter_restore=True,
                meta={"identityConfidence": observed.identity_confidence},
            )

        active_unit_id = UUID(str(active["hardware_unit_id"]))
        if active_unit_id == unit_id:
            network_changed = self._maybe_network_change(active, unit, observed, device_id)
            self._units.touch(
                unit_id,
                mac_address=observed.mac_address,
                controller_code=observed.controller_code,
                hardware_uid=observed.hardware_uid,
                identity_confidence=observed.identity_confidence,
                identity_source=observed.identity_source,
            )
            self._sync_device_controller_cache(device_id, observed.controller_code)
            outcome = (
                HardwareIdentityOutcome.NETWORK_IDENTITY_CHANGED
                if network_changed
                else HardwareIdentityOutcome.SAME_HARDWARE
            )
            return HardwareResolutionResult(
                outcome=outcome,
                assignment_id=UUID(str(active["id"])),
                hardware_unit_id=unit_id,
                observed=observed,
                allow_counter_restore=True,
                meta={"identityConfidence": observed.identity_confidence},
            )

        # Different physical unit → replacement
        prev_assignment_id = UUID(str(active["id"]))
        closed = self._assignments.close_assignment(
            prev_assignment_id,
            logical_counter_at_end=logical_counter,
            last_counter_raw=_as_int(active.get("last_counter_raw")),
            last_firmware_version=observed.firmware_version,
            actor_sub=actor_sub,
        )
        self._fail_open_ota_targets(device_id)
        opened = self._open_new(
            device_id=device_id,
            unit_id=unit_id,
            observed=observed,
            counter_raw=counter_raw,
            logical_counter=logical_counter,
            actor_sub=actor_sub,
            event_type="hardware_replaced",
            extra_payload={
                "oldHardwareUnitId": str(active_unit_id),
                "oldAssignmentId": str(prev_assignment_id),
                "oldMac": active.get("mac_address_snapshot"),
                "newMac": observed.mac_address,
                "oldHardwareUid": active.get("hardware_uid_snapshot"),
                "newHardwareUid": observed.hardware_uid,
            },
        )
        self._sync_device_controller_cache(device_id, observed.controller_code)
        logger.info(
            "hardware_replacement_detected device_id=%s old_unit=%s new_unit=%s old_assignment=%s new_assignment=%s",
            device_id,
            active_unit_id,
            unit_id,
            prev_assignment_id,
            opened["id"],
        )
        return HardwareResolutionResult(
            outcome=HardwareIdentityOutcome.HARDWARE_REPLACEMENT,
            assignment_id=UUID(str(opened["id"])),
            hardware_unit_id=unit_id,
            previous_assignment_id=prev_assignment_id,
            previous_hardware_unit_id=active_unit_id,
            observed=observed,
            allow_counter_restore=False,
            replaced=True,
            meta={
                "identityConfidence": observed.identity_confidence,
                "previousAssignmentId": str(prev_assignment_id),
                "closedAssignmentId": str(closed["id"]) if closed else str(prev_assignment_id),
            },
        )

    def apply_poll_summaries(
        self,
        resolution: HardwareResolutionResult,
        *,
        device: dict[str, Any],
        counter_raw: int | None,
        counter_delta: int,
        previous_uptime_ms: int | None,
        success_at: datetime | None = None,
    ) -> None:
        if resolution.assignment_id is None:
            return
        assignment = self._assignments.get_by_id(resolution.assignment_id)
        if assignment is None:
            return

        now = success_at or datetime.now(timezone.utc)
        online_add = 0
        prev_success = assignment.get("last_success_poll_at")
        if prev_success is not None and resolution.outcome != HardwareIdentityOutcome.HARDWARE_REPLACEMENT:
            if getattr(prev_success, "tzinfo", None) is None:
                prev_success = prev_success.replace(tzinfo=timezone.utc)
            delta_sec = int((now - prev_success).total_seconds())
            poll_ms = int(device.get("poll_interval_ms") or 30000)
            max_gap = max(60, int((poll_ms / 1000.0) * 3))
            if delta_sec > 0:
                online_add = min(delta_sec, max_gap)

        reboot_inc = 0
        if (
            resolution.same_hardware
            and previous_uptime_ms is not None
            and resolution.observed.uptime_ms is not None
            and resolution.observed.uptime_ms < previous_uptime_ms
        ):
            reboot_inc = 1

        self._assignments.update_poll_stats(
            resolution.assignment_id,
            counter_raw=counter_raw,
            counter_delta=max(0, int(counter_delta)),
            firmware_version=resolution.observed.firmware_version,
            online_seconds_add=online_add,
            reboot_increment=reboot_inc,
            uptime_ms=resolution.observed.uptime_ms,
            mac_address=resolution.observed.mac_address,
            controller_code=resolution.observed.controller_code,
            success_at=now,
        )

    def _resolve_or_create_unit(
        self,
        observed: ObservedHardwareIdentity,
        *,
        hardware_family: str,
    ) -> dict[str, Any]:
        existing = None
        if observed.hardware_uid:
            existing = self._units.find_by_hardware_uid(observed.hardware_uid)
        if existing is None and observed.controller_code:
            existing = self._units.find_by_controller_code(observed.controller_code)
        if existing is None and observed.mac_address and observed.identity_confidence == "mac_fallback":
            existing = self._units.find_by_mac(observed.mac_address)
        if existing:
            return existing
        return self._units.create(
            hardware_uid=observed.hardware_uid,
            mac_address=observed.mac_address,
            controller_code=observed.controller_code,
            hardware_family=hardware_family or None,
            identity_confidence=observed.identity_confidence,
            identity_source=observed.identity_source,
        )

    def _open_new(
        self,
        *,
        device_id: UUID,
        unit_id: UUID,
        observed: ObservedHardwareIdentity,
        counter_raw: int | None,
        logical_counter: int | None,
        actor_sub: str | None,
        event_type: str,
        extra_payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        # If this unit is somehow active on another device, close that first.
        other = self._assignments.get_active_for_unit(unit_id)
        if other and UUID(str(other["device_id"])) != device_id:
            self._assignments.close_assignment(
                UUID(str(other["id"])),
                actor_sub=actor_sub,
            )
            self._assignments.insert_event(
                device_id=UUID(str(other["device_id"])),
                event_type="hardware_removed",
                assignment_id=UUID(str(other["id"])),
                hardware_unit_id=unit_id,
                payload={"reason": "reassigned_to_other_device", "newDeviceId": str(device_id)},
                actor_sub=actor_sub,
            )

        opened = self._assignments.open_assignment(
            device_id=device_id,
            hardware_unit_id=unit_id,
            ip_address=observed.ip_address,
            mac_address=observed.mac_address,
            controller_code=observed.controller_code,
            hardware_uid=observed.hardware_uid,
            identity_confidence=observed.identity_confidence,
            firmware_version=observed.firmware_version,
            counter_raw=counter_raw,
            logical_counter=logical_counter,
            actor_sub=actor_sub,
        )
        payload = {
            "hardwareUid": observed.hardware_uid,
            "mac": observed.mac_address,
            "controllerCode": observed.controller_code,
            "identityConfidence": observed.identity_confidence,
            **(extra_payload or {}),
        }
        self._assignments.insert_event(
            device_id=device_id,
            event_type=event_type,
            assignment_id=UUID(str(opened["id"])),
            hardware_unit_id=unit_id,
            payload=payload,
            actor_sub=actor_sub,
        )
        logger.info(
            "hardware_assignment_opened device_id=%s assignment_id=%s hardware_unit_id=%s event=%s",
            device_id,
            opened["id"],
            unit_id,
            event_type,
        )
        return opened

    def _maybe_network_change(
        self,
        active: dict[str, Any],
        unit: dict[str, Any],
        observed: ObservedHardwareIdentity,
        device_id: UUID,
    ) -> bool:
        old_mac = normalize_mac_address(active.get("mac_address_snapshot"))
        new_mac = observed.mac_address
        uid = observed.hardware_uid or normalize_hardware_uid(unit.get("hardware_uid"))
        if uid and old_mac and new_mac and old_mac != new_mac:
            self._assignments.insert_event(
                device_id=device_id,
                event_type="network_identity_changed",
                assignment_id=UUID(str(active["id"])),
                hardware_unit_id=UUID(str(unit["id"])),
                payload={"oldMac": old_mac, "newMac": new_mac, "hardwareUid": uid},
            )
            logger.info(
                "hardware_network_identity_changed device_id=%s old_mac=%s new_mac=%s",
                device_id,
                old_mac,
                new_mac,
            )
            return True
        return False

    def _sync_device_controller_cache(self, device_id: UUID, controller_code: str | None) -> None:
        code = normalize_controller_code(controller_code)
        if not code:
            return
        try:
            self._devices.update_controller_code(device_id, code)
        except AttributeError:
            # Fallback if helper not present yet
            pass
        except Exception:
            logger.exception("failed_to_sync_controller_code_cache device_id=%s", device_id)

    def _fail_open_ota_targets(self, device_id: UUID) -> None:
        try:
            self._jobs.fail_open_targets_for_device(
                device_id,
                error_code="hardware_replaced",
                error_message="Physical hardware was replaced during an open OTA target.",
            )
        except AttributeError:
            logger.warning("fail_open_targets_for_device not available on job repository")
        except Exception:
            logger.exception("fail_open_ota_on_hardware_replace_failed device_id=%s", device_id)

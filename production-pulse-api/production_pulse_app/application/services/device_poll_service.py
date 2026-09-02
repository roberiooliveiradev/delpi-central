from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from production_pulse_app.application.services.device_driver_registry_service import (
    DeviceDriverNotImplementedError,
    get_device_driver_registry,
)
from production_pulse_app.core.serialize import json_safe
from production_pulse_app.domain.errors import DeviceDriverError
from production_pulse_app.domain.services.device_connectivity_status_service import (
    resolve_connectivity_status,
)
from production_pulse_app.domain.services.device_monotonic_counter_continuity_service import (
    COUNTER_OFFSET_KEY,
    COUNTER_RAW_KEY,
    apply_monotonic_continuity,
    build_hardware_set_payload,
    counter_floor,
    counter_restore_enabled,
    intentional_decrease_command_grace_ms,
    intentional_decrease_command_keys,
    is_unexplained_counter_drop,
    public_metrics,
)
from production_pulse_app.domain.services.device_reading_delta_service import compute_delta_metrics
from production_pulse_app.domain.services.reading_serialization_service import reading_row_to_api
from production_pulse_app.infrastructure.persistence.repositories.postgres_device_binding_repository import (
    PostgresDeviceBindingRepository,
)
from production_pulse_app.infrastructure.persistence.repositories.postgres_device_command_repository import (
    PostgresDeviceCommandRepository,
)
from production_pulse_app.infrastructure.persistence.repositories.postgres_device_reading_repository import (
    PostgresDeviceReadingRepository,
)
from production_pulse_app.infrastructure.persistence.repositories.postgres_device_repository import (
    DeviceNotFoundError,
    PostgresDeviceRepository,
)


class DevicePollService:
    def __init__(
        self,
        device_repository: PostgresDeviceRepository | None = None,
        binding_repository: PostgresDeviceBindingRepository | None = None,
        reading_repository: PostgresDeviceReadingRepository | None = None,
        command_repository: PostgresDeviceCommandRepository | None = None,
    ) -> None:
        self._devices = device_repository or PostgresDeviceRepository()
        self._bindings = binding_repository or PostgresDeviceBindingRepository()
        self._readings = reading_repository or PostgresDeviceReadingRepository()
        self._commands = command_repository or PostgresDeviceCommandRepository()
        self._registry = get_device_driver_registry()

    def _require_device(self, device_id: UUID) -> dict[str, Any]:
        device = self._devices.get_by_id(device_id)
        if device is None:
            raise DeviceNotFoundError(str(device_id))
        return device

    def _has_binding(self, device_id: UUID) -> bool:
        return self._bindings.get_active(device_id) is not None

    def _capabilities(self, driver_key: str) -> dict[str, Any]:
        return self._registry.build_capabilities(driver_key)

    def _has_recent_intentional_decrease(self, device_id: UUID, driver_key: str) -> bool:
        """True quando um comando recente explica queda intencional (pad), não power-loss."""
        return self._commands.has_recent_successful_command(
            device_id,
            command_keys=intentional_decrease_command_keys(driver_key),
            within_ms=intentional_decrease_command_grace_ms(driver_key),
        )

    def _build_poll_payload(
        self,
        device: dict[str, Any],
        *,
        has_binding: bool,
        metrics: dict[str, Any],
        recorded_at: datetime,
        delta_metrics: dict[str, Any] | None = None,
        reading_id: int | None = None,
        meta: dict[str, Any] | None = None,
        latency_ms: int | None = None,
        chip_health: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        connectivity = resolve_connectivity_status(device, has_binding=has_binding)
        payload: dict[str, Any] = {
            "metrics": metrics,
            "recordedAt": recorded_at,
            "status": connectivity["status"],
            "online": connectivity["online"],
            "graceSeconds": connectivity["graceSeconds"],
            "capabilities": self._capabilities(device["driver_key"]),
        }
        if delta_metrics is not None:
            payload["deltaMetrics"] = delta_metrics
        if reading_id is not None:
            payload["readingId"] = reading_id
        if meta:
            payload["meta"] = meta
        if latency_ms is not None:
            payload["latencyMs"] = latency_ms
        if chip_health:
            for key, value in chip_health.items():
                if value is not None:
                    payload[key] = value
        return json_safe(payload)

    def read_live(self, device_id: UUID) -> dict[str, Any]:
        device = self._require_device(device_id)
        has_binding = self._has_binding(device_id)
        try:
            reading = self._read_from_driver(device)
        except DeviceDriverError as exc:
            connectivity = resolve_connectivity_status(device, has_binding=has_binding)
            raise DevicePollFailedError(
                exc.code,
                technical_detail=exc.technical_detail,
                connectivity=connectivity,
            ) from exc
        previous_metrics = device.get("last_metrics") or {}
        accept_decrease = self._has_recent_intentional_decrease(device_id, device["driver_key"])
        canonical, _meta = apply_monotonic_continuity(
            driver_key=device["driver_key"],
            previous_metrics=previous_metrics if isinstance(previous_metrics, dict) else {},
            raw_metrics=reading.metrics,
            accept_decrease=accept_decrease,
        )
        return self._build_poll_payload(
            device,
            has_binding=has_binding,
            metrics=public_metrics(canonical),
            recorded_at=reading.recorded_at,
            chip_health=self._chip_health_from_driver(device),
        )

    def poll_and_persist(self, device_id: UUID, *, source: str = "manual") -> dict[str, Any]:
        device = self._require_device(device_id)
        has_binding = self._has_binding(device_id)

        try:
            reading = self._read_from_driver(device)
        except DeviceDriverError as exc:
            device = self._devices.record_poll_failure(device_id, error_message=exc.code)
            connectivity = resolve_connectivity_status(device, has_binding=has_binding)
            raise DevicePollFailedError(
                exc.code,
                technical_detail=exc.technical_detail,
                connectivity=connectivity,
            ) from exc

        previous_metrics = (
            device.get("last_metrics") if isinstance(device.get("last_metrics"), dict) else {}
        )
        raw_metrics = dict(reading.metrics)
        continuity_meta: dict[str, Any] = {}
        accept_decrease = self._has_recent_intentional_decrease(device_id, device["driver_key"])

        restored = self._maybe_hardware_restore_counter(
            device,
            previous_metrics=previous_metrics,
            raw_metrics=raw_metrics,
            accept_decrease=accept_decrease,
        )
        if restored is not None:
            canonical, continuity_meta = restored
        else:
            floored = self._maybe_hardware_floor_counter(device, raw_metrics=raw_metrics)
            if floored is not None:
                canonical, continuity_meta = floored
            else:
                canonical, continuity_meta = apply_monotonic_continuity(
                    driver_key=device["driver_key"],
                    previous_metrics=previous_metrics,
                    raw_metrics=raw_metrics,
                    accept_decrease=accept_decrease,
                )

        previous_public = public_metrics(previous_metrics)
        canonical_public = public_metrics(canonical)
        delta_metrics, delta_meta = compute_delta_metrics(
            driver_key=device["driver_key"],
            previous_metrics=previous_public,
            new_metrics=canonical_public,
        )
        meta = {**continuity_meta, **delta_meta}
        if meta.get("counter_restored"):
            meta.pop("counter_reset", None)

        reading_row = self._readings.insert(
            device_id,
            metrics=canonical_public,
            delta_metrics=delta_metrics,
            meta=meta,
            source=source,
            recorded_at=reading.recorded_at,
        )
        device = self._devices.record_poll_success(device_id, metrics=canonical)
        return self._build_poll_payload(
            device,
            has_binding=has_binding,
            metrics=canonical_public,
            recorded_at=reading_row["recorded_at"],
            delta_metrics=delta_metrics,
            reading_id=reading_row["id"],
            meta=meta,
        )

    def _maybe_hardware_floor_counter(
        self,
        device: dict[str, Any],
        *,
        raw_metrics: dict[str, Any],
    ) -> tuple[dict[str, Any], dict[str, Any]] | None:
        """Se o chip reportou contagem negativa, grava o piso (0) no hardware."""
        new_raw = raw_metrics.get("counter")
        if not isinstance(new_raw, (int, float)) or isinstance(new_raw, bool):
            return None
        floor = counter_floor()
        if int(new_raw) >= floor:
            return None

        try:
            driver = self._registry.get_implementation(device["driver_key"])
        except DeviceDriverNotImplementedError:
            return None

        result = driver.execute(
            device,
            "set",
            payload=build_hardware_set_payload(counter=floor),
        )
        if not result.success or not result.metrics:
            metrics = {
                "counter": floor,
                COUNTER_RAW_KEY: floor,
                COUNTER_OFFSET_KEY: 0,
            }
            return metrics, {
                "counter_floored": True,
                "counter_floor": floor,
                "counter_floor_from_raw": int(new_raw),
                "counter_floor_sync": "software_only",
            }

        restored_raw = result.metrics.get("counter")
        if not isinstance(restored_raw, (int, float)) or isinstance(restored_raw, bool):
            restored_raw = floor
        value = max(floor, int(restored_raw))
        return {
            "counter": value,
            COUNTER_RAW_KEY: value,
            COUNTER_OFFSET_KEY: 0,
        }, {
            "counter_floored": True,
            "counter_floor": floor,
            "counter_floor_from_raw": int(new_raw),
            "counter_floor_sync": "hardware_set",
        }

    def _maybe_hardware_restore_counter(
        self,
        device: dict[str, Any],
        *,
        previous_metrics: dict[str, Any],
        raw_metrics: dict[str, Any],
        accept_decrease: bool = False,
    ) -> tuple[dict[str, Any], dict[str, Any]] | None:
        if not counter_restore_enabled(device["driver_key"]):
            return None
        if accept_decrease:
            # Comando recente (decrement/reset/set) explica a queda — não reescrever o chip.
            return None

        prev_logical = previous_metrics.get("counter")
        prev_raw = previous_metrics.get(COUNTER_RAW_KEY, prev_logical)
        new_raw = raw_metrics.get("counter")
        if not isinstance(prev_logical, (int, float)) or isinstance(prev_logical, bool):
            return None
        if not isinstance(prev_raw, (int, float)) or isinstance(prev_raw, bool):
            return None
        if not isinstance(new_raw, (int, float)) or isinstance(new_raw, bool):
            return None
        if not is_unexplained_counter_drop(int(prev_raw), int(new_raw)):
            return None

        target = max(counter_floor(), int(prev_logical) + int(new_raw))
        try:
            driver = self._registry.get_implementation(device["driver_key"])
        except DeviceDriverNotImplementedError:
            return None

        result = driver.execute(
            device,
            "set",
            payload=build_hardware_set_payload(counter=target),
        )
        if not result.success or not result.metrics:
            return None

        restored_raw = result.metrics.get("counter")
        if not isinstance(restored_raw, (int, float)) or isinstance(restored_raw, bool):
            return None

        value = max(counter_floor(), int(restored_raw))
        metrics = {
            "counter": value,
            COUNTER_RAW_KEY: value,
            COUNTER_OFFSET_KEY: 0,
        }
        meta = {
            "counter_restored": True,
            "counter_restore_mode": "hardware_set",
            "counter_restore_from": int(prev_logical),
            "counter_restore_raw": int(new_raw),
            "counter_restore_target": target,
            "counter_restore_reason": "unexplained_drop",
        }
        return metrics, meta

    def list_readings(
        self,
        device_id: UUID,
        *,
        page: int = 1,
        page_size: int = 20,
        recorded_from: datetime | None = None,
        recorded_to: datetime | None = None,
        metric_key: str | None = None,
    ) -> dict[str, Any]:
        self._require_device(device_id)
        page = max(1, page)
        page_size = min(max(1, page_size), 500)
        rows, total = self._readings.list_for_device(
            device_id,
            page=page,
            page_size=page_size,
            recorded_from=recorded_from,
            recorded_to=recorded_to,
            metric_key=metric_key,
        )
        return {
            "items": [json_safe(reading_row_to_api(row)) for row in rows],
            "pagination": {
                "page": page,
                "pageSize": page_size,
                "total": total,
            },
        }

    def poll_all(
        self,
        *,
        branch: str | None = None,
        branches: list[str] | None = None,
        role: str | None = None,
    ) -> dict[str, Any]:
        rows = self._devices.list_devices(branch=branch, branches=branches, role_key=role, enabled=True)
        device_ids = [row["id"] for row in rows]
        bound_ids = self._bindings.active_device_ids_among(device_ids)

        results: list[dict[str, Any]] = []
        succeeded = 0
        failed = 0
        skipped = 0

        for row in rows:
            device_id = row["id"]
            if device_id not in bound_ids:
                skipped += 1
                continue
            try:
                payload = self.poll_and_persist(device_id, source="manual")
                succeeded += 1
                results.append(
                    {
                        "deviceId": str(device_id),
                        "success": True,
                        "online": payload.get("online"),
                        "status": payload.get("status"),
                    }
                )
            except DevicePollFailedError as exc:
                failed += 1
                results.append(
                    {
                        "deviceId": str(device_id),
                        "success": False,
                        "error": exc.code,
                        "code": exc.code,
                    }
                )

        return {
            "polled": succeeded + failed,
            "succeeded": succeeded,
            "failed": failed,
            "skippedNoBinding": skipped,
            "results": results,
        }

    def _chip_health_from_driver(self, device: dict[str, Any]) -> dict[str, Any]:
        try:
            driver = self._registry.get_implementation(device["driver_key"])
        except DeviceDriverNotImplementedError:
            return {}
        fetch_identity = getattr(driver, "_fetch_identity", None)
        if not callable(fetch_identity):
            return {}
        try:
            identity = fetch_identity(device)
        except DeviceDriverError:
            return {}
        if not isinstance(identity, dict):
            return {}
        health: dict[str, Any] = {}
        for key in ("firmwareVersion", "uptimeMs", "freeHeap", "rssi", "wifiConnected"):
            if key in identity and identity.get(key) is not None:
                health[key] = identity[key]
        return health

    def _read_from_driver(self, device: dict[str, Any]):
        try:
            driver = self._registry.get_implementation(device["driver_key"])
        except DeviceDriverNotImplementedError as exc:
            raise DeviceDriverError(
                "driver_not_implemented",
                technical_detail=f"Driver not implemented: {device['driver_key']}",
            ) from exc
        return driver.read(device)


class DevicePollFailedError(DeviceDriverError):
    def __init__(
        self,
        code: str,
        *,
        technical_detail: str | None = None,
        connectivity: dict[str, Any] | None = None,
        **context: Any,
    ) -> None:
        super().__init__(code, technical_detail=technical_detail, **context)
        self.connectivity = connectivity or {}


__all__ = [
    "DeviceNotFoundError",
    "DevicePollFailedError",
    "DevicePollService",
]

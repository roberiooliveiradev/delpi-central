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
from production_pulse_app.domain.services.device_reading_delta_service import compute_delta_metrics
from production_pulse_app.domain.services.reading_serialization_service import reading_row_to_api
from production_pulse_app.infrastructure.persistence.repositories.postgres_device_binding_repository import (
    PostgresDeviceBindingRepository,
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
    ) -> None:
        self._devices = device_repository or PostgresDeviceRepository()
        self._bindings = binding_repository or PostgresDeviceBindingRepository()
        self._readings = reading_repository or PostgresDeviceReadingRepository()
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
        return json_safe(payload)

    def read_live(self, device_id: UUID) -> dict[str, Any]:
        device = self._require_device(device_id)
        has_binding = self._has_binding(device_id)
        try:
            reading = self._read_from_driver(device)
        except DeviceDriverError as exc:
            connectivity = resolve_connectivity_status(device, has_binding=has_binding)
            raise DevicePollFailedError(
                str(exc),
                code=exc.code,
                connectivity=connectivity,
            ) from exc
        return self._build_poll_payload(
            device,
            has_binding=has_binding,
            metrics=reading.metrics,
            recorded_at=reading.recorded_at,
        )

    def poll_and_persist(self, device_id: UUID, *, source: str = "manual") -> dict[str, Any]:
        device = self._require_device(device_id)
        has_binding = self._has_binding(device_id)

        try:
            reading = self._read_from_driver(device)
        except DeviceDriverError as exc:
            device = self._devices.record_poll_failure(device_id, error_message=str(exc))
            connectivity = resolve_connectivity_status(device, has_binding=has_binding)
            raise DevicePollFailedError(
                str(exc),
                code=exc.code,
                connectivity=connectivity,
            ) from exc

        previous_metrics = device.get("last_metrics") or {}
        delta_metrics, meta = compute_delta_metrics(
            driver_key=device["driver_key"],
            previous_metrics=previous_metrics if isinstance(previous_metrics, dict) else {},
            new_metrics=reading.metrics,
        )
        reading_row = self._readings.insert(
            device_id,
            metrics=reading.metrics,
            delta_metrics=delta_metrics,
            meta=meta,
            source=source,
            recorded_at=reading.recorded_at,
        )
        device = self._devices.record_poll_success(device_id, metrics=reading.metrics)
        return self._build_poll_payload(
            device,
            has_binding=has_binding,
            metrics=reading.metrics,
            recorded_at=reading_row["recorded_at"],
            delta_metrics=delta_metrics,
            reading_id=reading_row["id"],
            meta=meta,
        )

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
        page_size = min(max(1, page_size), 100)
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
                        "error": str(exc),
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

    def _read_from_driver(self, device: dict[str, Any]):
        try:
            driver = self._registry.get_implementation(device["driver_key"])
        except DeviceDriverNotImplementedError as exc:
            raise DeviceDriverError(
                f"Driver não implementado: {device['driver_key']}",
                code="driver_not_implemented",
            ) from exc
        return driver.read(device)


class DevicePollFailedError(DeviceDriverError):
    def __init__(
        self,
        message: str,
        *,
        code: str = "device_error",
        connectivity: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code=code)
        self.connectivity = connectivity or {}


__all__ = [
    "DeviceNotFoundError",
    "DevicePollFailedError",
    "DevicePollService",
]

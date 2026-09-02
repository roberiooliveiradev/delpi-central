from __future__ import annotations

from typing import Any
from uuid import UUID

from production_pulse_app.application.services.device_driver_registry_service import (
    DeviceDriverNotImplementedError,
    get_device_driver_registry,
)
from production_pulse_app.core.serialize import json_safe
from production_pulse_app.domain.errors import CommandNotSupportedError, DeviceDriverError
from production_pulse_app.domain.models.device_reading import CommandResult
from production_pulse_app.application.services.command_audit_actor_enrichment_service import (
    enrich_command_audit_actors,
)
from production_pulse_app.domain.services.command_serialization_service import command_row_to_api
from production_pulse_app.domain.services.device_reading_delta_service import compute_delta_metrics
from production_pulse_app.infrastructure.content.device_api_messages_content_service import (
    command_error_message,
    device_connectivity_codes,
    device_connectivity_user_message,
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


class DeviceCommandService:
    def __init__(
        self,
        device_repository: PostgresDeviceRepository | None = None,
        command_repository: PostgresDeviceCommandRepository | None = None,
        reading_repository: PostgresDeviceReadingRepository | None = None,
    ) -> None:
        self._devices = device_repository or PostgresDeviceRepository()
        self._commands = command_repository or PostgresDeviceCommandRepository()
        self._readings = reading_repository or PostgresDeviceReadingRepository()
        self._registry = get_device_driver_registry()

    def _require_device(self, device_id: UUID) -> dict[str, Any]:
        device = self._devices.get_by_id(device_id)
        if device is None:
            raise DeviceNotFoundError(str(device_id))
        return device

    def _assert_command_supported(self, driver_key: str, command_key: str) -> None:
        capabilities = self._registry.build_capabilities(driver_key)
        allowed = {item.strip().lower() for item in capabilities.get("commands") or []}
        normalized = (command_key or "").strip().lower()
        if normalized not in allowed:
            raise CommandNotSupportedError("unsupported_command")

    @staticmethod
    def _resolve_command_error_message(result: CommandResult) -> str | None:
        if result.success:
            return None
        code = result.error_code or "command_failed"
        if code in device_connectivity_codes():
            return device_connectivity_user_message(code, fallback=result.error_message)
        return command_error_message(code, fallback=result.error_message)

    def execute_command(
        self,
        device_id: UUID,
        command_key: str,
        *,
        actor_sub: str | None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        device = self._require_device(device_id)
        normalized_key = (command_key or "").strip().lower()
        self._assert_command_supported(device["driver_key"], normalized_key)

        try:
            driver = self._registry.get_implementation(device["driver_key"])
        except DeviceDriverNotImplementedError:
            result = CommandResult(success=False, error_code="driver_not_implemented")
        else:
            try:
                result = driver.execute(device, normalized_key, payload=payload)
            except DeviceDriverError as exc:
                result = CommandResult(success=False, error_code=exc.code)

        user_error_message = self._resolve_command_error_message(result)
        audit_row = self._commands.insert(
            device_id,
            command_key=normalized_key,
            issued_by=actor_sub or "unknown",
            success=result.success,
            error_message=user_error_message,
            request_payload=payload or {},
            response_payload=result.response_payload,
        )

        reading_id = None
        if result.success and result.metrics:
            previous_metrics = device.get("last_metrics") or {}
            delta_metrics, meta = compute_delta_metrics(
                driver_key=device["driver_key"],
                previous_metrics=previous_metrics if isinstance(previous_metrics, dict) else {},
                new_metrics=result.metrics,
            )
            reading_row = self._readings.insert(
                device_id,
                metrics=result.metrics,
                delta_metrics=delta_metrics,
                meta=meta,
                source="command",
            )
            self._devices.record_poll_success(device_id, metrics=result.metrics)
            reading_id = reading_row["id"]

        response = {
            "commandKey": normalized_key,
            "success": result.success,
            "metrics": result.metrics,
            "errorMessage": user_error_message,
            "commandId": str(audit_row["id"]),
        }
        if reading_id is not None:
            response["readingId"] = reading_id
        return json_safe(response)

    def list_commands(
        self,
        device_id: UUID,
        *,
        page: int = 1,
        page_size: int = 20,
        authorization: str | None = None,
    ) -> dict[str, Any]:
        self._require_device(device_id)
        page = max(1, page)
        page_size = min(max(1, page_size), 100)
        rows, total = self._commands.list_for_device(device_id, page=page, page_size=page_size)
        items = [json_safe(command_row_to_api(row)) for row in rows]
        enrich_command_audit_actors(items, authorization=authorization)
        return {
            "items": items,
            "pagination": {
                "page": page,
                "pageSize": page_size,
                "total": total,
            },
        }


__all__ = [
    "CommandNotSupportedError",
    "DeviceCommandService",
    "DeviceNotFoundError",
]

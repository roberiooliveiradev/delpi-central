from __future__ import annotations

from typing import Any
from uuid import UUID

from production_pulse_app.application.services.device_driver_registry_service import (
    get_device_driver_registry,
)
from production_pulse_app.core.serialize import json_safe
from production_pulse_app.domain.services.device_connectivity_status_service import (
    resolve_connectivity_status,
)
from production_pulse_app.domain.services.binding_serialization_service import binding_row_to_api
from production_pulse_app.domain.services.device_serialization_service import device_row_to_api
from production_pulse_app.domain.errors import DeviceValidationError
from production_pulse_app.application.services.device_config_push_service import (
    DeviceConfigPushService,
)
from production_pulse_app.domain.services.device_validation_service import (
    normalize_controller_code,
    normalize_debounce_ms,
    normalize_device_api_token,
    normalize_firmware_source,
    normalize_ip_address,
    normalize_name,
    normalize_wifi_ssid,
    resolve_driver,
    validate_branch,
    validate_poll_interval_ms,
)
from production_pulse_app.infrastructure.content.device_validation_content_service import (
    poll_interval_default,
)
from production_pulse_app.application.services.device_binding_service import DeviceBindingService
from production_pulse_app.application.services.device_period_delta_service import (
    DevicePeriodDeltaService,
)
from production_pulse_app.infrastructure.persistence.repositories.postgres_device_binding_repository import (
    PostgresDeviceBindingRepository,
)
from production_pulse_app.infrastructure.persistence.repositories.postgres_device_repository import (
    DeviceConflictError,
    DeviceNotFoundError,
    PostgresDeviceRepository,
)


class DeviceService:
    def __init__(
        self,
        repository: PostgresDeviceRepository | None = None,
        binding_repository: PostgresDeviceBindingRepository | None = None,
    ) -> None:
        self._repository = repository or PostgresDeviceRepository()
        self._binding_repository = binding_repository or PostgresDeviceBindingRepository()
        self._binding_service = DeviceBindingService(
            device_repository=self._repository,
            binding_repository=self._binding_repository,
        )
        self._period_delta_service = DevicePeriodDeltaService()
        self._driver_registry = get_device_driver_registry()
        self._config_push = DeviceConfigPushService()

    @staticmethod
    def _payload_has(payload: dict[str, Any], snake: str, camel: str) -> bool:
        return snake in payload or camel in payload

    @staticmethod
    def _payload_get(payload: dict[str, Any], snake: str, camel: str) -> Any:
        if snake in payload:
            return payload.get(snake)
        return payload.get(camel)

    def _resolve_device_config_fields(self, payload: dict[str, Any]) -> dict[str, Any]:
        fields: dict[str, Any] = {}
        if self._payload_has(payload, "wifi_ssid", "wifiSsid"):
            fields["wifi_ssid"] = normalize_wifi_ssid(
                self._payload_get(payload, "wifi_ssid", "wifiSsid")
            )
        if self._payload_has(payload, "debounce_ms", "debounceMs"):
            fields["debounce_ms"] = normalize_debounce_ms(
                self._payload_get(payload, "debounce_ms", "debounceMs")
            )
        if self._payload_has(payload, "api_token", "apiToken"):
            fields["device_api_token"] = normalize_device_api_token(
                self._payload_get(payload, "api_token", "apiToken")
            )
        return fields

    def _with_config_push(
        self,
        row: dict[str, Any],
        *,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        api_payload = json_safe(device_row_to_api(row))
        api_payload["deviceConfigPush"] = self._config_push.push_after_save(
            row,
            request_payload=payload,
        )
        return api_payload

    def _capabilities_for(self, driver_key: str) -> dict[str, Any]:
        return self._driver_registry.build_capabilities(driver_key)

    def _enrich_connectivity(self, row: dict[str, Any], *, has_binding: bool) -> dict[str, Any]:
        payload = json_safe(
            device_row_to_api(
                row,
                capabilities=self._capabilities_for(row["driver_key"]),
            )
        )
        connectivity = resolve_connectivity_status(row, has_binding=has_binding)
        payload["status"] = connectivity["status"]
        payload["online"] = connectivity["online"]
        payload["graceSeconds"] = connectivity["graceSeconds"]
        if "graceMs" in connectivity:
            payload["graceMs"] = connectivity["graceMs"]
        return payload

    def list_devices(
        self,
        *,
        branch: str | None = None,
        branches: list[str] | None = None,
        role: str | None = None,
        enabled: bool | None = None,
        search: str | None = None,
    ) -> dict[str, Any]:
        if branch:
            validate_branch(branch)
        rows = self._repository.list_devices(
            branch=branch,
            branches=branches,
            role_key=role,
            enabled=enabled,
            search=search,
        )
        device_ids = [row["id"] for row in rows]
        bindings_by_device = self._binding_repository.list_active_for_device_ids(device_ids)
        period_deltas = self._period_delta_service.build_period_deltas_for_devices(rows)
        items = []
        for row in rows:
            binding_row = bindings_by_device.get(row["id"])
            payload = self._enrich_connectivity(row, has_binding=binding_row is not None)
            payload["binding"] = binding_row_to_api(binding_row) if binding_row else None
            deltas = period_deltas.get(row["id"])
            if deltas:
                payload["periodDeltas"] = deltas
            items.append(payload)
        return {"items": items}

    def get_device(self, device_id: UUID) -> dict[str, Any]:
        row = self._repository.get_by_id(device_id)
        if row is None:
            raise DeviceNotFoundError(str(device_id))
        has_binding = self._binding_repository.get_active(device_id) is not None
        payload = self._enrich_connectivity(row, has_binding=has_binding)
        payload["binding"] = self._binding_service.get_active_binding(device_id)
        return payload

    def get_device_record(self, device_id: UUID) -> dict[str, Any]:
        row = self._repository.get_by_id(device_id)
        if row is None:
            raise DeviceNotFoundError(str(device_id))
        return row

    def create_device(self, payload: dict[str, Any], *, actor_sub: str | None) -> dict[str, Any]:
        branch = validate_branch(payload.get("branch", ""))
        name = normalize_name(payload.get("name", ""))
        ip_address = normalize_ip_address(payload.get("ip_address") or payload.get("ipAddress", ""))
        driver = resolve_driver(payload.get("driver_key") or payload.get("driverKey", ""))
        poll_interval = validate_poll_interval_ms(
            float(
                payload.get("poll_interval_ms")
                or payload.get("pollIntervalMs")
                or poll_interval_default()
            )
        )
        enabled = bool(payload.get("enabled", True))
        controller_code = normalize_controller_code(
            payload.get("controller_code")
            if "controller_code" in payload
            else payload.get("controllerCode")
        )
        firmware_source = normalize_firmware_source(
            payload.get("firmware_source")
            if "firmware_source" in payload
            else payload.get("firmwareSource")
        )
        config_fields = self._resolve_device_config_fields(payload)
        row = self._repository.create(
            branch=branch,
            name=name,
            ip_address=ip_address,
            driver_key=driver.driver_key,
            role_key=driver.role_key,
            enabled=enabled,
            poll_interval_ms=poll_interval,
            controller_code=controller_code,
            firmware_source=firmware_source,
            wifi_ssid=config_fields.get("wifi_ssid"),
            debounce_ms=config_fields.get("debounce_ms"),
            device_api_token=config_fields.get("device_api_token"),
            actor_sub=actor_sub,
        )
        return self._with_config_push(row, payload=payload)

    def replace_device(
        self,
        device_id: UUID,
        payload: dict[str, Any],
        *,
        actor_sub: str | None,
    ) -> dict[str, Any]:
        branch = validate_branch(payload.get("branch", ""))
        name = normalize_name(payload.get("name", ""))
        ip_address = normalize_ip_address(payload.get("ip_address") or payload.get("ipAddress", ""))
        driver = resolve_driver(payload.get("driver_key") or payload.get("driverKey", ""))
        poll_interval = validate_poll_interval_ms(
            float(
                payload.get("poll_interval_ms")
                or payload.get("pollIntervalMs")
                or poll_interval_default()
            )
        )
        enabled = bool(payload.get("enabled", True))
        controller_code = normalize_controller_code(
            payload.get("controller_code")
            if "controller_code" in payload
            else payload.get("controllerCode")
        )
        firmware_source = normalize_firmware_source(
            payload.get("firmware_source")
            if "firmware_source" in payload
            else payload.get("firmwareSource")
        )
        existing = self._repository.get_by_id(device_id)
        if existing is None:
            raise DeviceNotFoundError(str(device_id))
        config_fields = self._resolve_device_config_fields(payload)
        wifi_ssid = (
            config_fields["wifi_ssid"]
            if "wifi_ssid" in config_fields
            else existing.get("wifi_ssid")
        )
        debounce_ms = (
            config_fields["debounce_ms"]
            if "debounce_ms" in config_fields
            else existing.get("debounce_ms")
        )
        device_api_token = (
            config_fields["device_api_token"]
            if "device_api_token" in config_fields
            else existing.get("device_api_token")
        )
        row = self._repository.replace(
            device_id,
            branch=branch,
            name=name,
            ip_address=ip_address,
            driver_key=driver.driver_key,
            role_key=driver.role_key,
            enabled=enabled,
            poll_interval_ms=poll_interval,
            controller_code=controller_code,
            firmware_source=firmware_source,
            wifi_ssid=wifi_ssid,
            debounce_ms=debounce_ms,
            device_api_token=device_api_token,
            actor_sub=actor_sub,
        )
        return self._with_config_push(row, payload=payload)

    def patch_device(
        self,
        device_id: UUID,
        payload: dict[str, Any],
        *,
        actor_sub: str | None,
    ) -> dict[str, Any]:
        updates: dict[str, Any] = {}
        if "branch" in payload:
            updates["branch"] = validate_branch(payload["branch"])
        if "name" in payload:
            updates["name"] = normalize_name(payload["name"])
        if "ip_address" in payload or "ipAddress" in payload:
            updates["ip_address"] = normalize_ip_address(
                payload.get("ip_address") or payload.get("ipAddress", "")
            )
        if "controller_code" in payload or "controllerCode" in payload:
            updates["controller_code"] = normalize_controller_code(
                payload.get("controller_code")
                if "controller_code" in payload
                else payload.get("controllerCode")
            )
        if "firmware_source" in payload or "firmwareSource" in payload:
            updates["firmware_source"] = normalize_firmware_source(
                payload.get("firmware_source")
                if "firmware_source" in payload
                else payload.get("firmwareSource")
            )
        updates.update(self._resolve_device_config_fields(payload))
        if "driver_key" in payload or "driverKey" in payload:
            driver = resolve_driver(payload.get("driver_key") or payload.get("driverKey", ""))
            updates["driver_key"] = driver.driver_key
            updates["role_key"] = driver.role_key
        if "enabled" in payload:
            updates["enabled"] = bool(payload["enabled"])
        if "poll_interval_ms" in payload or "pollIntervalMs" in payload:
            updates["poll_interval_ms"] = validate_poll_interval_ms(
                float(payload.get("poll_interval_ms") or payload.get("pollIntervalMs"))
            )
        row = self._repository.patch(device_id, updates=updates, actor_sub=actor_sub)
        return self._with_config_push(row, payload=payload)

    def delete_device(self, device_id: UUID, *, actor_sub: str | None) -> dict[str, Any]:
        row = self._repository.soft_delete(device_id, actor_sub=actor_sub)
        return json_safe(device_row_to_api(row))


__all__ = [
    "DeviceConflictError",
    "DeviceNotFoundError",
    "DeviceService",
    "DeviceValidationError",
]

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from production_pulse_app.domain.errors import DeviceValidationError
from production_pulse_app.domain.ports.device_driver_port import DeviceDriver
from production_pulse_app.infrastructure.persistence.repositories.postgres_device_driver_repository import (
    PostgresDeviceDriverRepository,
)
from production_pulse_app.application.services.device_driver_catalog_service import (
    row_to_definition,
)


class DeviceDriverNotImplementedError(RuntimeError):
    pass


@dataclass(frozen=True)
class ResolvedDriverDefinition:
    driver_key: str
    role_key: str
    definition: dict[str, Any]
    protocol_kind: str | None = None


class DeviceDriverRegistryService:
    def __init__(self, repo: PostgresDeviceDriverRepository | None = None) -> None:
        self._implementations: dict[str, DeviceDriver] = {}
        self._repo = repo or PostgresDeviceDriverRepository()

    def register_implementation(self, driver: DeviceDriver) -> None:
        self._implementations[driver.driver_key] = driver

    def get_implementation(self, driver_key: str) -> DeviceDriver:
        normalized = (driver_key or "").strip()
        cached = self._implementations.get(normalized)
        if cached is not None:
            return cached

        row = self._repo.get_by_key(normalized)
        if row is None:
            raise DeviceDriverNotImplementedError(
                f"Implementação de driver não registrada: {normalized}"
            )
        protocol = str(row.get("protocol_kind") or "").strip()
        impl = self._build_protocol_implementation(normalized, protocol)
        self._implementations[normalized] = impl
        return impl

    def _build_protocol_implementation(self, driver_key: str, protocol_kind: str) -> DeviceDriver:
        # Lazy imports avoid circular dependency with Http*Driver → registry.poll_timeout_ms.
        if protocol_kind == "http_counter":
            from production_pulse_app.infrastructure.drivers.http_counter_driver import (
                HttpCounterDriver,
            )

            return HttpCounterDriver(driver_key=driver_key)
        if protocol_kind == "http_gauge":
            from production_pulse_app.infrastructure.drivers.http_gauge_driver import (
                HttpGaugeDriver,
            )

            return HttpGaugeDriver(driver_key=driver_key)
        raise DeviceDriverNotImplementedError(
            f"protocol_kind sem implementação: {protocol_kind} ({driver_key})"
        )

    def resolve_driver(self, driver_key: str) -> ResolvedDriverDefinition:
        normalized = (driver_key or "").strip()
        if not normalized:
            raise DeviceValidationError("driver_key_required")

        row = self._repo.get_by_key(normalized)
        if row is None:
            raise DeviceValidationError("unknown_driver", driver=normalized)

        definition = row_to_definition(row)
        role_key = str(definition.get("roleKey") or "").strip()
        if not role_key:
            raise DeviceValidationError("driver_missing_role_key", driver=normalized)

        return ResolvedDriverDefinition(
            driver_key=normalized,
            role_key=role_key,
            definition=definition,
            protocol_kind=str(row.get("protocol_kind") or "") or None,
        )

    def list_catalog_drivers(self, *, include_archived: bool = False) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for row in self._repo.list_drivers(include_archived=include_archived):
            if not include_archived and row.get("archived_at") is not None:
                continue
            items.append(self.driver_definition_to_api(row["driver_key"], row_to_definition(row)))
        return items

    def driver_definition_to_api(self, driver_key: str, definition: dict[str, Any]) -> dict[str, Any]:
        return {
            "key": driver_key,
            **definition,
        }

    def build_capabilities(self, driver_key: str) -> dict[str, Any]:
        resolved = self.resolve_driver(driver_key)
        definition = resolved.definition
        metrics = definition.get("metrics") or []
        metric_keys: list[str] = []
        if isinstance(metrics, list):
            for metric in metrics:
                if isinstance(metric, dict):
                    key = str(metric.get("key") or "").strip()
                    if key:
                        metric_keys.append(key)

        commands_raw = definition.get("commands") or []
        commands = (
            [str(item).strip() for item in commands_raw if str(item).strip()]
            if isinstance(commands_raw, list)
            else []
        )

        operator_surface = str(definition.get("operatorSurface") or "").strip()
        payload: dict[str, Any] = {
            "metrics": metric_keys,
            "commands": commands,
            "operatorSurface": operator_surface,
        }
        thresholds = definition.get("thresholds") or {}
        if isinstance(thresholds, dict) and thresholds:
            payload["thresholds"] = thresholds
        return payload

    def poll_timeout_ms(self, driver_key: str) -> int:
        resolved = self.resolve_driver(driver_key)
        poll = resolved.definition.get("poll") or {}
        if isinstance(poll, dict):
            try:
                return max(500, int(poll.get("timeoutMs") or 3000))
            except (TypeError, ValueError):
                pass
        return 3000

    def schema_version(self) -> int:
        return 2

    def clear_implementations_for_tests(self) -> None:
        self._implementations.clear()


_default_registry = DeviceDriverRegistryService()


def get_device_driver_registry() -> DeviceDriverRegistryService:
    return _default_registry


__all__ = [
    "DeviceDriverNotImplementedError",
    "DeviceDriverRegistryService",
    "ResolvedDriverDefinition",
    "get_device_driver_registry",
]

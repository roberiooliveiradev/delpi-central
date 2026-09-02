from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from production_pulse_app.domain.ports.device_driver_port import DeviceDriver
from production_pulse_app.domain.errors import DeviceValidationError
from production_pulse_app.infrastructure.content.device_drivers_content_service import (
    get_driver_definitions,
    load_device_drivers_catalog,
)


class DeviceDriverNotImplementedError(RuntimeError):
    pass


@dataclass(frozen=True)
class ResolvedDriverDefinition:
    driver_key: str
    role_key: str
    definition: dict[str, Any]


class DeviceDriverRegistryService:
    def __init__(self) -> None:
        self._implementations: dict[str, DeviceDriver] = {}

    def register_implementation(self, driver: DeviceDriver) -> None:
        self._implementations[driver.driver_key] = driver

    def get_implementation(self, driver_key: str) -> DeviceDriver:
        normalized = (driver_key or "").strip()
        impl = self._implementations.get(normalized)
        if impl is None:
            raise DeviceDriverNotImplementedError(
                f"Implementação de driver não registrada: {normalized}"
            )
        return impl

    def resolve_driver(self, driver_key: str) -> ResolvedDriverDefinition:
        normalized = (driver_key or "").strip()
        if not normalized:
            raise DeviceValidationError("driver_key é obrigatório.")

        definition = get_driver_definitions().get(normalized)
        if definition is None:
            raise DeviceValidationError(f"Driver desconhecido: {normalized}")

        role_key = str(definition.get("roleKey") or "").strip()
        if not role_key:
            raise DeviceValidationError(f"Driver '{normalized}' sem roleKey no registry.")

        return ResolvedDriverDefinition(
            driver_key=normalized,
            role_key=role_key,
            definition=definition,
        )

    def list_catalog_drivers(self) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for key in sorted(get_driver_definitions().keys()):
            resolved = self.resolve_driver(key)
            items.append(self.driver_definition_to_api(key, resolved.definition))
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
        commands = [str(item).strip() for item in commands_raw if str(item).strip()] if isinstance(
            commands_raw, list
        ) else []

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
        catalog = load_device_drivers_catalog()
        try:
            return int(catalog.get("schemaVersion") or 1)
        except (TypeError, ValueError):
            return 1

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

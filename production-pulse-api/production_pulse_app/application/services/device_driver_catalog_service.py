from __future__ import annotations

import re
from typing import Any

from production_pulse_app.domain.errors import ContentCodedError
from production_pulse_app.infrastructure.persistence.repositories.postgres_device_driver_repository import (
    PROTOCOL_KINDS,
    DeviceDriverConflictError,
    DeviceDriverNotFoundError,
    PostgresDeviceDriverRepository,
)

_DRIVER_KEY_RE = re.compile(r"^[a-z][a-z0-9_]{1,39}$")
_ROLE_KEYS = frozenset({"pulse_counter", "process_gauge", "telemetry"})
_OPERATOR_SURFACES = frozenset(
    {"counter_pad", "gauge_readout", "temperature_focus", "rotation_ring", "telemetry_stack"}
)
_PROTOCOL_DEFAULTS: dict[str, dict[str, Any]] = {
    "http_counter": {
        "role_key": "pulse_counter",
        "operator_surface": "counter_pad",
        "commands": [
            "increment",
            "decrement",
            "reset",
            "set",
            "configure",
            "reboot",
            "factory_reset",
        ],
        "metrics": [
            {
                "key": "counter",
                "type": "integer",
                "monotonic": True,
                "labelPt": "Golpes",
                "primary": True,
                "icon": "Hash",
            }
        ],
    },
    "http_gauge": {
        "role_key": "process_gauge",
        "operator_surface": "gauge_readout",
        "commands": [],
        "metrics": [
            {
                "key": "rpm",
                "type": "number",
                "monotonic": False,
                "labelPt": "Rotação",
                "unit": "rpm",
                "primary": True,
                "icon": "Gauge",
            },
            {
                "key": "temperature_c",
                "type": "number",
                "monotonic": False,
                "labelPt": "Temperatura",
                "unit": "°C",
                "primary": False,
                "icon": "Thermometer",
            },
        ],
    },
}


def row_to_definition(row: dict[str, Any]) -> dict[str, Any]:
    """Map DB row to the camelCase definition shape historically used by the registry."""
    definition: dict[str, Any] = {
        "protocolKind": row.get("protocol_kind"),
        "roleKey": row.get("role_key"),
        "labelPt": row.get("label_pt"),
        "descriptionPt": row.get("description_pt") or "",
        "metrics": row.get("metrics") or [],
        "commands": row.get("commands") or [],
        "operatorSurface": row.get("operator_surface"),
        "operatorEligible": bool(row.get("operator_eligible", True)),
        "poll": row.get("poll") or {"timeoutMs": 3000},
        "thresholds": row.get("thresholds") or {},
        "archivedAt": row["archived_at"].isoformat() if row.get("archived_at") else None,
    }
    if row.get("counter_restore") is not None:
        definition["counterRestore"] = row["counter_restore"]
    return definition


def row_to_api(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "key": row["driver_key"],
        **row_to_definition(row),
        "createdAt": row["created_at"].isoformat() if row.get("created_at") else None,
        "updatedAt": row["updated_at"].isoformat() if row.get("updated_at") else None,
    }


class DeviceDriverCatalogService:
    def __init__(self, repo: PostgresDeviceDriverRepository | None = None) -> None:
        self._repo = repo or PostgresDeviceDriverRepository()

    def list_drivers(self, *, include_archived: bool = False) -> list[dict[str, Any]]:
        return [row_to_api(row) for row in self._repo.list_drivers(include_archived=include_archived)]

    def get_driver(self, driver_key: str) -> dict[str, Any]:
        row = self._repo.get_by_key((driver_key or "").strip())
        if row is None:
            raise ContentCodedError("unknown_driver")
        return row_to_api(row)

    def create_driver(self, payload: dict[str, Any]) -> dict[str, Any]:
        normalized = self._normalize_create(payload)
        try:
            row = self._repo.create(normalized)
        except DeviceDriverConflictError as exc:
            raise ContentCodedError("driverKeyExists") from exc
        return row_to_api(row)

    def update_driver(self, driver_key: str, payload: dict[str, Any]) -> dict[str, Any]:
        key = (driver_key or "").strip()
        existing = self._repo.get_by_key(key)
        if existing is None:
            raise ContentCodedError("unknown_driver")
        updates = self._normalize_update(payload)
        try:
            row = self._repo.update(key, updates)
        except DeviceDriverNotFoundError as exc:
            raise ContentCodedError("unknown_driver") from exc
        return row_to_api(row)

    def archive_driver(self, driver_key: str) -> dict[str, Any]:
        try:
            row = self._repo.archive((driver_key or "").strip())
        except DeviceDriverNotFoundError as exc:
            raise ContentCodedError("unknown_driver") from exc
        return row_to_api(row)

    def unarchive_driver(self, driver_key: str) -> dict[str, Any]:
        try:
            row = self._repo.unarchive((driver_key or "").strip())
        except DeviceDriverNotFoundError as exc:
            raise ContentCodedError("unknown_driver") from exc
        return row_to_api(row)

    def _normalize_create(self, payload: dict[str, Any]) -> dict[str, Any]:
        key = str(payload.get("driverKey") or payload.get("driver_key") or "").strip()
        if not _DRIVER_KEY_RE.match(key):
            raise ContentCodedError("invalidDriverKey")
        protocol = str(payload.get("protocolKind") or payload.get("protocol_kind") or "").strip()
        if protocol not in PROTOCOL_KINDS:
            raise ContentCodedError("invalidProtocolKind")
        defaults = _PROTOCOL_DEFAULTS[protocol]
        role = str(payload.get("roleKey") or payload.get("role_key") or defaults["role_key"]).strip()
        if role not in _ROLE_KEYS:
            raise ContentCodedError("validation_error")
        label = str(payload.get("labelPt") or payload.get("label_pt") or "").strip()
        if not label:
            raise ContentCodedError("validation_error")
        surface = str(
            payload.get("operatorSurface")
            or payload.get("operator_surface")
            or defaults["operator_surface"]
        ).strip()
        if surface not in _OPERATOR_SURFACES:
            raise ContentCodedError("validation_error")
        metrics = payload.get("metrics")
        if metrics is None:
            metrics = defaults["metrics"]
        if not isinstance(metrics, list) or not metrics:
            raise ContentCodedError("validation_error")
        commands = payload.get("commands")
        if commands is None:
            commands = list(defaults["commands"])
        if not isinstance(commands, list):
            raise ContentCodedError("validation_error")
        poll = payload.get("poll") or {"timeoutMs": 3000}
        if not isinstance(poll, dict):
            raise ContentCodedError("validation_error")
        thresholds = payload.get("thresholds") or {}
        if not isinstance(thresholds, dict):
            raise ContentCodedError("validation_error")
        counter_restore = payload.get("counterRestore") or payload.get("counter_restore")
        eligible = payload.get("operatorEligible")
        if eligible is None:
            eligible = payload.get("operator_eligible", True)
        return {
            "driver_key": key,
            "protocol_kind": protocol,
            "role_key": role,
            "label_pt": label,
            "description_pt": str(
                payload.get("descriptionPt") or payload.get("description_pt") or ""
            ).strip()
            or None,
            "metrics": metrics,
            "commands": [str(c).strip() for c in commands if str(c).strip()],
            "operator_surface": surface,
            "operator_eligible": bool(eligible),
            "poll": poll,
            "thresholds": thresholds,
            "counter_restore": counter_restore,
        }

    def _normalize_update(self, payload: dict[str, Any]) -> dict[str, Any]:
        updates: dict[str, Any] = {}
        mapping = {
            "roleKey": "role_key",
            "role_key": "role_key",
            "labelPt": "label_pt",
            "label_pt": "label_pt",
            "descriptionPt": "description_pt",
            "description_pt": "description_pt",
            "metrics": "metrics",
            "commands": "commands",
            "operatorSurface": "operator_surface",
            "operator_surface": "operator_surface",
            "operatorEligible": "operator_eligible",
            "operator_eligible": "operator_eligible",
            "poll": "poll",
            "thresholds": "thresholds",
            "counterRestore": "counter_restore",
            "counter_restore": "counter_restore",
        }
        for src, dest in mapping.items():
            if src in payload:
                updates[dest] = payload[src]
        if "role_key" in updates and updates["role_key"] not in _ROLE_KEYS:
            raise ContentCodedError("validation_error")
        if "operator_surface" in updates and updates["operator_surface"] not in _OPERATOR_SURFACES:
            raise ContentCodedError("validation_error")
        if "label_pt" in updates and not str(updates["label_pt"] or "").strip():
            raise ContentCodedError("validation_error")
        if "metrics" in updates and (
            not isinstance(updates["metrics"], list) or not updates["metrics"]
        ):
            raise ContentCodedError("validation_error")
        return updates

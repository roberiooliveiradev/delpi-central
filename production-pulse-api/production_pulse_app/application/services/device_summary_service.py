from __future__ import annotations

from typing import Any

from production_pulse_app.domain.services.device_connectivity_status_service import (
    resolve_connectivity_status,
)
from production_pulse_app.infrastructure.persistence.repositories.postgres_device_binding_repository import (
    PostgresDeviceBindingRepository,
)
from production_pulse_app.infrastructure.persistence.repositories.postgres_device_repository import (
    PostgresDeviceRepository,
)


class DeviceSummaryService:
    def __init__(
        self,
        device_repository: PostgresDeviceRepository | None = None,
        binding_repository: PostgresDeviceBindingRepository | None = None,
    ) -> None:
        self._devices = device_repository or PostgresDeviceRepository()
        self._bindings = binding_repository or PostgresDeviceBindingRepository()

    def build_summary(
        self,
        *,
        branch: str | None = None,
        branches: list[str] | None = None,
    ) -> dict[str, Any]:
        rows = self._devices.list_devices(branch=branch, branches=branches, enabled=True)
        device_ids = [row["id"] for row in rows]
        bound_ids = self._bindings.active_device_ids_among(device_ids)

        total = len(rows)
        online = 0
        offline = 0
        without_binding = 0

        for row in rows:
            has_binding = row["id"] in bound_ids
            if not has_binding:
                without_binding += 1
                continue
            connectivity = resolve_connectivity_status(row, has_binding=True)
            if connectivity.get("online"):
                online += 1
            elif connectivity.get("status") == "offline":
                offline += 1

        payload: dict[str, Any] = {
            "total": total,
            "online": online,
            "offline": offline,
            "withoutBinding": without_binding,
        }
        if branch:
            payload["branch"] = branch
        elif branches:
            payload["branches"] = branches
        return payload
from __future__ import annotations

from typing import Any
from uuid import UUID

from production_pulse_app.application.services.work_center_catalog_service import (
    WorkCenterCatalogService,
)
from production_pulse_app.domain.services.binding_serialization_service import binding_row_to_api
from production_pulse_app.domain.services.binding_validation_service import (
    BindingValidationError,
    compose_placement_key_base,
    compose_placement_label,
    normalize_binding_input,
)
from production_pulse_app.infrastructure.persistence.repositories.postgres_device_binding_repository import (
    BindingNotFoundError,
    PostgresDeviceBindingRepository,
)
from production_pulse_app.infrastructure.persistence.repositories.postgres_device_repository import (
    DeviceNotFoundError,
    PostgresDeviceRepository,
)


class DeviceBindingService:
    def __init__(
        self,
        device_repository: PostgresDeviceRepository | None = None,
        binding_repository: PostgresDeviceBindingRepository | None = None,
        work_center_catalog: WorkCenterCatalogService | None = None,
    ) -> None:
        self._devices = device_repository or PostgresDeviceRepository()
        self._bindings = binding_repository or PostgresDeviceBindingRepository()
        self._work_centers = work_center_catalog or WorkCenterCatalogService()

    def _require_device(self, device_id: UUID) -> dict[str, Any]:
        device = self._devices.get_by_id(device_id)
        if device is None:
            raise DeviceNotFoundError(str(device_id))
        return device

    def get_active_binding(self, device_id: UUID) -> dict[str, Any] | None:
        self._require_device(device_id)
        row = self._bindings.get_active(device_id)
        if row is None:
            return None
        return binding_row_to_api(row)

    def upsert_binding(
        self,
        device_id: UUID,
        payload: dict[str, Any],
        *,
        actor_sub: str | None,
        authorization: str | None = None,
    ) -> dict[str, Any]:
        device = self._require_device(device_id)
        binding_input = normalize_binding_input(payload)
        if binding_input.work_center_code:
            self._work_centers.validate_work_center_code(
                branch=device["branch"],
                work_center_code=binding_input.work_center_code,
                authorization=authorization,
            )
        placement_label = compose_placement_label(
            binding_input,
            device_name=device["name"],
        )
        base_key = compose_placement_key_base(
            binding_input,
            branch=device["branch"],
            device_id=device_id,
        )
        placement_key = self._bindings.resolve_unique_placement_key(base_key, device_id)

        active = self._bindings.get_active(device_id)
        if active is not None:
            self._bindings.close_active(device_id, actor_sub=actor_sub)

        row = self._bindings.create(
            device_id,
            binding_input,
            placement_label=placement_label,
            placement_key=placement_key,
            actor_sub=actor_sub,
        )
        return binding_row_to_api(row)

    def delete_active_binding(self, device_id: UUID, *, actor_sub: str | None) -> None:
        self._require_device(device_id)
        active = self._bindings.get_active(device_id)
        if active is None:
            raise BindingNotFoundError(str(device_id))
        self._bindings.close_active(device_id, actor_sub=actor_sub)

    def list_binding_history(
        self,
        device_id: UUID,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        self._require_device(device_id)
        page = max(1, page)
        page_size = min(max(1, page_size), 100)
        rows, total = self._bindings.list_history(device_id, page=page, page_size=page_size)
        return {
            "items": [binding_row_to_api(row) for row in rows],
            "pagination": {
                "page": page,
                "pageSize": page_size,
                "total": total,
            },
        }


__all__ = [
    "BindingNotFoundError",
    "BindingValidationError",
    "DeviceBindingService",
]

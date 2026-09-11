from __future__ import annotations

import logging
from typing import Any

from production_pulse_app.application.services.device_driver_catalog_service import (
    DeviceDriverCatalogService,
)
from production_pulse_app.application.services.device_driver_registry_service import (
    get_device_driver_registry,
)
from production_pulse_app.domain.errors import ContentCodedError
from production_pulse_app.infrastructure.persistence.repositories.postgres_device_driver_repository import (
    DeviceDriverNotFoundError,
    PostgresDeviceDriverRepository,
)

logger = logging.getLogger(__name__)


class DriverDeletionService:
    def __init__(
        self,
        repository: PostgresDeviceDriverRepository | None = None,
        catalog: DeviceDriverCatalogService | None = None,
    ) -> None:
        self._repo = repository or PostgresDeviceDriverRepository()
        self._catalog = catalog or DeviceDriverCatalogService(repo=self._repo)

    def get_deletion_impact(self, driver_key: str) -> dict[str, Any]:
        key = (driver_key or "").strip()
        row = self._repo.get_by_key(key)
        if row is None:
            raise DeviceDriverNotFoundError(key)
        device_refs = self._repo.count_device_refs(key)
        firmware_refs = self._repo.count_firmware_refs(key)
        blockers: list[dict[str, Any]] = []
        if device_refs > 0:
            blockers.append({"code": "driverHasDevices", "count": device_refs})
        if firmware_refs > 0:
            blockers.append({"code": "driverHasFirmwares", "count": firmware_refs})
        return {
            "canDelete": len(blockers) == 0,
            "blockers": blockers,
            "dependencies": {
                "devices": device_refs,
                "firmwares": firmware_refs,
            },
            "displayName": row.get("label_pt") or key,
            "driverKey": key,
        }

    def delete_permanently(self, driver_key: str, *, actor_sub: str | None) -> dict[str, Any]:
        impact = self.get_deletion_impact(driver_key)
        if not impact["canDelete"]:
            code = impact["blockers"][0]["code"]
            logger.info(
                "hard_delete_blocked entity_type=driver entity_key=%s code=%s actor_sub=%s",
                driver_key,
                code,
                actor_sub,
            )
            raise ContentCodedError(code)

        key = impact["driverKey"]
        # Revalidate refs.
        if self._repo.count_device_refs(key) > 0 or self._repo.count_firmware_refs(key) > 0:
            raise ContentCodedError("deleteDependencyConflict")

        deleted = self._repo.hard_delete(key)
        if not deleted:
            raise DeviceDriverNotFoundError(key)

        get_device_driver_registry().invalidate_implementation(key)

        logger.info(
            "driver_hard_deleted entity_key=%s actor_sub=%s dependencies=%s",
            key,
            actor_sub,
            impact["dependencies"],
        )
        return {
            "deleted": True,
            "driverKey": key,
            "dependencies": impact["dependencies"],
        }

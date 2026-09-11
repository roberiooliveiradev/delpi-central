from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from production_pulse_app.domain.errors import ContentCodedError
from production_pulse_app.infrastructure.persistence.repositories.postgres_device_repository import (
    DeviceNotFoundError,
    PostgresDeviceRepository,
)
from production_pulse_app.infrastructure.persistence.repositories.postgres_firmware_repository import (
    PostgresFirmwareUpdateJobRepository,
)

logger = logging.getLogger(__name__)


class DeviceDeletionService:
    def __init__(
        self,
        device_repository: PostgresDeviceRepository | None = None,
        job_repository: PostgresFirmwareUpdateJobRepository | None = None,
    ) -> None:
        self._devices = device_repository or PostgresDeviceRepository()
        self._jobs = job_repository or PostgresFirmwareUpdateJobRepository()

    def get_deletion_impact(self, device_id: UUID) -> dict[str, Any]:
        row = self._devices.get_by_id(device_id)
        if row is None:
            raise DeviceNotFoundError(str(device_id))
        deps = self._devices.count_deletion_dependencies(device_id)
        blockers: list[dict[str, Any]] = []
        if deps["activeOtaTargets"] > 0:
            blockers.append(
                {
                    "code": "deviceHasActiveOta",
                    "count": deps["activeOtaTargets"],
                }
            )
        return {
            "canDelete": len(blockers) == 0,
            "blockers": blockers,
            "dependencies": {
                "bindings": deps["bindings"],
                "readings": deps["readings"],
                "rollups": deps["rollups"],
                "commands": deps["commands"],
                "otaTargets": deps["otaTargets"],
            },
            "displayName": row.get("name"),
            "id": str(device_id),
        }

    def delete_permanently(self, device_id: UUID, *, actor_sub: str | None) -> dict[str, Any]:
        impact = self.get_deletion_impact(device_id)
        if not impact["canDelete"]:
            code = impact["blockers"][0]["code"]
            logger.info(
                "hard_delete_blocked entity_type=device entity_id=%s code=%s actor_sub=%s",
                device_id,
                code,
                actor_sub,
            )
            raise ContentCodedError(code)

        job_ids = self._devices.list_ota_job_ids_for_device(device_id)
        # Re-check active OTA under the same moment as delete.
        deps = self._devices.count_deletion_dependencies(device_id)
        if deps["activeOtaTargets"] > 0:
            raise ContentCodedError("deviceHasActiveOta")

        deleted = self._devices.hard_delete(device_id)
        if not deleted:
            raise DeviceNotFoundError(str(device_id))

        for job_id in job_ids:
            try:
                self._jobs.maybe_finish_job(job_id)
            except Exception:
                logger.exception(
                    "maybe_finish_job_after_device_hard_delete_failed job_id=%s device_id=%s",
                    job_id,
                    device_id,
                )

        logger.info(
            "device_hard_deleted entity_id=%s actor_sub=%s dependencies=%s",
            device_id,
            actor_sub,
            impact["dependencies"],
        )
        return {
            "deleted": True,
            "id": str(device_id),
            "dependencies": impact["dependencies"],
        }

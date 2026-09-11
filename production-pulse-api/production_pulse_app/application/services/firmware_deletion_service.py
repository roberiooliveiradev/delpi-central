from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from production_pulse_app.domain.errors import ContentCodedError
from production_pulse_app.infrastructure.persistence.repositories.postgres_firmware_repository import (
    FirmwareNotFoundError,
    PostgresFirmwareRepository,
)
from production_pulse_app.infrastructure.storage.firmware_artifact_storage import (
    FirmwareArtifactStorage,
)

logger = logging.getLogger(__name__)


class FirmwareDeletionService:
    def __init__(
        self,
        repository: PostgresFirmwareRepository | None = None,
        storage: FirmwareArtifactStorage | None = None,
    ) -> None:
        self._repo = repository or PostgresFirmwareRepository()
        self._storage = storage or FirmwareArtifactStorage()

    def get_deletion_impact(self, firmware_id: UUID) -> dict[str, Any]:
        row = self._repo.get_by_id(firmware_id)
        if row is None:
            raise FirmwareNotFoundError(str(firmware_id))
        deps = self._repo.count_deletion_dependencies(firmware_id)
        blockers: list[dict[str, Any]] = []
        if deps["jobs"] > 0:
            blockers.append({"code": "firmwareHasUpdateHistory", "count": deps["jobs"]})
        if deps["activeTargets"] > 0:
            blockers.append(
                {"code": "firmwareHasActiveTargets", "count": deps["activeTargets"]}
            )
        if deps["installedDevices"] > 0:
            blockers.append(
                {
                    "code": "firmwareInstalledOnDevices",
                    "count": deps["installedDevices"],
                }
            )
        return {
            "canDelete": len(blockers) == 0,
            "blockers": blockers,
            "dependencies": {
                "jobs": deps["jobs"],
                "activeTargets": deps["activeTargets"],
                "installedDevices": deps["installedDevices"],
                "hasArtifact": bool(row.get("artifact_path")),
                "hasSource": bool(row.get("source_text")),
            },
            "displayName": row.get("display_name") or row.get("firmware_key"),
            "firmwareKey": row.get("firmware_key"),
            "version": row.get("version"),
            "id": str(firmware_id),
        }

    def delete_permanently(self, firmware_id: UUID, *, actor_sub: str | None) -> dict[str, Any]:
        impact = self.get_deletion_impact(firmware_id)
        if not impact["canDelete"]:
            code = impact["blockers"][0]["code"]
            logger.info(
                "hard_delete_blocked entity_type=firmware entity_id=%s code=%s actor_sub=%s",
                firmware_id,
                code,
                actor_sub,
            )
            raise ContentCodedError(code)

        row = self._repo.get_by_id(firmware_id)
        if row is None:
            raise FirmwareNotFoundError(str(firmware_id))
        artifact_path = row.get("artifact_path")

        # Revalidate immediately before delete (race with new job).
        deps = self._repo.count_deletion_dependencies(firmware_id)
        if deps["jobs"] > 0 or deps["activeTargets"] > 0 or deps["installedDevices"] > 0:
            raise ContentCodedError("deleteDependencyConflict")

        deleted = self._repo.hard_delete(firmware_id)
        if deleted is None:
            raise FirmwareNotFoundError(str(firmware_id))

        if artifact_path:
            try:
                self._storage.delete_relative(str(artifact_path))
            except Exception:
                logger.exception(
                    "firmware_artifact_cleanup_failed firmware_id=%s path=%s",
                    firmware_id,
                    artifact_path,
                )

        logger.info(
            "firmware_hard_deleted entity_id=%s firmware_key=%s version=%s actor_sub=%s",
            firmware_id,
            impact.get("firmwareKey"),
            impact.get("version"),
            actor_sub,
        )
        return {
            "deleted": True,
            "id": str(firmware_id),
            "firmwareKey": impact.get("firmwareKey"),
            "version": impact.get("version"),
            "dependencies": impact["dependencies"],
        }

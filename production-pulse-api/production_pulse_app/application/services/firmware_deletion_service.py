from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from production_pulse_app.domain.errors import ContentCodedError
from production_pulse_app.application.services.production_pulse_realtime_notify import (
    notify_firmware_catalog_updated,
    safe_realtime,
)
from production_pulse_app.infrastructure.persistence.repositories.postgres_firmware_repository import (
    FirmwareFamilyActiveTargetsError,
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
        safe_realtime(
            notify_firmware_catalog_updated,
            reason="delete",
            firmware_id=firmware_id,
            firmware_key=impact.get("firmwareKey"),
            actor_user_id=actor_sub,
        )
        return {
            "deleted": True,
            "id": str(firmware_id),
            "firmwareKey": impact.get("firmwareKey"),
            "version": impact.get("version"),
            "dependencies": impact["dependencies"],
        }

    def get_family_deletion_impact(self, firmware_key: str) -> dict[str, Any]:
        key = (firmware_key or "").strip()
        if not key:
            raise FirmwareNotFoundError(firmware_key or "")
        deps = self._repo.count_family_deletion_dependencies(key)
        blockers: list[dict[str, Any]] = []
        if deps["activeTargets"] > 0:
            blockers.append(
                {"code": "firmwareHasActiveTargets", "count": deps["activeTargets"]}
            )
        will_purge = deps["jobsFinished"] > 0
        return {
            "canDelete": len(blockers) == 0,
            "blockers": blockers,
            "versionCount": deps["versionCount"],
            "jobsFinished": deps["jobsFinished"],
            "jobsActive": deps["jobsActive"],
            "activeTargets": deps["activeTargets"],
            "linkedDevices": deps["linkedDevices"],
            "installedDevices": deps["installedDevices"],
            "willPurgeFinishedJobs": will_purge,
            "dependencies": {
                "versionCount": deps["versionCount"],
                "jobsFinished": deps["jobsFinished"],
                "jobsActive": deps["jobsActive"],
                "activeTargets": deps["activeTargets"],
                "linkedDevices": deps["linkedDevices"],
                "installedDevices": deps["installedDevices"],
                "willPurgeFinishedJobs": will_purge,
            },
            "displayName": key,
            "firmwareKey": key,
        }

    def delete_family_permanently(
        self, firmware_key: str, *, actor_sub: str | None
    ) -> dict[str, Any]:
        impact = self.get_family_deletion_impact(firmware_key)
        if not impact["canDelete"]:
            code = impact["blockers"][0]["code"]
            logger.info(
                "hard_delete_blocked entity_type=firmware_family entity_key=%s code=%s actor_sub=%s",
                impact.get("firmwareKey"),
                code,
                actor_sub,
            )
            raise ContentCodedError(code)

        key = str(impact["firmwareKey"])
        try:
            result = self._repo.hard_delete_family(key)
        except FirmwareFamilyActiveTargetsError:
            raise ContentCodedError("deleteDependencyConflict") from None
        except FirmwareNotFoundError:
            raise

        for row in result["deletedVersions"]:
            artifact_path = row.get("artifact_path")
            if not artifact_path:
                continue
            try:
                self._storage.delete_relative(str(artifact_path))
            except Exception:
                logger.exception(
                    "firmware_artifact_cleanup_failed firmware_id=%s path=%s",
                    row.get("id"),
                    artifact_path,
                )

        deleted_ids = [str(row["id"]) for row in result["deletedVersions"]]
        logger.info(
            "firmware_family_hard_deleted firmware_key=%s versions=%s purged_jobs=%s "
            "unlinked_devices=%s actor_sub=%s",
            key,
            len(deleted_ids),
            result["purgedJobs"],
            result["unlinkedDevices"],
            actor_sub,
        )
        safe_realtime(
            notify_firmware_catalog_updated,
            reason="family_delete",
            firmware_key=key,
            actor_user_id=actor_sub,
        )
        return {
            "deleted": True,
            "firmwareKey": key,
            "deletedVersionIds": deleted_ids,
            "versionCount": len(deleted_ids),
            "purgedJobs": result["purgedJobs"],
            "unlinkedDevices": result["unlinkedDevices"],
            "willPurgeFinishedJobs": impact["willPurgeFinishedJobs"],
            "dependencies": impact["dependencies"],
        }

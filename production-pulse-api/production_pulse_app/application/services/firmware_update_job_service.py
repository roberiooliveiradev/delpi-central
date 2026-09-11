from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from production_pulse_app.config import settings
from production_pulse_app.domain.errors import ContentCodedError
from production_pulse_app.domain.services.device_validation_service import validate_branch
from production_pulse_app.infrastructure.persistence.repositories.postgres_device_repository import (
    PostgresDeviceRepository,
)
from production_pulse_app.application.services.device_ota_wake_service import DeviceOtaWakeService
from production_pulse_app.infrastructure.persistence.repositories.postgres_firmware_repository import (
    FirmwareJobConflictError,
    FirmwareJobNotFoundError,
    FirmwareNotFoundError,
    PostgresFirmwareRepository,
    PostgresFirmwareUpdateJobRepository,
)

logger = logging.getLogger(__name__)

_OPEN_TARGET_STATUSES = ("pending", "authorized", "downloading", "applying")


class FirmwareUpdateJobService:
    def __init__(
        self,
        job_repository: PostgresFirmwareUpdateJobRepository | None = None,
        firmware_repository: PostgresFirmwareRepository | None = None,
        device_repository: PostgresDeviceRepository | None = None,
        wake_service: DeviceOtaWakeService | None = None,
    ) -> None:
        self._jobs = job_repository or PostgresFirmwareUpdateJobRepository()
        self._firmwares = firmware_repository or PostgresFirmwareRepository()
        self._devices = device_repository or PostgresDeviceRepository()
        self._wake = wake_service or DeviceOtaWakeService(
            job_repository=self._jobs,
            device_repository=self._devices,
        )

    def list_jobs(self, *, branch: str | None = None) -> list[dict[str, Any]]:
        if branch:
            validate_branch(branch)
        return [self._job_to_api(row) for row in self._jobs.list_jobs(branch=branch)]

    def get_job(self, job_id: UUID) -> dict[str, Any]:
        row = self._jobs.get_job(job_id)
        if row is None:
            raise FirmwareJobNotFoundError(str(job_id))
        return self._job_to_api(row)

    def list_targets(self, job_id: UUID) -> list[dict[str, Any]]:
        if self._jobs.get_job(job_id) is None:
            raise FirmwareJobNotFoundError(str(job_id))
        return [self._target_to_api(row) for row in self._jobs.list_targets(job_id)]

    def get_device_firmware_update_status(self, device_id: UUID) -> dict[str, Any]:
        row = self._jobs.find_status_target_for_device(device_id)
        if row is None:
            return {"active": False, "target": None}
        status = str(row.get("status") or "")
        active = status in {"pending", "authorized", "downloading", "applying"}
        return {
            "active": active,
            "target": self._target_to_api(row),
            "jobId": str(row["job_id"]),
            "targetId": str(row["id"]),
            "status": status,
            "fromVersion": row.get("from_version"),
            "toVersion": row.get("to_version"),
            "errorCode": row.get("error_code"),
            "firmwareKey": row.get("firmware_key"),
            "bytesReceived": row.get("bytes_received"),
            "bytesTotal": row.get("bytes_total"),
            "progressPercent": row.get("progress_percent"),
            "jobStatus": row.get("job_status"),
            "updatedAt": row.get("updated_at"),
        }

    def create_job(self, payload: dict[str, Any], *, actor_sub: str | None) -> dict[str, Any]:
        firmware_id = UUID(str(payload.get("firmware_id") or payload.get("firmwareId")))
        firmware = self._firmwares.get_by_id(firmware_id)
        if firmware is None or firmware.get("published_at") is None:
            raise FirmwareNotFoundError(str(firmware_id))
        if firmware.get("archived_at") is not None:
            raise ContentCodedError("firmwareArchived")

        branch = validate_branch(payload.get("branch", ""))
        trigger = str(payload.get("trigger") or "manual").strip().lower()
        if trigger not in {"manual", "scheduled"}:
            raise ContentCodedError("validation_error")

        scheduled_at = payload.get("scheduled_at") or payload.get("scheduledAt")
        if trigger == "scheduled":
            if not scheduled_at:
                raise ContentCodedError("validation_error")
            if isinstance(scheduled_at, str):
                scheduled_at = datetime.fromisoformat(scheduled_at.replace("Z", "+00:00"))
            status = "scheduled"
            authorize_now = False
        else:
            scheduled_at = None
            status = "running"
            authorize_now = True

        filter_payload = payload.get("filter") if isinstance(payload.get("filter"), dict) else {}
        device_ids_raw = filter_payload.get("deviceIds") or payload.get("deviceIds") or []
        only_outdated = bool(
            filter_payload.get("onlyOutdated", payload.get("onlyOutdated", True))
        )
        firmware_key = (
            filter_payload.get("firmwareKey")
            or payload.get("firmwareKey")
            or firmware["firmware_key"]
        )

        devices = self._devices.list_devices(branch=branch)
        eligible: list[dict[str, Any]] = []
        selected_ids = {str(item) for item in device_ids_raw} if device_ids_raw else None
        for device in devices:
            if selected_ids is not None and str(device["id"]) not in selected_ids:
                continue
            device_family = device.get("firmware_key") or device.get("driver_key")
            if device_family not in {firmware_key, firmware["driver_key"]}:
                continue
            if device.get("driver_key") != firmware["driver_key"]:
                continue
            installed = device.get("installed_firmware_version")
            if only_outdated and installed and str(installed) == str(firmware["version"]):
                continue
            eligible.append(
                {
                    "device_id": device["id"],
                    "from_version": installed,
                    "to_version": firmware["version"],
                }
            )

        if not eligible:
            raise ContentCodedError("noEligibleDevices")

        try:
            job = self._jobs.create_job_with_targets(
                firmware_id=firmware_id,
                branch=branch,
                trigger=trigger,
                scheduled_at=scheduled_at,
                status=status,
                filter_payload={
                    "firmwareKey": firmware_key,
                    "onlyOutdated": only_outdated,
                    "deviceIds": [str(item["device_id"]) for item in eligible]
                    if selected_ids
                    else None,
                },
                targets=eligible,
                actor_sub=actor_sub,
                authorize_now=authorize_now,
            )
        except FirmwareJobConflictError as exc:
            raise ContentCodedError("openTargetExists") from exc

        if authorize_now:
            for device in eligible:
                self._devices.patch(
                    device["device_id"],
                    updates={"target_firmware_version": firmware["version"]},
                    actor_sub=actor_sub,
                )
            # Wake only after commit (create_job_with_targets already committed).
            authorized_targets = self._jobs.list_targets(job["id"])
            self._wake.wake_authorized_targets(authorized_targets)
        api = self._job_to_api(job)
        logger.info(
            "ota_job_created job_id=%s status=%s branch=%s targets=%s",
            api.get("id"),
            api.get("status"),
            api.get("branch"),
            len(eligible),
        )
        return api

    def cancel_job(self, job_id: UUID) -> dict[str, Any]:
        existing = self._jobs.get_job(job_id)
        if existing is None:
            raise FirmwareJobNotFoundError(str(job_id))
        if existing["status"] == "cancelled":
            return self._job_to_api(existing)
        try:
            job = self._jobs.cancel_job(job_id)
        except FirmwareJobNotFoundError:
            raise
        except FirmwareJobConflictError as exc:
            raise ContentCodedError("jobCannotCancel") from exc
        api = self._job_to_api(job)
        logger.info("ota_job_cancelled job_id=%s", api.get("id"))
        return api

    def authorize_due_scheduled(self) -> int:
        job_count, targets = self._jobs.authorize_due_scheduled_jobs()
        if targets:
            self._wake.wake_authorized_targets(targets)
        return job_count

    def reconcile_device_installed_version(self, device_id: UUID, version: str) -> bool:
        """Close open target when device already reports the target to_version."""
        installed = str(version or "").strip()
        if not installed:
            return False
        target = self._jobs.find_open_target_for_device(device_id)
        if target is None:
            return False
        if str(target.get("to_version") or "") != installed:
            return False
        updated = self._jobs.transition_target(
            target["id"],
            next_status="updated",
            allowed_statuses=_OPEN_TARGET_STATUSES,
            clear_artifact_token=True,
            touch_finished=True,
            progress_percent=100,
        )
        if updated is None:
            return False
        finished = self._jobs.maybe_finish_job(target["job_id"])
        logger.info(
            "ota_target_reconciled target_id=%s job_id=%s device_id=%s version=%s job_status=%s",
            updated["id"],
            target["job_id"],
            device_id,
            installed,
            (finished or {}).get("status"),
        )
        return True

    def fail_stale_open_targets(self, stale_seconds: int | None = None) -> int:
        seconds = stale_seconds if stale_seconds is not None else settings.PP_OTA_TARGET_STALE_SECONDS
        seconds = max(1, int(seconds))
        stale_before = datetime.now(timezone.utc) - timedelta(seconds=seconds)
        stale_targets = self._jobs.list_stale_open_targets(stale_before)
        failed_count = 0
        for target in stale_targets:
            updated = self._jobs.transition_target(
                target["id"],
                next_status="failed",
                allowed_statuses=_OPEN_TARGET_STATUSES,
                error_code="ota_target_stale",
                clear_artifact_token=True,
                touch_finished=True,
            )
            if updated is None:
                continue
            finished = self._jobs.maybe_finish_job(target["job_id"])
            failed_count += 1
            logger.info(
                "ota_target_stale target_id=%s job_id=%s device_id=%s job_status=%s",
                updated["id"],
                target["job_id"],
                target["device_id"],
                (finished or {}).get("status"),
            )
        return failed_count

    def reconcile_matching_installed_versions(self) -> int:
        targets = self._jobs.list_open_targets_for_reconcile()
        reconciled = 0
        for target in targets:
            version = str(target.get("to_version") or "").strip()
            if not version:
                continue
            if self.reconcile_device_installed_version(target["device_id"], version):
                reconciled += 1
        return reconciled

    def summary(self, *, branch: str, firmware_key: str | None = None) -> dict[str, Any]:
        validate_branch(branch)
        counts = self._jobs.summary_counts(branch=branch, firmware_key=firmware_key)
        return {
            "branch": branch,
            "firmwareKey": firmware_key,
            "total": counts["total"],
            "updated": counts["updated"],
            "updating": counts["updating"],
            "failed": counts["failed"],
        }

    @staticmethod
    def _job_to_api(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": str(row["id"]),
            "firmwareId": str(row["firmware_id"]),
            "branch": row["branch"],
            "trigger": row["trigger"],
            "scheduledAt": row.get("scheduled_at"),
            "status": row["status"],
            "filter": row.get("filter") or {},
            "createdBy": row.get("created_by"),
            "createdAt": row.get("created_at"),
            "updatedAt": row.get("updated_at"),
        }

    @staticmethod
    def _target_to_api(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": str(row["id"]),
            "jobId": str(row["job_id"]),
            "deviceId": str(row["device_id"]),
            "status": row["status"],
            "fromVersion": row.get("from_version"),
            "toVersion": row.get("to_version"),
            "errorCode": row.get("error_code"),
            "bytesReceived": row.get("bytes_received"),
            "bytesTotal": row.get("bytes_total"),
            "progressPercent": row.get("progress_percent"),
            "authorizedAt": row.get("authorized_at"),
            "startedAt": row.get("started_at"),
            "finishedAt": row.get("finished_at"),
            "createdAt": row.get("created_at"),
            "updatedAt": row.get("updated_at"),
            "wakeStatus": row.get("wake_status"),
            "wakeAttemptedAt": row.get("wake_attempted_at"),
            "wakeAcknowledgedAt": row.get("wake_acknowledged_at"),
            "wakeErrorCode": row.get("wake_error_code"),
        }

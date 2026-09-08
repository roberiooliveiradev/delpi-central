from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from production_pulse_app.domain.errors import ContentCodedError
from production_pulse_app.domain.services.device_validation_service import validate_branch
from production_pulse_app.infrastructure.persistence.repositories.postgres_device_repository import (
    PostgresDeviceRepository,
)
from production_pulse_app.infrastructure.persistence.repositories.postgres_firmware_repository import (
    FirmwareJobConflictError,
    FirmwareJobNotFoundError,
    FirmwareNotFoundError,
    PostgresFirmwareRepository,
    PostgresFirmwareUpdateJobRepository,
)


class FirmwareUpdateJobService:
    def __init__(
        self,
        job_repository: PostgresFirmwareUpdateJobRepository | None = None,
        firmware_repository: PostgresFirmwareRepository | None = None,
        device_repository: PostgresDeviceRepository | None = None,
    ) -> None:
        self._jobs = job_repository or PostgresFirmwareUpdateJobRepository()
        self._firmwares = firmware_repository or PostgresFirmwareRepository()
        self._devices = device_repository or PostgresDeviceRepository()

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

    def create_job(self, payload: dict[str, Any], *, actor_sub: str | None) -> dict[str, Any]:
        firmware_id = UUID(str(payload.get("firmware_id") or payload.get("firmwareId")))
        firmware = self._firmwares.get_by_id(firmware_id)
        if firmware is None or firmware.get("published_at") is None:
            raise FirmwareNotFoundError(str(firmware_id))

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
        return self._job_to_api(job)

    def cancel_job(self, job_id: UUID) -> dict[str, Any]:
        try:
            job = self._jobs.cancel_job(job_id)
        except FirmwareJobNotFoundError:
            raise
        except FirmwareJobConflictError as exc:
            raise ContentCodedError("jobCannotCancel") from exc
        return self._job_to_api(job)

    def authorize_due_scheduled(self) -> int:
        return self._jobs.authorize_due_scheduled_jobs()

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
            "authorizedAt": row.get("authorized_at"),
            "startedAt": row.get("started_at"),
            "finishedAt": row.get("finished_at"),
            "createdAt": row.get("created_at"),
            "updatedAt": row.get("updated_at"),
        }

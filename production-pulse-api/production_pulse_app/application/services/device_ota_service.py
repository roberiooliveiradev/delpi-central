from __future__ import annotations

import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from production_pulse_app.config import settings
from production_pulse_app.domain.errors import ContentCodedError
from production_pulse_app.infrastructure.persistence.repositories.postgres_device_repository import (
    PostgresDeviceRepository,
)
from production_pulse_app.infrastructure.persistence.repositories.postgres_firmware_repository import (
    PostgresFirmwareUpdateJobRepository,
)
from production_pulse_app.infrastructure.storage.firmware_artifact_storage import (
    FirmwareArtifactStorage,
    FirmwareArtifactStorageError,
)

logger = logging.getLogger(__name__)

_OPEN = ("authorized", "downloading", "applying")
_TERMINAL = ("updated", "failed", "cancelled", "skipped")


class DeviceOtaAuthError(Exception):
    pass


class DeviceOtaService:
    def __init__(
        self,
        device_repository: PostgresDeviceRepository | None = None,
        job_repository: PostgresFirmwareUpdateJobRepository | None = None,
        storage: FirmwareArtifactStorage | None = None,
    ) -> None:
        self._devices = device_repository or PostgresDeviceRepository()
        self._jobs = job_repository or PostgresFirmwareUpdateJobRepository()
        self._storage = storage or FirmwareArtifactStorage()

    def authenticate_device(
        self,
        *,
        token: str | None,
        device_id: str | None = None,
        controller_code: str | None = None,
        branch: str | None = None,
    ) -> dict[str, Any]:
        raw_token = (token or "").strip()
        if not raw_token:
            raise DeviceOtaAuthError("deviceOtaUnauthorized")

        device: dict[str, Any] | None = None
        if device_id:
            try:
                device = self._devices.get_by_id(UUID(str(device_id)))
            except ValueError as exc:
                raise DeviceOtaAuthError("deviceOtaUnauthorized") from exc
        elif controller_code and branch:
            device = self._devices.get_by_controller_code(
                branch=branch.strip(),
                controller_code=controller_code.strip(),
            )
        if device is None:
            raise DeviceOtaAuthError("deviceOtaUnauthorized")

        expected = str(device.get("device_api_token") or "").strip()
        if not expected or expected != raw_token:
            raise DeviceOtaAuthError("deviceOtaUnauthorized")
        return device

    def check(self, device: dict[str, Any]) -> dict[str, Any]:
        target = self._jobs.find_authorized_target_for_device(device["id"])
        if target is None:
            return {
                "updateAvailable": False,
                "deviceId": str(device["id"]),
                "installedFirmwareVersion": device.get("installed_firmware_version"),
            }

        token = secrets.token_urlsafe(24)
        expires = datetime.now(timezone.utc) + timedelta(
            seconds=max(60, settings.PP_FIRMWARE_ARTIFACT_TOKEN_TTL_SECONDS)
        )
        self._jobs.update_target(
            target["id"],
            artifact_token=token,
            artifact_token_expires_at=expires,
        )
        return {
            "updateAvailable": True,
            "deviceId": str(device["id"]),
            "targetId": str(target["id"]),
            "jobId": str(target["job_id"]),
            "firmwareKey": target.get("firmware_key"),
            "version": target.get("firmware_version") or target.get("to_version"),
            "artifactSha256": target.get("artifact_sha256"),
            "artifactSizeBytes": int(target.get("artifact_size_bytes") or 0),
            "artifactToken": token,
            "artifactTokenExpiresAt": expires,
            "installedFirmwareVersion": device.get("installed_firmware_version"),
        }

    def open_artifact(self, *, artifact_token: str, device: dict[str, Any]):
        target = self._jobs.get_target_by_artifact_token(artifact_token)
        if target is None or str(target["device_id"]) != str(device["id"]):
            raise ContentCodedError("deviceOtaNotAuthorized")
        expires = target.get("artifact_token_expires_at")
        if expires is not None:
            exp = expires if expires.tzinfo else expires.replace(tzinfo=timezone.utc)
            if exp < datetime.now(timezone.utc):
                raise ContentCodedError("deviceOtaArtifactExpired")
        if target["status"] not in _OPEN:
            raise ContentCodedError("deviceOtaNotAuthorized")

        transitioned = self._jobs.transition_target(
            target["id"],
            next_status="downloading",
            allowed_statuses=_OPEN,
            touch_started=True,
        )
        if transitioned is None:
            raise ContentCodedError("deviceOtaNotAuthorized")
        try:
            path = self._storage.open_path(target["artifact_path"])
        except FirmwareArtifactStorageError as exc:
            raise ContentCodedError("firmwareArtifactInvalid") from exc
        return path, transitioned

    def report(
        self,
        device: dict[str, Any],
        *,
        target_id: str | None,
        status: str,
        error_code: str | None = None,
        installed_version: str | None = None,
        bytes_received: int | None = None,
        bytes_total: int | None = None,
        progress_percent: int | None = None,
    ) -> dict[str, Any]:
        normalized = (status or "").strip().lower()
        if normalized not in {"updated", "failed", "downloading", "applying"}:
            raise ContentCodedError("validation_error")

        target: dict[str, Any] | None = None
        if target_id:
            try:
                tid = UUID(str(target_id))
            except ValueError as exc:
                raise ContentCodedError("jobNotFound") from exc
            target = self._jobs.get_target_by_id_for_device(tid, device["id"])
        else:
            target = self._jobs.find_authorized_target_for_device(device["id"])

        if target is None:
            raise ContentCodedError("deviceOtaNotAuthorized")

        current = str(target.get("status") or "")
        if current in _TERMINAL:
            # Idempotent terminal: same status = no-op; otherwise reject resurrection.
            if current == normalized or (
                normalized == "updated" and current == "updated"
            ) or (normalized == "failed" and current == "failed"):
                return {
                    "targetId": str(target["id"]),
                    "status": current,
                    "bytesReceived": target.get("bytes_received"),
                    "bytesTotal": target.get("bytes_total"),
                    "progressPercent": target.get("progress_percent"),
                    "errorCode": target.get("error_code"),
                    "installedFirmwareVersion": installed_version
                    if current == "updated"
                    else None,
                }
            logger.info(
                "ota_late_report_rejected target_id=%s current=%s attempted=%s",
                target["id"],
                current,
                normalized,
            )
            raise ContentCodedError("deviceOtaInvalidTransition")

        if normalized == "downloading":
            pct = progress_percent
            if pct is None and bytes_received is not None and bytes_total and bytes_total > 0:
                pct = int(round(100.0 * float(bytes_received) / float(bytes_total)))
            updated = self._jobs.transition_target(
                target["id"],
                next_status="downloading",
                allowed_statuses=_OPEN,
                touch_started=True,
                bytes_received=bytes_received,
                bytes_total=bytes_total,
                progress_percent=pct,
            )
            if updated is None:
                raise ContentCodedError("deviceOtaInvalidTransition")
            return {
                "targetId": str(updated["id"]),
                "status": updated["status"],
                "bytesReceived": updated.get("bytes_received"),
                "bytesTotal": updated.get("bytes_total"),
                "progressPercent": updated.get("progress_percent"),
            }

        if normalized == "applying":
            updated = self._jobs.transition_target(
                target["id"],
                next_status="applying",
                allowed_statuses=_OPEN,
                touch_started=True,
                progress_percent=100,
                bytes_received=bytes_received
                if bytes_received is not None
                else target.get("bytes_total"),
                bytes_total=bytes_total if bytes_total is not None else target.get("bytes_total"),
            )
            if updated is None:
                raise ContentCodedError("deviceOtaInvalidTransition")
            return {
                "targetId": str(updated["id"]),
                "status": updated["status"],
                "bytesReceived": updated.get("bytes_received"),
                "bytesTotal": updated.get("bytes_total"),
                "progressPercent": updated.get("progress_percent"),
            }

        if normalized == "updated":
            version = installed_version or target.get("to_version")
            updated = self._jobs.transition_target(
                target["id"],
                next_status="updated",
                allowed_statuses=_OPEN,
                clear_artifact_token=True,
                touch_finished=True,
                progress_percent=100,
            )
            if updated is None:
                logger.info(
                    "ota_invalid_transition target_id=%s attempted=updated",
                    target["id"],
                )
                raise ContentCodedError("deviceOtaInvalidTransition")
            self._devices.record_installed_firmware_version(
                device["id"],
                version=str(version),
            )
            finished = self._jobs.maybe_finish_job(target["job_id"])
            logger.info(
                "ota_target_updated target_id=%s job_id=%s job_status=%s",
                updated["id"],
                target["job_id"],
                (finished or {}).get("status"),
            )
            return {
                "targetId": str(updated["id"]),
                "status": "updated",
                "installedFirmwareVersion": version,
                "progressPercent": 100,
            }

        updated = self._jobs.transition_target(
            target["id"],
            next_status="failed",
            allowed_statuses=_OPEN,
            error_code=(error_code or "ota_failed"),
            clear_artifact_token=True,
            touch_finished=True,
        )
        if updated is None:
            logger.info(
                "ota_invalid_transition target_id=%s attempted=failed",
                target["id"],
            )
            raise ContentCodedError("deviceOtaInvalidTransition")
        finished = self._jobs.maybe_finish_job(target["job_id"])
        logger.info(
            "ota_target_failed target_id=%s job_id=%s job_status=%s error_code=%s",
            updated["id"],
            target["job_id"],
            (finished or {}).get("status"),
            updated.get("error_code"),
        )
        return {
            "targetId": str(updated["id"]),
            "status": "failed",
            "errorCode": updated.get("error_code"),
            "bytesReceived": updated.get("bytes_received"),
            "bytesTotal": updated.get("bytes_total"),
            "progressPercent": updated.get("progress_percent"),
        }

from __future__ import annotations

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
        if target["status"] not in {"authorized", "downloading", "applying"}:
            raise ContentCodedError("deviceOtaNotAuthorized")

        self._jobs.update_target(
            target["id"],
            status="downloading",
            touch_started=True,
        )
        try:
            path = self._storage.open_path(target["artifact_path"])
        except FirmwareArtifactStorageError as exc:
            raise ContentCodedError("firmwareArtifactInvalid") from exc
        return path, target

    def report(
        self,
        device: dict[str, Any],
        *,
        target_id: str | None,
        status: str,
        error_code: str | None = None,
        installed_version: str | None = None,
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

        if normalized in {"downloading", "applying"}:
            updated = self._jobs.update_target(
                target["id"],
                status=normalized,
                touch_started=True,
            )
            return {"targetId": str(updated["id"]), "status": updated["status"]}

        if normalized == "updated":
            version = installed_version or target.get("to_version")
            updated = self._jobs.update_target(
                target["id"],
                status="updated",
                clear_artifact_token=True,
                touch_finished=True,
            )
            self._devices.record_installed_firmware_version(
                device["id"],
                version=str(version),
            )
            return {
                "targetId": str(updated["id"]),
                "status": "updated",
                "installedFirmwareVersion": version,
            }

        updated = self._jobs.update_target(
            target["id"],
            status="failed",
            error_code=(error_code or "ota_failed"),
            clear_artifact_token=True,
            touch_finished=True,
        )
        return {
            "targetId": str(updated["id"]),
            "status": "failed",
            "errorCode": updated.get("error_code"),
        }

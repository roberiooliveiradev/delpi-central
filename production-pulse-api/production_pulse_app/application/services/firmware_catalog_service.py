from __future__ import annotations

import re
from typing import Any

from production_pulse_app.domain.errors import ContentCodedError, DeviceValidationError
from production_pulse_app.domain.services.device_validation_service import resolve_driver
from production_pulse_app.infrastructure.content.firmware_ota_messages_content_service import (
    firmware_ota_http_message,
)
from production_pulse_app.infrastructure.persistence.repositories.postgres_firmware_repository import (
    FirmwareConflictError,
    FirmwareNotFoundError,
    PostgresFirmwareRepository,
)
from production_pulse_app.infrastructure.storage.firmware_artifact_storage import (
    FirmwareArtifactStorage,
    FirmwareArtifactStorageError,
)

_FIRMWARE_KEY_RE = re.compile(r"^[a-z][a-z0-9_]{1,63}$")
_VERSION_RE = re.compile(r"^[0-9]+(\.[0-9]+){0,3}([-+][A-Za-z0-9.-]+)?$")


class FirmwareCatalogService:
    def __init__(
        self,
        repository: PostgresFirmwareRepository | None = None,
        storage: FirmwareArtifactStorage | None = None,
    ) -> None:
        self._repo = repository or PostgresFirmwareRepository()
        self._storage = storage or FirmwareArtifactStorage()

    def list_firmwares(
        self,
        *,
        firmware_key: str | None = None,
        driver_key: str | None = None,
    ) -> list[dict[str, Any]]:
        rows = self._repo.list_firmwares(
            firmware_key=firmware_key,
            driver_key=driver_key,
            published_only=False,
        )
        return [self._to_api(row) for row in rows]

    def get_firmware(self, firmware_id) -> dict[str, Any]:
        row = self._repo.get_by_id(firmware_id)
        if row is None:
            raise FirmwareNotFoundError(str(firmware_id))
        return self._to_api(row)

    def publish(
        self,
        *,
        firmware_key: str,
        driver_key: str,
        version: str,
        display_name: str,
        raw: bytes,
        filename_hint: str | None = None,
        release_notes: str | None = None,
        min_compatible_version: str | None = None,
        publish: bool = True,
        actor_sub: str | None = None,
    ) -> dict[str, Any]:
        key = (firmware_key or "").strip()
        if not _FIRMWARE_KEY_RE.fullmatch(key):
            raise ContentCodedError("invalidFirmwareKey")
        ver = (version or "").strip()
        if not _VERSION_RE.fullmatch(ver):
            raise ContentCodedError("invalidFirmwareVersion")
        try:
            driver = resolve_driver(driver_key)
        except DeviceValidationError as exc:
            raise ContentCodedError("driverKeyUnknown") from exc

        name = (display_name or "").strip() or key
        try:
            saved = self._storage.save(
                firmware_key=key,
                version=ver,
                raw=raw,
                filename_hint=filename_hint,
            )
        except FirmwareArtifactStorageError as exc:
            code = str(exc)
            if code == "artifact_too_large":
                raise ContentCodedError("firmwareArtifactTooLarge") from exc
            raise ContentCodedError("firmwareArtifactInvalid") from exc

        try:
            row = self._repo.create(
                firmware_key=key,
                driver_key=driver.driver_key,
                version=ver,
                display_name=name,
                artifact_path=saved.relative_path,
                artifact_sha256=saved.sha256,
                artifact_size_bytes=saved.size_bytes,
                release_notes=(release_notes or None),
                min_compatible_version=(min_compatible_version or None),
                publish=publish,
                actor_sub=actor_sub,
            )
        except FirmwareConflictError as exc:
            raise ContentCodedError("firmwareDuplicateVersion") from exc
        return self._to_api(row)

    @staticmethod
    def _to_api(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": str(row["id"]),
            "firmwareKey": row["firmware_key"],
            "driverKey": row["driver_key"],
            "version": row["version"],
            "displayName": row["display_name"],
            "artifactSha256": row["artifact_sha256"],
            "artifactSizeBytes": int(row["artifact_size_bytes"]),
            "releaseNotes": row.get("release_notes"),
            "minCompatibleVersion": row.get("min_compatible_version"),
            "publishedAt": row.get("published_at"),
            "createdBy": row.get("created_by"),
            "createdAt": row.get("created_at"),
        }


def message_for_firmware_error(code: str) -> str:
    return firmware_ota_http_message(code, default=code)

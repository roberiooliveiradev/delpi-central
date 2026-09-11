from __future__ import annotations

import logging
import re
from typing import Any
from uuid import UUID

from production_pulse_app.domain.errors import ContentCodedError, DeviceValidationError
from production_pulse_app.application.services.production_pulse_realtime_notify import (
    notify_firmware_catalog_updated,
    safe_realtime,
)
from production_pulse_app.domain.services.device_validation_service import resolve_driver
from production_pulse_app.domain.services.firmware_version_lifecycle import (
    can_edit_metadata,
    can_edit_source,
    firmware_lifecycle_state,
    has_artifact,
    has_source,
    validate_source_text,
)
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

logger = logging.getLogger(__name__)

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
        include_archived: bool = True,
        published_only: bool = False,
    ) -> list[dict[str, Any]]:
        rows = self._repo.list_firmwares(
            firmware_key=firmware_key,
            driver_key=driver_key,
            published_only=published_only,
            include_archived=include_archived,
        )
        return [self._to_list_item(row) for row in rows]

    def get_firmware(self, firmware_id) -> dict[str, Any]:
        row = self._repo.get_by_id(firmware_id)
        if row is None:
            raise FirmwareNotFoundError(str(firmware_id))
        return self._to_detail(row)

    def create_draft(
        self,
        *,
        firmware_key: str,
        driver_key: str,
        version: str,
        display_name: str,
        source_text: str | None = None,
        raw: bytes | None = None,
        filename_hint: str | None = None,
        release_notes: str | None = None,
        min_compatible_version: str | None = None,
        publish: bool = False,
        actor_sub: str | None = None,
    ) -> dict[str, Any]:
        key, ver, name, driver = self._validate_create_fields(
            firmware_key, driver_key, version, display_name
        )
        normalized_source = None
        if source_text is not None:
            try:
                normalized_source = validate_source_text(source_text)
            except ValueError as exc:
                raise ContentCodedError(str(exc)) from exc

        artifact_path: str | None = None
        artifact_sha256: str | None = None
        artifact_size: int | None = None
        saved_path: str | None = None

        if raw:
            saved = self._save_artifact(key, ver, raw, filename_hint)
            saved_path = saved.relative_path
            artifact_path = saved.relative_path
            artifact_sha256 = saved.sha256
            artifact_size = saved.size_bytes

        if publish and not artifact_path:
            raise ContentCodedError("firmwareMissingArtifact")

        try:
            row = self._repo.create(
                firmware_key=key,
                driver_key=driver.driver_key,
                version=ver,
                display_name=name,
                source_text=normalized_source,
                artifact_path=artifact_path,
                artifact_sha256=artifact_sha256,
                artifact_size_bytes=artifact_size,
                release_notes=(release_notes or None),
                min_compatible_version=(min_compatible_version or None),
                publish=publish,
                actor_sub=actor_sub,
            )
        except FirmwareConflictError as exc:
            if saved_path:
                self._storage.delete_relative(saved_path)
            raise ContentCodedError("firmwareDuplicateVersion") from exc

        api = self._to_detail(row)
        logger.info(
            "firmware_draft_created firmware_id=%s firmware_key=%s version=%s published=%s",
            api.get("id"),
            api.get("firmwareKey"),
            api.get("version"),
            publish,
        )
        safe_realtime(
            notify_firmware_catalog_updated,
            reason="create" if not publish else "publish",
            firmware_id=api.get("id"),
            firmware_key=api.get("firmwareKey"),
            actor_user_id=actor_sub,
        )
        return api

    def update_metadata(
        self,
        firmware_id: UUID,
        *,
        display_name: str | None = None,
        release_notes: str | None = None,
        source_text: str | None = None,
        source_text_provided: bool = False,
    ) -> dict[str, Any]:
        row = self._repo.get_by_id(firmware_id)
        if row is None:
            raise FirmwareNotFoundError(str(firmware_id))
        if not can_edit_metadata(row):
            raise ContentCodedError("firmwareNotEditable")

        if source_text_provided:
            if not can_edit_source(row):
                raise ContentCodedError("firmwareNotEditable")
            try:
                normalized = validate_source_text(source_text)
            except ValueError as exc:
                raise ContentCodedError(str(exc)) from exc
            row = self._repo.update_source(firmware_id, source_text=normalized)
            logger.info("firmware_source_updated firmware_id=%s", firmware_id)

        if display_name is not None or release_notes is not None:
            if display_name is not None:
                display_name = display_name.strip()
                if not display_name:
                    raise ContentCodedError("validation_error")
            try:
                row = self._repo.update_metadata(
                    firmware_id,
                    display_name=display_name,
                    release_notes=release_notes,
                )
            except FirmwareConflictError as exc:
                raise ContentCodedError("firmwareArchived") from exc
        return self._to_detail(row)

    def attach_artifact(
        self,
        firmware_id: UUID,
        *,
        raw: bytes,
        filename_hint: str | None = None,
    ) -> dict[str, Any]:
        row = self._repo.get_by_id(firmware_id)
        if row is None:
            raise FirmwareNotFoundError(str(firmware_id))
        if firmware_lifecycle_state(row) != "draft":
            raise ContentCodedError("firmwareNotEditable")

        saved = self._save_artifact(
            row["firmware_key"],
            row["version"],
            raw,
            filename_hint,
        )
        try:
            updated = self._repo.attach_artifact(
                firmware_id,
                artifact_path=saved.relative_path,
                artifact_sha256=saved.sha256,
                artifact_size_bytes=saved.size_bytes,
            )
        except FirmwareConflictError as exc:
            self._storage.delete_relative(saved.relative_path)
            raise ContentCodedError("firmwareNotEditable") from exc
        logger.info("firmware_artifact_attached firmware_id=%s", firmware_id)
        detail = self._to_detail(updated)
        safe_realtime(
            notify_firmware_catalog_updated,
            reason="artifact",
            firmware_id=detail.get("id"),
            firmware_key=detail.get("firmwareKey"),
        )
        return detail

    def publish_version(self, firmware_id: UUID) -> dict[str, Any]:
        row = self._repo.get_by_id(firmware_id)
        if row is None:
            raise FirmwareNotFoundError(str(firmware_id))
        try:
            updated = self._repo.publish_version(firmware_id)
        except FirmwareConflictError as exc:
            code = str(exc)
            if code == "firmware_missing_artifact":
                raise ContentCodedError("firmwareMissingArtifact") from exc
            if code == "firmware_archived":
                raise ContentCodedError("firmwareArchived") from exc
            if code == "firmware_already_published":
                raise ContentCodedError("firmwareAlreadyPublished") from exc
            raise ContentCodedError("firmwareNotEditable") from exc
        api = self._to_detail(updated)
        logger.info(
            "firmware_published firmware_id=%s firmware_key=%s version=%s",
            api.get("id"),
            api.get("firmwareKey"),
            api.get("version"),
        )
        safe_realtime(
            notify_firmware_catalog_updated,
            reason="publish",
            firmware_id=api.get("id"),
            firmware_key=api.get("firmwareKey"),
        )
        return api

    def archive(self, firmware_id: UUID) -> dict[str, Any]:
        row = self._to_detail(self._repo.archive(firmware_id))
        logger.info(
            "firmware_archived firmware_id=%s firmware_key=%s version=%s",
            row.get("id"),
            row.get("firmwareKey"),
            row.get("version"),
        )
        safe_realtime(
            notify_firmware_catalog_updated,
            reason="archive",
            firmware_id=row.get("id"),
            firmware_key=row.get("firmwareKey"),
        )
        return row

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
        source_text: str | None = None,
        publish: bool = True,
        actor_sub: str | None = None,
    ) -> dict[str, Any]:
        return self.create_draft(
            firmware_key=firmware_key,
            driver_key=driver_key,
            version=version,
            display_name=display_name,
            source_text=source_text,
            raw=raw,
            filename_hint=filename_hint,
            release_notes=release_notes,
            min_compatible_version=min_compatible_version,
            publish=publish,
            actor_sub=actor_sub,
        )

    def _validate_create_fields(
        self,
        firmware_key: str,
        driver_key: str,
        version: str,
        display_name: str,
    ):
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
        from production_pulse_app.application.services.device_driver_registry_service import (
            get_device_driver_registry,
        )

        resolved = get_device_driver_registry().resolve_driver(driver_key)
        if resolved.definition.get("archivedAt"):
            raise ContentCodedError("driverArchived")
        name = (display_name or "").strip() or key
        return key, ver, name, driver

    def _save_artifact(
        self,
        firmware_key: str,
        version: str,
        raw: bytes,
        filename_hint: str | None,
    ):
        try:
            return self._storage.save(
                firmware_key=firmware_key,
                version=version,
                raw=raw,
                filename_hint=filename_hint,
            )
        except FirmwareArtifactStorageError as exc:
            code = str(exc)
            if code == "artifact_too_large":
                raise ContentCodedError("firmwareArtifactTooLarge") from exc
            if code == "artifact_bad_extension":
                raise ContentCodedError("firmwareArtifactInvalid") from exc
            raise ContentCodedError("firmwareArtifactInvalid") from exc

    @staticmethod
    def _lifecycle(row: dict[str, Any]) -> str:
        return firmware_lifecycle_state(row)

    @classmethod
    def _to_list_item(cls, row: dict[str, Any]) -> dict[str, Any]:
        artifact_size = row.get("artifact_size_bytes")
        return {
            "id": str(row["id"]),
            "firmwareKey": row["firmware_key"],
            "driverKey": row["driver_key"],
            "version": row["version"],
            "displayName": row["display_name"],
            "lifecycle": cls._lifecycle(row),
            "hasSource": has_source(row),
            "hasArtifact": has_artifact(row),
            "artifactSha256": row.get("artifact_sha256"),
            "artifactSizeBytes": int(artifact_size) if artifact_size is not None else None,
            "releaseNotes": row.get("release_notes"),
            "minCompatibleVersion": row.get("min_compatible_version"),
            "publishedAt": row.get("published_at"),
            "archivedAt": row.get("archived_at"),
            "createdBy": row.get("created_by"),
            "createdAt": row.get("created_at"),
        }

    @classmethod
    def _to_detail(cls, row: dict[str, Any]) -> dict[str, Any]:
        item = cls._to_list_item(row)
        item["sourceText"] = row.get("source_text")
        return item


def message_for_firmware_error(code: str) -> str:
    return firmware_ota_http_message(code, default=code)

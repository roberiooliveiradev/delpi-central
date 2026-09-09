from __future__ import annotations

from typing import Any

from production_pulse_app.infrastructure.persistence.repositories.postgres_firmware_repository import (
    PostgresFirmwareRepository,
)


class FirmwareSourceResolutionService:
    def __init__(self, repository: PostgresFirmwareRepository | None = None) -> None:
        self._repo = repository or PostgresFirmwareRepository()

    def resolve_version_source(
        self,
        *,
        firmware_key: str | None,
        version: str | None,
    ) -> dict[str, Any]:
        key = (firmware_key or "").strip()
        ver = (version or "").strip()
        if not key or not ver:
            return {
                "available": False,
                "firmwareKey": key or None,
                "version": ver or None,
                "sourceText": None,
                "reason": "missing_version",
            }
        row = self._repo.get_by_key_version(firmware_key=key, version=ver)
        if row is None:
            return {
                "available": False,
                "firmwareKey": key,
                "version": ver,
                "sourceText": None,
                "reason": "version_not_in_catalog",
            }
        source = (row.get("source_text") or "").strip()
        if not source:
            return {
                "available": False,
                "firmwareKey": key,
                "version": ver,
                "firmwareId": str(row["id"]),
                "sourceText": None,
                "reason": "no_source_on_version",
            }
        return {
            "available": True,
            "firmwareKey": key,
            "version": ver,
            "firmwareId": str(row["id"]),
            "sourceText": source,
            "reason": None,
        }

    def resolve_device_firmware_sources(
        self,
        device: dict[str, Any],
        *,
        target_version: str | None = None,
    ) -> dict[str, Any]:
        family_key = (
            (device.get("firmware_key") or device.get("firmwareKey") or "").strip()
            or (device.get("driver_key") or device.get("driverKey") or "").strip()
        )
        installed = (
            device.get("installed_firmware_version")
            or device.get("installedFirmwareVersion")
        )
        installed_ver = str(installed).strip() if installed else None
        target_ver = str(target_version).strip() if target_version else None
        legacy = (device.get("firmware_source") or device.get("firmwareSource") or "").strip()

        installed_res = self.resolve_version_source(
            firmware_key=family_key,
            version=installed_ver,
        )
        target_res = (
            self.resolve_version_source(firmware_key=family_key, version=target_ver)
            if target_ver
            else None
        )

        legacy_block: dict[str, Any] | None = None
        if legacy:
            catalog_source = installed_res.get("sourceText") if installed_res.get("available") else None
            if not catalog_source or legacy != catalog_source:
                legacy_block = {
                    "available": True,
                    "sourceText": legacy,
                    "label": "legacy_device",
                }

        return {
            "firmwareKey": family_key or None,
            "installedVersion": installed_ver,
            "targetVersion": target_ver,
            "installedSource": installed_res,
            "targetSource": target_res,
            "legacySource": legacy_block,
        }

from __future__ import annotations

import re
from typing import Any
from uuid import UUID

from production_pulse_app.domain.errors import ContentCodedError
from production_pulse_app.domain.services.device_serialization_service import device_row_to_api
from production_pulse_app.application.services.production_pulse_realtime_notify import (
    notify_device_updated,
    safe_realtime,
)
from production_pulse_app.infrastructure.persistence.repositories.postgres_device_repository import (
    DeviceNotFoundError,
    PostgresDeviceRepository,
)
from production_pulse_app.infrastructure.persistence.repositories.postgres_firmware_repository import (
    PostgresFirmwareRepository,
)

_FIRMWARE_KEY_RE = re.compile(r"^[a-z][a-z0-9_]{1,63}$")


class DeviceFirmwareLinkService:
    """Assigns at most one firmware family per device (`devices.firmware_key`)."""

    def __init__(
        self,
        device_repository: PostgresDeviceRepository | None = None,
        firmware_repository: PostgresFirmwareRepository | None = None,
    ) -> None:
        self._devices = device_repository or PostgresDeviceRepository()
        self._firmwares = firmware_repository or PostgresFirmwareRepository()

    def set_link(
        self,
        device_id: UUID,
        *,
        firmware_key: str | None,
        actor_sub: str | None = None,
    ) -> dict[str, Any]:
        device = self._devices.get_by_id(device_id)
        if device is None:
            raise DeviceNotFoundError(str(device_id))

        normalized: str | None
        if firmware_key is None or str(firmware_key).strip() == "":
            normalized = None
        else:
            normalized = str(firmware_key).strip()
            if not _FIRMWARE_KEY_RE.fullmatch(normalized):
                raise ContentCodedError("invalidFirmwareKey")
            self._assert_compatible(device, normalized)

        row = self._devices.set_firmware_key(
            device_id,
            firmware_key=normalized,
            actor_sub=actor_sub,
        )
        api = device_row_to_api(row)
        safe_realtime(
            notify_device_updated,
            reason="firmware_link",
            device_id=row["id"],
            branch=str(row.get("branch") or ""),
            actor_user_id=actor_sub,
        )
        return api

    def _assert_compatible(self, device: dict[str, Any], firmware_key: str) -> None:
        driver_key = str(device.get("driver_key") or "")
        compatible = {firmware_key}
        for row in self._firmwares.list_firmwares(firmware_key=firmware_key):
            dk = str(row.get("driver_key") or "").strip()
            if dk:
                compatible.add(dk)
        if driver_key not in compatible:
            raise ContentCodedError("firmwareLinkIncompatible")

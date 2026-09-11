from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from production_pulse_app.application.services.device_driver_registry_service import (
    DeviceDriverNotImplementedError,
    get_device_driver_registry,
)
from production_pulse_app.config import settings
from production_pulse_app.domain.errors import DeviceDriverError
from production_pulse_app.infrastructure.persistence.repositories.postgres_device_repository import (
    PostgresDeviceRepository,
)
from production_pulse_app.infrastructure.persistence.repositories.postgres_firmware_repository import (
    PostgresFirmwareUpdateJobRepository,
)

logger = logging.getLogger(__name__)


class DeviceOtaWakeService:
    """Best-effort push wake after OTA authorize / retry. Never fails the OTA target."""

    def __init__(
        self,
        *,
        job_repository: PostgresFirmwareUpdateJobRepository | None = None,
        device_repository: PostgresDeviceRepository | None = None,
        driver_registry=None,
        wake_retry_seconds: int | None = None,
    ) -> None:
        self._jobs = job_repository or PostgresFirmwareUpdateJobRepository()
        self._devices = device_repository or PostgresDeviceRepository()
        self._registry = driver_registry or get_device_driver_registry()
        self._wake_retry_seconds = max(
            1,
            int(
                wake_retry_seconds
                if wake_retry_seconds is not None
                else settings.PP_OTA_WAKE_RETRY_SECONDS
            ),
        )

    def wake_authorized_targets(self, targets: list[dict[str, Any]]) -> None:
        for target in targets:
            try:
                self.wake_target(target)
            except Exception:
                logger.exception(
                    "ota_wake_unexpected target_id=%s",
                    target.get("id"),
                )

    def retry_authorized_wakes(self) -> int:
        """Re-wake authorized targets still without download progress (Pulse-driven OTA)."""
        targets = self._jobs.list_authorized_targets_for_wake_retry(
            retry_after_seconds=self._wake_retry_seconds,
        )
        if not targets:
            return 0
        self.wake_authorized_targets(targets)
        return len(targets)

    def wake_target(self, target: dict[str, Any]) -> None:
        target_id = target.get("id")
        if target_id is None:
            return
        if str(target.get("status") or "") != "authorized":
            return
        if target.get("started_at") is not None:
            return

        claimed = self._jobs.claim_wake_attempt(
            UUID(str(target_id)),
            retry_after_seconds=self._wake_retry_seconds,
        )
        if claimed is None:
            return

        device_id = claimed.get("device_id") or target.get("device_id")
        device = self._devices.get_by_id(UUID(str(device_id))) if device_id else None
        if device is None:
            self._jobs.finalize_wake_attempt(
                UUID(str(target_id)),
                wake_status="failed",
                wake_error_code="device_not_found",
            )
            logger.warning("ota_wake_failed target_id=%s error=device_not_found", target_id)
            return

        driver_key = str(device.get("driver_key") or "")
        try:
            driver = self._registry.get_implementation(driver_key)
        except DeviceDriverNotImplementedError:
            self._jobs.finalize_wake_attempt(
                UUID(str(target_id)),
                wake_status="failed",
                wake_error_code="unsupported_driver",
            )
            logger.warning(
                "ota_wake_failed target_id=%s device_id=%s error=unsupported_driver",
                target_id,
                device_id,
            )
            return

        wake_fn = getattr(driver, "wake_ota_check", None)
        if not callable(wake_fn):
            self._jobs.finalize_wake_attempt(
                UUID(str(target_id)),
                wake_status="failed",
                wake_error_code="wake_unsupported",
            )
            logger.warning(
                "ota_wake_failed target_id=%s device_id=%s error=wake_unsupported",
                target_id,
                device_id,
            )
            return

        try:
            result = wake_fn(device)
            success = bool(getattr(result, "success", False))
            error_code = getattr(result, "error_code", None)
            if success:
                self._jobs.finalize_wake_attempt(
                    UUID(str(target_id)),
                    wake_status="accepted",
                    wake_error_code=None,
                )
                logger.info(
                    "ota_wake_accepted target_id=%s device_id=%s",
                    target_id,
                    device_id,
                )
                return
            self._jobs.finalize_wake_attempt(
                UUID(str(target_id)),
                wake_status="failed",
                wake_error_code=str(error_code or "wake_rejected"),
            )
            logger.warning(
                "ota_wake_failed target_id=%s device_id=%s error=%s",
                target_id,
                device_id,
                error_code or "wake_rejected",
            )
        except DeviceDriverError as exc:
            self._jobs.finalize_wake_attempt(
                UUID(str(target_id)),
                wake_status="failed",
                wake_error_code=str(exc.code or "network_error"),
            )
            logger.warning(
                "ota_wake_failed target_id=%s device_id=%s error=%s",
                target_id,
                device_id,
                exc.code,
            )
        except Exception:
            self._jobs.finalize_wake_attempt(
                UUID(str(target_id)),
                wake_status="failed",
                wake_error_code="wake_exception",
            )
            logger.exception(
                "ota_wake_failed target_id=%s device_id=%s error=wake_exception",
                target_id,
                device_id,
            )

"""Notificações Minha DELPI para alertas do Pulso (offline + OTA).

Destinatários: permissionCodes = production-pulse.alerts.receive (OR);
requiredPermissionCodes = view.filial-XX (AND). Superadmin sem a permissão
de alerta não entra no seletor do Core.

Best-effort: falha de dispatch nunca propaga para poll/OTA.
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from production_pulse_app.application.security.production_pulse_permissions import (
    ALERTS_RECEIVE,
    BRANCH_VIEW_PERMISSIONS,
    normalize_branch,
)

logger = logging.getLogger(__name__)

DEVICE_OFFLINE_CATEGORY = "production_pulse_device_offline"
OPERATIONAL_FAILURE_CATEGORY = "production_pulse_operational_failure"
_SOURCE_APP = "production-pulse"


class DeviceAlertNotificationService:
    def __init__(self, *, gateway: Any | None) -> None:
        self._gateway = gateway

    def notify_device_went_offline(
        self,
        *,
        device: dict[str, Any],
        previous_status: str,
        next_status: str,
        error_code: str | None = None,
    ) -> None:
        if previous_status != "online" or next_status != "offline":
            return
        if self._gateway is None:
            return
        branch = normalize_branch(str(device.get("branch") or ""))
        branch_permission = BRANCH_VIEW_PERMISSIONS.get(branch or "")
        if not branch_permission:
            logger.warning(
                "pp_alert_offline_skipped device_id=%s branch=%s reason=unknown_branch",
                device.get("id"),
                device.get("branch"),
            )
            return

        name = str(device.get("name") or "dispositivo").strip() or "dispositivo"
        ip = _format_ip(device.get("ip_address"))
        err = (error_code or "").strip()
        detail = f" Último erro: {err}." if err else ""
        payload = {
            "title": "Dispositivo IoT offline",
            "message": (
                f"O dispositivo {name} (filial {branch}, IP {ip}) "
                f"passou de online para offline.{detail}"
            ),
            "type": "warning",
            "category": DEVICE_OFFLINE_CATEGORY,
            "presentation": "text",
            "sourceApp": _SOURCE_APP,
            "permissionCodes": [ALERTS_RECEIVE],
            "requiredPermissionCodes": [branch_permission],
            "action": {
                "type": "portal_route",
                "label": "Abrir Pulso de Produção",
                "target": _device_link(device),
            },
            "metadata": {
                "event": "device_went_offline",
                "deviceId": str(device.get("id") or ""),
                "branch": branch,
                "errorCode": err or None,
            },
        }
        self._dispatch(payload, ref_id=device.get("id"))

    def notify_ota_target_failed(
        self,
        *,
        device: dict[str, Any] | None,
        target: dict[str, Any],
        branch: str | None = None,
        error_code: str | None = None,
    ) -> None:
        if self._gateway is None:
            return
        branch_code = normalize_branch(
            branch or str((device or {}).get("branch") or target.get("branch") or "")
        )
        branch_permission = BRANCH_VIEW_PERMISSIONS.get(branch_code or "")
        if not branch_permission:
            logger.warning(
                "pp_alert_ota_skipped target_id=%s branch=%s reason=unknown_branch",
                target.get("id"),
                branch_code,
            )
            return

        name = str((device or {}).get("name") or "dispositivo").strip() or "dispositivo"
        err = (error_code or target.get("error_code") or "ota_failed").strip()
        to_version = str(target.get("to_version") or "").strip()
        version_bit = f" para a versão {to_version}" if to_version else ""
        payload = {
            "title": "Falha na atualização OTA",
            "message": (
                f"A atualização OTA do dispositivo {name} "
                f"(filial {branch_code}){version_bit} falhou ({err})."
            ),
            "type": "error",
            "category": OPERATIONAL_FAILURE_CATEGORY,
            "presentation": "text",
            "sourceApp": _SOURCE_APP,
            "permissionCodes": [ALERTS_RECEIVE],
            "requiredPermissionCodes": [branch_permission],
            "action": {
                "type": "portal_route",
                "label": "Abrir Pulso de Produção",
                "target": _device_link(device) if device else "/apps/production-pulse",
            },
            "metadata": {
                "event": "ota_target_failed",
                "targetId": str(target.get("id") or ""),
                "jobId": str(target.get("job_id") or ""),
                "deviceId": str(target.get("device_id") or (device or {}).get("id") or ""),
                "branch": branch_code,
                "errorCode": err,
            },
        }
        self._dispatch(payload, ref_id=target.get("id"))

    def _dispatch(self, payload: dict[str, Any], *, ref_id: Any) -> None:
        try:
            self._gateway.dispatch(payload)
        except Exception:  # noqa: BLE001 — notificação nunca derruba o fato
            logger.warning(
                "pp_alert_notification_failed ref_id=%s category=%s",
                ref_id,
                payload.get("category"),
                exc_info=True,
            )


def _format_ip(raw: Any) -> str:
    text = str(raw or "").strip()
    if not text:
        return "?"
    return text.split("/", 1)[0]


def _device_link(device: dict[str, Any] | None) -> str:
    if not device:
        return "/apps/production-pulse"
    device_id = device.get("id")
    branch = normalize_branch(str(device.get("branch") or "")) or "01"
    if isinstance(device_id, UUID):
        device_id = str(device_id)
    if device_id:
        return f"/apps/production-pulse/devices/{device_id}?branch={branch}"
    return f"/apps/production-pulse?branch={branch}"


def build_device_alert_notification_service() -> DeviceAlertNotificationService:
    from production_pulse_app.config import settings
    from production_pulse_app.infrastructure.gateways.core_api_notification_gateway import (
        CoreApiNotificationGateway,
    )

    token = (settings.CORE_API_INTEGRATIONS_SERVICE_TOKEN or "").strip()
    base = (settings.CORE_API_BASE_URL or "").strip()
    if not token or not base:
        return DeviceAlertNotificationService(gateway=None)
    return DeviceAlertNotificationService(gateway=CoreApiNotificationGateway())


__all__ = [
    "DEVICE_OFFLINE_CATEGORY",
    "OPERATIONAL_FAILURE_CATEGORY",
    "DeviceAlertNotificationService",
    "build_device_alert_notification_service",
]

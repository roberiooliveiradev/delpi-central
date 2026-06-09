"""Notificações Minha DELPI para alertas do console API DELPI."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_CONSOLE_APP_ID = "api-delpi-console"
_ALERTAS_ROUTE = "/apps/api-delpi-console/alertas"


def portal_notifications_enabled() -> bool:
    if not settings.CONSOLE_ALERT_PORTAL_ENABLED:
        return False
    if not (settings.CORE_API_BASE_URL or "").strip():
        return False
    if not (settings.CORE_API_INTEGRATIONS_SERVICE_TOKEN or "").strip():
        return False
    return True


def _alert_notification_type(severity: str) -> str:
    if severity == "critical":
        return "error"
    if severity == "warning":
        return "warning"
    return "info"


def _build_notification_message(alert: dict[str, Any]) -> str:
    message = str(alert.get("message") or "Alerta do console API DELPI.")
    details = alert.get("details") or {}
    if alert.get("code") == "slow_sql":
        preview = details.get("preview")
        operation_id = details.get("operation_id")
        extras: list[str] = []
        if preview:
            extras.append(f"Query: {preview}")
        if operation_id:
            extras.append(f"Operation: {operation_id}")
        if extras:
            return f"{message} {' · '.join(extras)}"
    return message


def _build_dedupe_key(alert: dict[str, Any]) -> str:
    code = str(alert.get("code") or "alert")
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return f"{_CONSOLE_APP_ID}:{code}:{day}"


def send_console_alert_portal_notifications(alerts: list[dict[str, Any]]) -> bool:
    if not portal_notifications_enabled() or not alerts:
        return False

    base_url = settings.CORE_API_BASE_URL.rstrip("/")
    token = settings.CORE_API_INTEGRATIONS_SERVICE_TOKEN
    sent_any = False

    for alert in alerts:
        code = str(alert.get("code") or "alert")
        severity = str(alert.get("severity") or "warning")
        payload: dict[str, Any] = {
            "broadcast": True,
            "title": f"Console API DELPI — {code}",
            "message": _build_notification_message(alert),
            "type": _alert_notification_type(severity),
            "category": "system",
            "sourceApp": _CONSOLE_APP_ID,
            "action": {
                "type": "portal_route",
                "label": "Ver alertas",
                "target": _ALERTAS_ROUTE,
            },
            "metadata": {
                "source": _CONSOLE_APP_ID,
                "event": f"console_alert:{code}",
                "deepPath": "/alertas",
                "dedupeKey": _build_dedupe_key(alert),
                "alertCode": code,
                "alertDetails": alert.get("details") or {},
            },
        }

        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.post(
                    f"{base_url}/integrations/notifications",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
            if response.status_code in (200, 201, 202):
                sent_any = True
            else:
                logger.warning(
                    "console_alert_portal_notification_rejected status=%s code=%s",
                    response.status_code,
                    code,
                )
        except Exception:
            logger.warning(
                "console_alert_portal_notification_failed code=%s",
                code,
                exc_info=True,
            )

    return sent_any

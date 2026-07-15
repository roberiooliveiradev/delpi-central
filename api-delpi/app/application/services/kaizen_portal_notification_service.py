"""Notificações in-app do Cadastro de Kaizen via Core API."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.application.security.api_delpi_permissions import CADASTRO_KAIZEN_NOTIFY_SUGGESTIONS
from app.config import settings

logger = logging.getLogger(__name__)

_SOURCE_APP = "cadastro-kaizen"
_CATEGORY = "cadastro_kaizen"
_APP_BASE = "/apps/cadastro-kaizen"


def kaizen_portal_notifications_enabled() -> bool:
    if not settings.KAIZEN_NOTIFICATIONS_ENABLED:
        return False
    if not (settings.CORE_API_BASE_URL or "").strip():
        return False
    if not (settings.CORE_API_INTEGRATIONS_SERVICE_TOKEN or "").strip():
        return False
    return True


def _post_notification(payload: dict[str, Any]) -> bool:
    if not kaizen_portal_notifications_enabled():
        return False

    base_url = settings.CORE_API_BASE_URL.rstrip("/")
    token = settings.CORE_API_INTEGRATIONS_SERVICE_TOKEN

    try:
        with httpx.Client(timeout=8.0) as client:
            response = client.post(
                f"{base_url}/integrations/notifications",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
        if response.status_code in (200, 201, 202):
            return True
        logger.warning(
            "kaizen_portal_notification_rejected status=%s event=%s",
            response.status_code,
            (payload.get("metadata") or {}).get("event"),
        )
    except Exception:
        logger.warning(
            "kaizen_portal_notification_failed event=%s",
            (payload.get("metadata") or {}).get("event"),
            exc_info=True,
        )
    return False


def notify_public_suggestion_created(*, record: dict[str, Any]) -> bool:
    record_id = str(record.get("id") or "").strip()
    if not record_id:
        return False

    title = str(record.get("title") or "Sugestão Kaizen").strip()
    proposer = str(record.get("accountable") or "Colaborador").strip()
    sector = str(record.get("sector") or "").strip()

    message = f"{proposer} enviou uma sugestão «{title}»"
    if sector:
        message += f" ({sector})"
    message += ". Abra o cadastro para analisar (status Recebido)."

    payload: dict[str, Any] = {
        "permissionCodes": [CADASTRO_KAIZEN_NOTIFY_SUGGESTIONS],
        "title": "Nova sugestão Kaizen",
        "message": message,
        "type": "info",
        "category": _CATEGORY,
        "sourceApp": _SOURCE_APP,
        "action": {
            "type": "portal_route",
            "label": "Abrir sugestão",
            "target": f"{_APP_BASE}/detalhe/{record_id}",
        },
        "metadata": {
            "source": _SOURCE_APP,
            "event": "kaizen_suggestion_created",
            "dedupeKey": f"kaizen:suggestion:{record_id}",
            "kaizenId": record_id,
        },
    }
    return _post_notification(payload)

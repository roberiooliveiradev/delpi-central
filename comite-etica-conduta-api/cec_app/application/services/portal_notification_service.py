from __future__ import annotations

import logging
from typing import Any

import httpx

from cec_app.config import settings

logger = logging.getLogger("comite_etica.notifications")

_SOURCE_APP = "comite-etica-conduta"
_CATEGORY = "comite_etica_conduta"
_APP_BASE = "/apps/comite-etica-conduta"

EVENT_SIGN_PENDING = "cec_minute_sign_pending"
EVENT_MINUTE_SIGNED = "cec_minute_signed"
EVENT_MINUTE_REFUSED = "cec_minute_refused"


class CecPortalNotificationService:
    def __init__(
        self,
        *,
        core_api_url: str | None = None,
        service_token: str | None = None,
        enabled: bool | None = None,
    ) -> None:
        self.core_api_url = (core_api_url or settings.CORE_API_URL).rstrip("/")
        self.service_token = (
            service_token
            if service_token is not None
            else settings.CORE_API_SERVICE_TOKEN
        )
        self.enabled = (
            settings.CEC_PORTAL_NOTIFICATIONS_ENABLED if enabled is None else enabled
        )

    def minute_sign_route(self, minute_id: str) -> str:
        return f"{_APP_BASE}/atas/{minute_id}/sign"

    def minute_detail_route(self, minute_id: str) -> str:
        return f"{_APP_BASE}/atas/{minute_id}"

    def send(
        self,
        *,
        user_id: str,
        title: str,
        message: str,
        notification_type: str = "info",
        action_label: str = "Abrir ata",
        action_target: str,
        dedupe_key: str,
        event_type: str,
        metadata: dict[str, Any] | None = None,
        # Compat legado (ignora)
        portal_route: str | None = None,
    ) -> bool:
        _ = portal_route
        if not self.enabled:
            return False
        if not self.service_token:
            logger.warning("cec_notification_skipped_no_token")
            return False
        recipient = str(user_id or "").strip()
        if not recipient or recipient == "unknown":
            return False

        payload: dict[str, Any] = {
            "userIds": [recipient],
            "title": title,
            "message": message,
            "type": notification_type,
            "category": _CATEGORY,
            "sourceApp": _SOURCE_APP,
            "action": {
                "type": "portal_route",
                "label": action_label,
                "target": action_target,
            },
            "metadata": {
                "source": _SOURCE_APP,
                "event": event_type,
                "dedupeKey": dedupe_key,
                **(metadata or {}),
            },
        }
        try:
            response = httpx.post(
                f"{self.core_api_url}/integrations/notifications",
                headers={
                    "Authorization": f"Bearer {self.service_token}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=10.0,
            )
            if response.status_code >= 400:
                logger.warning(
                    "cec_notification_rejected status=%s body=%s",
                    response.status_code,
                    response.text[:300],
                )
                return False
            return True
        except Exception:
            logger.exception("cec_notification_failed user=%s", recipient)
            return False

    def notify_sign_pending(
        self,
        *,
        user_id: str,
        minute_id: str,
        minute_number: str,
        title: str,
    ) -> bool:
        return self.send(
            user_id=user_id,
            title="Assinatura de ata do Comitê de Ética pendente",
            message=f"A ata {minute_number} — {title} — aguarda sua assinatura.",
            notification_type="warning",
            action_label="Assinar ata",
            action_target=self.minute_sign_route(minute_id),
            dedupe_key=f"cec:sign_pending:{minute_id}:{user_id}",
            event_type=EVENT_SIGN_PENDING,
            metadata={"minuteId": minute_id, "minuteNumber": minute_number},
        )

    def notify_minute_signed(
        self,
        *,
        user_id: str,
        minute_id: str,
        minute_number: str,
        title: str,
    ) -> bool:
        return self.send(
            user_id=user_id,
            title="Ata do Comitê de Ética assinada",
            message=f"A ata {minute_number} — {title} — foi assinada por todos os signatários.",
            notification_type="success",
            action_label="Abrir ata",
            action_target=self.minute_detail_route(minute_id),
            dedupe_key=f"cec:signed:{minute_id}:{user_id}",
            event_type=EVENT_MINUTE_SIGNED,
            metadata={"minuteId": minute_id, "minuteNumber": minute_number},
        )

    def notify_minute_refused(
        self,
        *,
        user_id: str,
        minute_id: str,
        minute_number: str,
        title: str,
        actor_name: str,
        reason: str,
    ) -> bool:
        return self.send(
            user_id=user_id,
            title="Assinatura de ata recusada",
            message=(
                f"{actor_name} recusou assinar a ata {minute_number} — {title}. "
                f"Motivo: {reason}"
            ),
            notification_type="warning",
            action_label="Abrir ata",
            action_target=self.minute_detail_route(minute_id),
            dedupe_key=f"cec:refused:{minute_id}:{user_id}",
            event_type=EVENT_MINUTE_REFUSED,
            metadata={"minuteId": minute_id, "minuteNumber": minute_number},
        )

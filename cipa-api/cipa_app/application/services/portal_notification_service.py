from __future__ import annotations

import logging
from typing import Any

import httpx

from cipa_app.config import settings

logger = logging.getLogger("cipa.notifications")

_SOURCE_APP = "cipa"
_CATEGORY = "cipa"
_APP_BASE = "/apps/cipa"

EVENT_SIGN_PENDING = "cipa_minute_sign_pending"
EVENT_MINUTE_SIGNED = "cipa_minute_signed"
EVENT_MINUTE_REFUSED = "cipa_minute_refused"


class CipaPortalNotificationService:
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
            else settings.CORE_API_INTEGRATIONS_SERVICE_TOKEN
        )
        self.enabled = (
            settings.CIPA_PORTAL_NOTIFICATIONS_ENABLED if enabled is None else enabled
        )

    def minute_sign_route(self, unit_code: str, minute_id: str) -> str:
        return f"{_APP_BASE}/filial-{unit_code}/minutes/{minute_id}/sign"

    def minute_detail_route(self, unit_code: str, minute_id: str) -> str:
        return f"{_APP_BASE}/filial-{unit_code}/minutes/{minute_id}"

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
        portal_route: str | None = None,
    ) -> bool:
        _ = portal_route
        if not self.enabled:
            return False
        if not self.service_token:
            logger.warning("cipa_notification_skipped_no_token")
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
                    "cipa_notification_rejected status=%s body=%s",
                    response.status_code,
                    response.text[:300],
                )
                return False
            return True
        except Exception:
            logger.exception("cipa_notification_failed user=%s", recipient)
            return False

    def notify_sign_pending(
        self,
        *,
        user_id: str,
        minute_id: str,
        minute_number: str,
        title: str,
        unit_code: str,
        dedupe_key: str | None = None,
    ) -> bool:
        key = (dedupe_key or "").strip() or f"cipa:sign_pending:{minute_id}:{user_id}"
        return self.send(
            user_id=user_id,
            title="Assinatura de ata CIPA pendente",
            message=f"A ata {minute_number} — {title} — aguarda sua assinatura.",
            notification_type="warning",
            action_label="Assinar ata",
            action_target=self.minute_sign_route(unit_code, minute_id),
            dedupe_key=key,
            event_type=EVENT_SIGN_PENDING,
            metadata={
                "minuteId": minute_id,
                "minuteNumber": minute_number,
                "unitCode": unit_code,
            },
        )

    def notify_minute_signed(
        self,
        *,
        user_id: str,
        minute_id: str,
        minute_number: str,
        title: str,
        unit_code: str,
    ) -> bool:
        return self.send(
            user_id=user_id,
            title="Ata CIPA totalmente assinada",
            message=f"A ata {minute_number} — {title} — recebeu todas as assinaturas.",
            notification_type="success",
            action_label="Abrir ata",
            action_target=self.minute_detail_route(unit_code, minute_id),
            dedupe_key=f"cipa:signed:{minute_id}:{user_id}",
            event_type=EVENT_MINUTE_SIGNED,
            metadata={
                "minuteId": minute_id,
                "minuteNumber": minute_number,
                "unitCode": unit_code,
            },
        )

    def notify_minute_refused(
        self,
        *,
        user_id: str,
        minute_id: str,
        minute_number: str,
        title: str,
        unit_code: str,
        actor_name: str,
        reason: str,
    ) -> bool:
        return self.send(
            user_id=user_id,
            title="Assinatura de ata CIPA recusada",
            message=(
                f"{actor_name} recusou assinar a ata {minute_number} — {title}. "
                f"Motivo: {reason}"
            ),
            notification_type="warning",
            action_label="Abrir ata",
            action_target=self.minute_detail_route(unit_code, minute_id),
            dedupe_key=f"cipa:refused:{minute_id}:{user_id}",
            event_type=EVENT_MINUTE_REFUSED,
            metadata={
                "minuteId": minute_id,
                "minuteNumber": minute_number,
                "unitCode": unit_code,
            },
        )

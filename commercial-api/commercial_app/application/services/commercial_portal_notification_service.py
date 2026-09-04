"""Send Minha Delpi portal notifications from commercial-api."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Sequence

import httpx

from commercial_app.config import settings
from commercial_app.domain.services.ready_to_invoice_notification_content_service import (
    ReadyToInvoiceNotificationContentService,
)

logger = logging.getLogger("commercial.portal_notifications")

_SOURCE_APP = "commercial"
_CATEGORY = "commercial"

EVENT_READY_TO_INVOICE = "commercial.order.ready_to_invoice"


@dataclass(frozen=True, slots=True)
class PortalNotifyResult:
    """Outcome of a core-api portal notification POST."""

    ok: bool
    rate_limited: bool = False

    def __bool__(self) -> bool:
        return self.ok


class CommercialPortalNotificationService:
    def __init__(
        self,
        *,
        core_api_url: str | None = None,
        service_token: str | None = None,
        enabled: bool | None = None,
        timeout: float | None = None,
    ) -> None:
        self.core_api_url = (core_api_url or settings.CORE_API_BASE_URL).rstrip("/")
        self.service_token = (
            service_token
            if service_token is not None
            else settings.CORE_API_INTEGRATIONS_SERVICE_TOKEN
        )
        self.enabled = (
            settings.COMMERCIAL_PORTAL_NOTIFICATIONS_ENABLED
            if enabled is None
            else enabled
        )
        self.timeout = float(
            timeout if timeout is not None else settings.CORE_API_TIMEOUT or 10
        )

    def send(
        self,
        *,
        user_ids: Sequence[str] | None = None,
        permission_codes: Sequence[str] | None = None,
        title: str,
        message: str,
        notification_type: str = "info",
        action_label: str,
        action_target: str,
        dedupe_key: str,
        event_type: str,
        category: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> PortalNotifyResult:
        if not self.enabled:
            return PortalNotifyResult(ok=False)
        if not self.service_token:
            logger.warning("commercial_notification_skipped_no_token")
            return PortalNotifyResult(ok=False)

        recipients = [
            str(uid).strip() for uid in (user_ids or ()) if str(uid).strip()
        ]
        codes = [
            str(code).strip()
            for code in (permission_codes or ())
            if str(code).strip()
        ]
        if not recipients and not codes:
            return PortalNotifyResult(ok=False)

        payload: dict[str, Any] = {
            "title": title,
            "message": message,
            "type": notification_type,
            "category": (category or _CATEGORY).strip() or _CATEGORY,
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
        if recipients:
            payload["userIds"] = recipients
        if codes:
            payload["permissionCodes"] = codes

        try:
            response = httpx.post(
                f"{self.core_api_url}/integrations/notifications",
                headers={
                    "Authorization": f"Bearer {self.service_token}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=self.timeout,
            )
            if response.status_code == 429:
                logger.warning(
                    "commercial_notification_rate_limited body=%s",
                    response.text[:300],
                )
                return PortalNotifyResult(ok=False, rate_limited=True)
            if response.status_code >= 400:
                logger.warning(
                    "commercial_notification_rejected status=%s body=%s",
                    response.status_code,
                    response.text[:300],
                )
                return PortalNotifyResult(ok=False)
            return PortalNotifyResult(ok=True)
        except Exception:
            logger.exception("commercial_notification_failed dedupe=%s", dedupe_key)
            return PortalNotifyResult(ok=False)

    def notify_ready_to_invoice(
        self,
        *,
        user_ids: Sequence[str],
        permission_codes: Sequence[str],
        line_key: str,
        pedido: str,
        linha: str,
        cliente: str,
        action_target: str | None = None,
        filial: str = "",
    ) -> PortalNotifyResult:
        content = ReadyToInvoiceNotificationContentService
        block = content.notification_block()
        title = str(block.get("title") or "Pedido pronto para faturar").strip()
        action_label = str(block.get("actionLabel") or "Abrir pedidos").strip()
        notification_type = str(block.get("type") or "info").strip() or "info"
        message = content.format_message(
            pedido=pedido, linha=linha, cliente=cliente or "—"
        )
        target = (action_target or "").strip() or content.build_deep_link_path(
            pedido=pedido,
            linha=linha,
            filial=filial,
        )
        # Layout do usuário (tabela/cards/board) — nunca forçar view=board.
        target = content.without_forced_view(target)
        return self.send(
            user_ids=user_ids,
            permission_codes=permission_codes,
            title=title,
            message=message,
            notification_type=notification_type,
            action_label=action_label,
            action_target=target,
            dedupe_key=f"commercial:ready_to_invoice:{line_key}",
            event_type=EVENT_READY_TO_INVOICE,
            metadata={
                "lineKey": line_key,
                "pedido": pedido,
                "linha": linha,
                "filial": filial,
            },
        )

    def notify_task_event(
        self,
        *,
        event_type: str,
        user_ids: Sequence[str],
        task_id: str,
        title: str,
        due_at: str | None = None,
        action_target: str | None = None,
        dedupe_key: str | None = None,
        bucket: str | None = None,
    ) -> PortalNotifyResult:
        from commercial_app.domain.services.task_portal_notification_content_service import (
            TASK_PORTAL_EVENT_TYPES,
            TaskPortalNotificationContentService as Content,
        )

        if event_type not in TASK_PORTAL_EVENT_TYPES:
            return PortalNotifyResult(ok=False)
        action_label = Content.action_label()
        notification_type = Content.notification_type_for(event_type)
        message = Content.format_message(
            event_type, title=title, due_at_iso=due_at
        )
        target = (action_target or "").strip() or Content.build_deep_link_path(
            bucket=bucket or Content.bucket_for(event_type),
            search=title,
        )
        return self.send(
            user_ids=user_ids,
            permission_codes=[],
            title=Content.title_for(event_type),
            message=message,
            notification_type=notification_type,
            action_label=action_label,
            action_target=target,
            dedupe_key=dedupe_key
            or f"commercial:task:{event_type}:{task_id}",
            event_type=event_type,
            category=Content.category(),
            metadata={
                "taskId": task_id,
                "bucket": bucket or Content.bucket_for(event_type),
            },
        )

    def notify_interaction_mention(
        self,
        *,
        user_ids: Sequence[str],
        room_id: str,
        message_id: str,
        actor_display_name: str,
        excerpt: str,
        action_target: str | None = None,
        dedupe_key: str | None = None,
    ) -> PortalNotifyResult:
        from commercial_app.domain.services.interaction_room_content_service import (
            InteractionRoomContentService as Content,
        )

        block = Content.notification("mention")
        title = str(block.get("title") or "Você foi mencionado na sala").strip()
        action_label = str(block.get("actionLabel") or "Abrir sala").strip()
        notification_type = str(block.get("type") or "info").strip() or "info"
        message = Content.format_mention_message(
            actor=actor_display_name,
            excerpt=excerpt,
        )
        target = (action_target or "").strip() or Content.mention_deep_link(
            room_id=room_id
        )
        return self.send(
            user_ids=user_ids,
            permission_codes=[],
            title=title,
            message=message,
            notification_type=notification_type,
            action_label=action_label,
            action_target=target,
            dedupe_key=dedupe_key
            or f"commercial:interaction:mention:{message_id}",
            event_type=Content.mention_event_type(),
            category=Content.mention_category(),
            metadata={
                "roomId": room_id,
                "messageId": message_id,
            },
        )

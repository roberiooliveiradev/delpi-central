"""Send Minha Delpi portal notifications from commercial-api."""

from __future__ import annotations

import logging
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
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        if not self.enabled:
            return False
        if not self.service_token:
            logger.warning("commercial_notification_skipped_no_token")
            return False

        recipients = [
            str(uid).strip() for uid in (user_ids or ()) if str(uid).strip()
        ]
        codes = [
            str(code).strip()
            for code in (permission_codes or ())
            if str(code).strip()
        ]
        if not recipients and not codes:
            return False

        payload: dict[str, Any] = {
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
            if response.status_code >= 400:
                logger.warning(
                    "commercial_notification_rejected status=%s body=%s",
                    response.status_code,
                    response.text[:300],
                )
                return False
            return True
        except Exception:
            logger.exception("commercial_notification_failed dedupe=%s", dedupe_key)
            return False

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
    ) -> bool:
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

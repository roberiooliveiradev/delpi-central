"""Send Minha Delpi portal notifications from purchase-requests-api."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Sequence

import httpx

from purchase_requests_app.config import settings
from purchase_requests_app.domain.services.purchase_order_linked_notification_content_service import (
    PurchaseOrderLinkedNotificationContentService as Content,
)

logger = logging.getLogger("purchase_requests.portal_notifications")

EVENT_PURCHASE_ORDER_CREATED = "purchase_order_created"


@dataclass(frozen=True)
class PortalNotifyOutcome:
    delivered: bool
    retry: bool

    def __bool__(self) -> bool:
        return self.delivered

    @classmethod
    def sent(cls) -> PortalNotifyOutcome:
        return cls(delivered=True, retry=False)

    @classmethod
    def skip(cls) -> PortalNotifyOutcome:
        return cls(delivered=False, retry=False)

    @classmethod
    def retry_later(cls) -> PortalNotifyOutcome:
        return cls(delivered=False, retry=True)


class PurchaseRequestsPortalNotificationService:
    def __init__(
        self,
        *,
        core_api_url: str | None = None,
        service_token: str | None = None,
        enabled: bool | None = None,
        timeout: float | None = None,
        http_post=None,
    ) -> None:
        self.core_api_url = (core_api_url or settings.CORE_API_BASE_URL).rstrip("/")
        self.service_token = (
            service_token
            if service_token is not None
            else settings.CORE_API_INTEGRATIONS_SERVICE_TOKEN
        )
        self.enabled = (
            settings.PURCHASE_REQUESTS_PO_NOTIFICATIONS_ENABLED
            if enabled is None
            else enabled
        )
        self.timeout = float(
            timeout if timeout is not None else settings.CORE_API_TIMEOUT or 10
        )
        self._http_post = http_post or httpx.post

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
    ) -> PortalNotifyOutcome:
        if not self.enabled:
            return PortalNotifyOutcome.retry_later()
        if not self.service_token:
            logger.warning("purchase_requests_notification_skipped_no_token")
            return PortalNotifyOutcome.retry_later()

        recipients = [
            str(uid).strip() for uid in (user_ids or ()) if str(uid).strip()
        ]
        codes = [
            str(code).strip()
            for code in (permission_codes or ())
            if str(code).strip()
        ]
        if not recipients and not codes:
            return PortalNotifyOutcome.skip()

        payload: dict[str, Any] = {
            "title": title,
            "message": message,
            "type": notification_type,
            "category": (category or Content.category()).strip() or Content.category(),
            "sourceApp": Content.source_app(),
            "action": {
                "type": "portal_route",
                "label": action_label,
                "target": action_target,
            },
            "metadata": {
                "source": Content.source_app(),
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
            response = self._http_post(
                f"{self.core_api_url}/integrations/notifications",
                headers={
                    "Authorization": f"Bearer {self.service_token}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=self.timeout,
            )
            if response.status_code >= 400:
                body = response.text[:300]
                logger.warning(
                    "purchase_requests_notification_rejected status=%s body=%s",
                    response.status_code,
                    body,
                )
                if _is_permanent_recipient_rejection(response.status_code, body):
                    return PortalNotifyOutcome.skip()
                return PortalNotifyOutcome.retry_later()
            return PortalNotifyOutcome.sent()
        except Exception:
            logger.exception("purchase_requests_notification_failed dedupe=%s", dedupe_key)
            return PortalNotifyOutcome.retry_later()

    def notify_purchase_order_linked(
        self,
        *,
        user_ids: Sequence[str],
        branch: str,
        order_number: str,
        order_item: str,
        request_number: str,
        product_code: str,
        product_description: str | None,
        supplier_name: str | None,
        expected_delivery_date: str | None,
    ) -> PortalNotifyOutcome:
        title = Content.format_title(
            order_number=order_number,
            request_number=request_number,
        )
        message = Content.format_message(
            product_code=product_code,
            product_description=product_description,
            supplier_name=supplier_name,
            expected_delivery_date=expected_delivery_date,
        )
        action_target = Content.build_deep_link_path(
            branch=branch,
            request_number=request_number,
        )
        dedupe_key = (
            f"{Content.source_app()}:purchase_order_created:"
            f"{branch}:{order_number}:{order_item}"
        )
        return self.send(
            user_ids=user_ids,
            title=title,
            message=message,
            notification_type=Content.notification_type(),
            action_label=Content.action_label(),
            action_target=action_target,
            dedupe_key=dedupe_key,
            event_type=Content.event_type() or EVENT_PURCHASE_ORDER_CREATED,
            category=Content.category(),
            metadata={
                "branch": branch,
                "orderNumber": order_number,
                "orderItem": order_item,
                "requestNumber": request_number,
                "productCode": product_code,
            },
        )


def _is_permanent_recipient_rejection(status_code: int, body: str) -> bool:
    if status_code != 400:
        return False
    lowered = (body or "").lower()
    return any(
        marker in lowered for marker in Content.core_permanent_rejection_substrings()
    )

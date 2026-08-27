from __future__ import annotations

import logging
from typing import Any

from purchase_requests_app.application.services.purchase_request_notification_preference_service import (
    PurchaseRequestNotificationPreferenceService,
)
from purchase_requests_app.application.services.purchase_requests_portal_notification_service import (
    PurchaseRequestsPortalNotificationService,
)
from purchase_requests_app.infrastructure.gateways.delpi_purchase_requests_gateway import (
    DelpiPurchaseRequestsGateway,
)
from purchase_requests_app.infrastructure.persistence.repositories.dispatched_purchase_receipt_event_repository import (
    DispatchedPurchaseReceiptEventRepository,
)
from purchase_requests_app.infrastructure.persistence.repositories.purchase_order_notification_cursor_repository import (
    JOB_KEY_PURCHASE_RECEIPT_RECORDED,
    PurchaseOrderNotificationCursorRepository,
)

logger = logging.getLogger("purchase_requests.receipt_notification_dispatch")


class DispatchPurchaseReceiptRecordedNotificationsUseCase:
    def __init__(
        self,
        *,
        gateway: DelpiPurchaseRequestsGateway | None = None,
        cursor_repository: PurchaseOrderNotificationCursorRepository | None = None,
        dispatched_repository: DispatchedPurchaseReceiptEventRepository | None = None,
        preference_service: PurchaseRequestNotificationPreferenceService | None = None,
        notification_service: PurchaseRequestsPortalNotificationService | None = None,
        job_key: str = JOB_KEY_PURCHASE_RECEIPT_RECORDED,
        limit: int = 100,
    ) -> None:
        self._gateway = gateway or DelpiPurchaseRequestsGateway()
        self._cursors = cursor_repository or PurchaseOrderNotificationCursorRepository()
        self._dispatched = dispatched_repository or DispatchedPurchaseReceiptEventRepository()
        self._preferences = preference_service or PurchaseRequestNotificationPreferenceService()
        self._notifications = (
            notification_service or PurchaseRequestsPortalNotificationService()
        )
        self._job_key = job_key
        self._limit = limit

    def execute(self) -> dict[str, Any]:
        last_recno = self._cursors.get_last_recno(self._job_key)
        payload = self._gateway.list_recent_linked_receipts(
            after_recno=int(last_recno or 0),
            limit=self._limit,
        )
        items = list(payload.get("items") or [])
        max_recno = int(payload.get("max_recno") or 0)
        if last_recno is None:
            watermark = max(max_recno, _max_item_recno(items))
            self._cursors.upsert_last_recno(self._job_key, watermark)
            logger.info(
                "purchase_receipt_recorded_first_run watermark=%s items_ignored=%s",
                watermark,
                len(items),
            )
            return {
                "first_run": True,
                "dispatched": 0,
                "skipped": 0,
                "last_recno": watermark,
            }

        dispatched = 0
        skipped = 0
        cursor = int(last_recno)
        for item in sorted(items, key=lambda row: int(row.get("recno") or 0)):
            recno = int(item.get("recno") or 0)
            branch = str(item.get("branch") or "").strip()
            invoice_number = str(item.get("invoice_number") or "").strip()
            invoice_series = str(item.get("invoice_series") or "").strip()
            invoice_item = str(item.get("invoice_item") or "").strip()
            request_number = str(item.get("request_number") or "").strip()
            order_number = str(item.get("order_number") or "").strip()
            if not branch or not invoice_number or not invoice_item:
                skipped += 1
                if recno > cursor:
                    cursor = recno
                continue
            if self._dispatched.exists(
                branch=branch,
                invoice_number=invoice_number,
                invoice_series=invoice_series,
                invoice_item=invoice_item,
            ):
                skipped += 1
                if recno > cursor:
                    cursor = recno
                continue
            requester = str(item.get("requester_protheus_user_id") or "").strip()
            user_ids = self._preferences.portal_users_for_mapped_requester(requester)
            if not user_ids:
                skipped += 1
                if recno > cursor:
                    cursor = recno
                continue
            outcome = self._notifications.notify_purchase_receipt_recorded(
                user_ids=user_ids,
                branch=branch,
                invoice_number=invoice_number,
                invoice_series=invoice_series,
                invoice_item=invoice_item,
                request_number=request_number,
                order_number=order_number,
                product_code=str(item.get("product_code") or ""),
                product_description=item.get("product_description"),
                supplier_name=item.get("supplier_name"),
                quantity=item.get("quantity"),
                entry_date=item.get("entry_date"),
            )
            delivered = bool(outcome)
            retry = bool(getattr(outcome, "retry", not delivered))
            if not delivered:
                skipped += 1
                if retry:
                    break
                if recno > cursor:
                    cursor = recno
                continue
            self._dispatched.mark_dispatched(
                branch=branch,
                invoice_number=invoice_number,
                invoice_series=invoice_series,
                invoice_item=invoice_item,
                request_number=request_number,
                order_number=order_number,
                recno=recno,
            )
            dispatched += 1
            if recno > cursor:
                cursor = recno

        self._cursors.upsert_last_recno(self._job_key, cursor)
        return {
            "first_run": False,
            "dispatched": dispatched,
            "skipped": skipped,
            "last_recno": cursor,
        }


def _max_item_recno(items: list[dict[str, Any]]) -> int:
    recnos = [int(item.get("recno") or 0) for item in items]
    return max(recnos) if recnos else 0

"""Background poller — notify portal users when TOTVS links a PO to an SC."""

from __future__ import annotations

import asyncio
import logging

from purchase_requests_app.application.use_cases.dispatch_purchase_order_linked_notifications_use_case import (
    DispatchPurchaseOrderLinkedNotificationsUseCase,
)
from purchase_requests_app.config import settings

logger = logging.getLogger("purchase_requests.po_notification_job")


async def run_purchase_order_linked_notification_loop() -> None:
    interval = max(15, int(settings.PURCHASE_REQUESTS_PO_NOTIFICATIONS_INTERVAL_SECONDS))
    use_case = DispatchPurchaseOrderLinkedNotificationsUseCase()
    while True:
        try:
            result = await asyncio.to_thread(use_case.execute)
            logger.info(
                "purchase_order_linked_poll first_run=%s dispatched=%s skipped=%s last_recno=%s",
                result.get("first_run"),
                result.get("dispatched"),
                result.get("skipped"),
                result.get("last_recno"),
            )
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("purchase_order_linked_poll_failed")
        await asyncio.sleep(interval)

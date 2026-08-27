"""Background poller — notify portal users when TOTVS records a receipt on an SC."""

from __future__ import annotations

import asyncio
import logging

from purchase_requests_app.application.use_cases.dispatch_purchase_receipt_recorded_notifications_use_case import (
    DispatchPurchaseReceiptRecordedNotificationsUseCase,
)
from purchase_requests_app.config import settings

logger = logging.getLogger("purchase_requests.receipt_notification_job")


async def run_purchase_receipt_recorded_notification_loop() -> None:
    interval = max(15, int(settings.PURCHASE_REQUESTS_PO_NOTIFICATIONS_INTERVAL_SECONDS))
    use_case = DispatchPurchaseReceiptRecordedNotificationsUseCase()
    while True:
        try:
            result = await asyncio.to_thread(use_case.execute)
            logger.info(
                "purchase_receipt_recorded_poll first_run=%s dispatched=%s skipped=%s last_recno=%s",
                result.get("first_run"),
                result.get("dispatched"),
                result.get("skipped"),
                result.get("last_recno"),
            )
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("purchase_receipt_recorded_poll_failed")
        await asyncio.sleep(interval)

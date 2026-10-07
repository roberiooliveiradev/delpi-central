"""Background poller — notify portal users when an SC is approved/rejected."""

from __future__ import annotations

import asyncio
import logging

from purchase_requests_app.application.use_cases.dispatch_purchase_request_approval_notifications_use_case import (
    DispatchPurchaseRequestApprovalNotificationsUseCase,
)
from purchase_requests_app.config import settings

logger = logging.getLogger("purchase_requests.approval_notification_job")


async def run_purchase_request_approval_notification_loop() -> None:
    interval = max(
        15, int(settings.PURCHASE_REQUESTS_APPROVAL_NOTIFICATIONS_INTERVAL_SECONDS)
    )
    use_case = DispatchPurchaseRequestApprovalNotificationsUseCase()
    while True:
        try:
            result = await asyncio.to_thread(use_case.execute)
            if result.get("first_run") or result.get("claimed") or result.get("retry"):
                logger.info(
                    "purchase_request_approval_poll first_run=%s observed=%s "
                    "baseline=%s claimed=%s dispatched=%s retry=%s",
                    result.get("first_run"),
                    result.get("observed"),
                    result.get("baseline"),
                    result.get("claimed"),
                    result.get("dispatched"),
                    result.get("retry"),
                )
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("purchase_request_approval_poll_failed")
        await asyncio.sleep(interval)

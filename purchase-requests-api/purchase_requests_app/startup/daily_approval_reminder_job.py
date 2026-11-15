import asyncio
import logging

from purchase_requests_app.application.use_cases.dispatch_daily_approval_reminders_use_case import (
    DispatchDailyApprovalRemindersUseCase,
)
from purchase_requests_app.config import settings

logger = logging.getLogger("purchase_requests.daily_approval_reminders")


async def run_daily_approval_reminder_loop():
    use_case = DispatchDailyApprovalRemindersUseCase()
    interval = max(
        60, settings.PURCHASE_REQUESTS_APPROVAL_NOTIFICATIONS_INTERVAL_SECONDS
    )
    while True:
        try:
            result = await asyncio.to_thread(use_case.execute)
            logger.info("daily_approval_reminders_poll counts=%s", result)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("daily_approval_reminders_poll_failed")
        await asyncio.sleep(interval)

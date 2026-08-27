"""Background poller — reconcilia entrega de e-mail de convites via Message Trace."""

from __future__ import annotations

import asyncio
import logging

from tm_app.application.services.sign_invite_mail_trace_reconciliation_service import (
    SignInviteMailTraceReconciliationService,
)
from tm_app.config import settings

logger = logging.getLogger("transformometro.mail.trace_job")


async def run_sign_invite_mail_trace_loop() -> None:
    interval_minutes = max(
        5,
        int(settings.TM_SIGN_INVITE_MAIL_TRACE_INTERVAL_MINUTES or "15"),
    )
    interval_seconds = interval_minutes * 60
    service = SignInviteMailTraceReconciliationService()
    while True:
        try:
            result = await asyncio.to_thread(service.execute)
            logger.info(
                "tm_sign_invite_mail_trace_poll processed=%s updated=%s enabled=%s",
                result.get("processed"),
                result.get("updated"),
                result.get("enabled"),
            )
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("tm_sign_invite_mail_trace_poll_failed")
        await asyncio.sleep(interval_seconds)

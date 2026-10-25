"""Background poller — recupera eventos da outbox de notificação.

R-105-05: evento `EMITTED`/`FAILED` deve ser recuperado e entregue ao
Core mesmo sem nova ação do usuário. Padrão canônico da plataforma
(mesmo modelo de `cipa-api/.../sign_invite_mail_trace_job.py` e dos
pollers de `purchase-requests-api`): loop asyncio no lifespan do app,
`asyncio.to_thread` para o trabalho síncrono, exceções logadas e nunca
fatais — a entrega é best-effort e não altera estado de negócio.
"""

from __future__ import annotations

import asyncio
import logging

from controllership_finance_app.config import settings
from controllership_finance_app.infrastructure.gateways.core_notifications_gateway import (
    CoreNotificationsDispatcher,
)
from controllership_finance_app.infrastructure.persistence.plugins_db import (
    plugins_db_configured,
)

logger = logging.getLogger("controllership_finance.notifications")


async def run_closing_notification_dispatch_loop() -> None:
    interval_seconds = max(
        15,
        int(
            getattr(
                settings,
                "CF_NOTIFICATION_DISPATCH_INTERVAL_SECONDS",
                None,
            )
            or 60
        ),
    )
    dispatcher = CoreNotificationsDispatcher()
    while True:
        try:
            if plugins_db_configured():
                result = await asyncio.to_thread(
                    dispatcher.dispatch_pending
                )
                if result.get("dispatched") or result.get("failed"):
                    logger.info(
                        "cf_notification_dispatch_cycle %s", result
                    )
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("cf_notification_dispatch_cycle_failed")
        await asyncio.sleep(interval_seconds)

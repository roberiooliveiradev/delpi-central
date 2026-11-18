"""Background poller — consumidor durável da outbox de checklist sync.

CF-CHECKLIST-LIVE-004 (RQ-03/12): mesmo padrão canônico de
`notification_dispatch_job` — loop asyncio no lifespan, `to_thread`,
claim `FOR UPDATE SKIP LOCKED` no dispatcher, exceções logadas nunca
fatais. Evento persiste restart; runs convergem por reconciliação.
"""

from __future__ import annotations

import asyncio
import logging

from controllership_finance_app.config import settings
from controllership_finance_app.infrastructure.persistence.closing_checklist_repository import (
    ClosingChecklistRepository,
)
from controllership_finance_app.infrastructure.persistence.plugins_db import (
    plugins_db_configured,
)

logger = logging.getLogger("controllership_finance.checklist_sync")


async def run_checklist_sync_dispatch_loop() -> None:
    interval_seconds = max(
        15,
        int(
            getattr(
                settings,
                "CF_CHECKLIST_SYNC_DISPATCH_INTERVAL_SECONDS",
                None,
            )
            or 60
        ),
    )
    repository = ClosingChecklistRepository()
    while True:
        try:
            if plugins_db_configured():
                result = await asyncio.to_thread(
                    repository.dispatch_sync_events
                )
                if result.get("claimed"):
                    logger.info(
                        "cf_checklist_sync_dispatch_cycle %s", result
                    )
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("cf_checklist_sync_dispatch_cycle_failed")
        await asyncio.sleep(interval_seconds)

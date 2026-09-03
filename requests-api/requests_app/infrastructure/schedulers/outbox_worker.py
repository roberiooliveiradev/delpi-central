from __future__ import annotations

import asyncio
import logging
from contextlib import suppress

from requests_app.config import settings
from requests_app.domain.ports.integration_outbox_port import IntegrationOutboxRepositoryPort
from requests_app.infrastructure.gateways.core_notification_adapter import (
    CoreNotificationAdapter,
    PortalNotificationPort,
)

logger = logging.getLogger(__name__)


class PublishOutboxUseCase:
    def __init__(
        self,
        outbox: IntegrationOutboxRepositoryPort,
        notifier: PortalNotificationPort,
    ) -> None:
        self._outbox = outbox
        self._notifier = notifier

    def execute(self, *, limit: int = 50) -> int:
        pending = self._outbox.list_pending(limit=limit)
        published = 0
        for row in pending:
            try:
                self._notifier.publish(row)
                self._outbox.mark_published(row.id)
                published += 1
            except Exception as exc:  # noqa: BLE001
                logger.exception("outbox_publish_failed id=%s", row.id)
                self._outbox.mark_failed(row.id, error=str(exc))
        return published


async def run_outbox_worker_loop(
    *,
    outbox: IntegrationOutboxRepositoryPort,
    notifier: PortalNotificationPort | None = None,
    interval_seconds: float = 5.0,
) -> None:
    use_case = PublishOutboxUseCase(outbox, notifier or CoreNotificationAdapter())
    while True:
        try:
            use_case.execute()
        except Exception:  # noqa: BLE001
            logger.exception("outbox_worker_tick_failed")
        await asyncio.sleep(interval_seconds)


def should_start_outbox_worker() -> bool:
    return bool(settings.REQUESTS_OUTBOX_WORKER_ENABLED)

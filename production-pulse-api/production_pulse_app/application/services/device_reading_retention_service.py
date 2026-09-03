from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from production_pulse_app.infrastructure.content.telemetry_persistence_content_service import (
    purge_batch_size,
    raw_retention_days,
)
from production_pulse_app.infrastructure.persistence.repositories.postgres_device_reading_repository import (
    PostgresDeviceReadingRepository,
)

logger = logging.getLogger(__name__)


class DeviceReadingRetentionService:
    """R49 — purge de readings raw além de rawRetentionDays."""

    def __init__(
        self,
        reading_repository: PostgresDeviceReadingRepository | None = None,
    ) -> None:
        self._readings = reading_repository or PostgresDeviceReadingRepository()

    def purge_expired_raw(
        self,
        *,
        now: datetime | None = None,
        retention_days: int | None = None,
        batch_size: int | None = None,
        max_batches: int = 20,
    ) -> dict[str, Any]:
        current = now or datetime.now(timezone.utc)
        if current.tzinfo is None:
            current = current.replace(tzinfo=timezone.utc)
        days = retention_days if retention_days is not None else raw_retention_days()
        size = batch_size if batch_size is not None else purge_batch_size()
        cutoff = current - timedelta(days=max(1, int(days)))

        total_deleted = 0
        batches = 0
        while batches < max(1, int(max_batches)):
            deleted = self._readings.delete_older_than(cutoff=cutoff, batch_size=size)
            batches += 1
            total_deleted += deleted
            if deleted < size:
                break

        if total_deleted:
            logger.info(
                "Purged %s raw reading(s) older than %s days (cutoff=%s, batches=%s).",
                total_deleted,
                days,
                cutoff.isoformat(),
                batches,
            )
        return {
            "deleted": total_deleted,
            "batches": batches,
            "cutoff": cutoff,
            "retentionDays": days,
        }

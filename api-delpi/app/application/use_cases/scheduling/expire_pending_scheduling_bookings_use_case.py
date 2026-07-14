from __future__ import annotations

from typing import Any

from app.application.services.scheduling_portal_notification_service import (
    notify_booking_decision,
)
from app.infrastructure.persistence.plugins.repositories.scheduling.postgres_scheduling_repository import (
    PostgresSchedulingRepository,
)


class ExpirePendingSchedulingBookingsUseCase:
    def __init__(self, repository: PostgresSchedulingRepository) -> None:
        self._repository = repository

    def execute(self, *, branch_code: str | None = None) -> list[dict[str, Any]]:
        expired = self._repository.expire_overdue_pending_bookings(branch_code=branch_code)
        for booking in expired:
            if booking:
                notify_booking_decision(booking=booking, event_type="booking_expired")
        return [row for row in expired if row]

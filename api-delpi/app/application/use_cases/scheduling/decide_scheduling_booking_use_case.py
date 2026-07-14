from __future__ import annotations

from typing import Any, Literal

from app.application.services.scheduling_portal_notification_service import (
    notify_booking_decision,
)
from app.application.use_cases.scheduling.expire_pending_scheduling_bookings_use_case import (
    ExpirePendingSchedulingBookingsUseCase,
)
from app.infrastructure.persistence.plugins.plugin_base_repository import PluginsRepositoryError
from app.infrastructure.persistence.plugins.repositories.scheduling.postgres_scheduling_repository import (
    PostgresSchedulingRepository,
)

DecisionAction = Literal["approve", "reject"]


class DecideSchedulingBookingUseCase:
    def __init__(self, repository: PostgresSchedulingRepository) -> None:
        self._repository = repository
        self._expire = ExpirePendingSchedulingBookingsUseCase(repository)

    def execute(
        self,
        *,
        booking_id: str,
        action: DecisionAction,
        actor_user_id: str,
        actor_name: str,
        reason: str | None = None,
        is_superadmin: bool = False,
    ) -> dict[str, Any]:
        booking = self._repository.get_booking(booking_id)
        if not booking:
            raise PluginsRepositoryError("Reserva não encontrada.")

        branch = str(booking["branch_code"])
        self._expire.execute(branch_code=branch)

        booking = self._repository.get_booking(booking_id)
        if not booking:
            raise PluginsRepositoryError("Reserva não encontrada.")

        if booking.get("status") != "pending":
            raise PluginsRepositoryError("Somente reservas pendentes podem ser decididas.")

        if (
            not is_superadmin
            and str(booking.get("booked_by_user_id")) == actor_user_id
        ):
            raise PluginsRepositoryError(
                "Você não pode aprovar ou rejeitar a própria solicitação."
            )

        if action == "reject":
            clean_reason = (reason or "").strip()
            if len(clean_reason) < 3:
                raise PluginsRepositoryError("Informe o motivo da rejeição (mínimo 3 caracteres).")
            status = "rejected"
            event = "booking_rejected"
        else:
            clean_reason = (reason or "").strip() or None
            status = "confirmed"
            event = "booking_approved"

        updated = self._repository.decide_booking(
            booking_id,
            status=status,  # type: ignore[arg-type]
            decided_by_user_id=actor_user_id,
            decided_by_name=actor_name,
            decision_reason=clean_reason,
        )
        if not updated:
            raise PluginsRepositoryError(
                "Não foi possível registrar a decisão. A reserva pode ter expirado."
            )

        notify_booking_decision(booking=updated, event_type=event)
        return updated

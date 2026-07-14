from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from app.application.services.scheduling_portal_notification_service import (
    notify_booking_approval_requested,
)
from app.application.use_cases.scheduling.expire_pending_scheduling_bookings_use_case import (
    ExpirePendingSchedulingBookingsUseCase,
)
from app.config import settings
from app.infrastructure.persistence.plugins.plugin_base_repository import PluginsRepositoryError
from app.infrastructure.persistence.plugins.repositories.scheduling.postgres_scheduling_repository import (
    BookingConflictError,
    PostgresSchedulingRepository,
)


class CreateSchedulingBookingUseCase:
    def __init__(self, repository: PostgresSchedulingRepository) -> None:
        self._repository = repository
        self._expire = ExpirePendingSchedulingBookingsUseCase(repository)

    def execute(
        self,
        *,
        branch_code: str,
        resource_id: str,
        title: str,
        notes: str | None,
        start_at: datetime,
        end_at: datetime,
        booked_by_user_id: str,
        booked_by_name: str,
        recurrence: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], str, str]:
        """
        Returns (data, operation_id, message).
        """
        self._expire.execute(branch_code=branch_code)

        resource = self._repository.get_resource(resource_id)
        if not resource:
            raise PluginsRepositoryError("Recurso não encontrado.")
        if str(resource["branch_code"]) != branch_code:
            raise PluginsRepositoryError("Recurso não pertence à filial informada.")
        if not resource.get("active", True):
            raise PluginsRepositoryError("Recurso inativo.")

        requires_approval = bool(resource.get("requires_approval"))

        if recurrence:
            if requires_approval:
                raise PluginsRepositoryError(
                    "Recursos que exigem aprovação não permitem recorrência. "
                    "Solicite cada horário individualmente."
                )
            if recurrence["until"] < start_at:
                raise PluginsRepositoryError(
                    "A data final da recorrência deve ser igual ou posterior ao início."
                )
            data = self._repository.create_recurring_bookings(
                resource_id=resource_id,
                branch_code=branch_code,
                title=title,
                notes=notes,
                start_at=start_at,
                end_at=end_at,
                booked_by_user_id=booked_by_user_id,
                booked_by_name=booked_by_name,
                frequency=recurrence["frequency"],
                until=recurrence["until"],
                interval=int(recurrence.get("interval") or 1),
            )
            created_count = int(data.get("total_created", 0))
            skipped_count = int(data.get("total_skipped", 0))
            if skipped_count:
                message = (
                    f"Série recorrente criada com {created_count} reserva(s). "
                    f"{skipped_count} horário(s) ignorado(s) por conflito."
                )
            else:
                message = f"Série recorrente criada com {created_count} reserva(s)."
            return data, "create_scheduling_recurring_booking", message

        status = "pending" if requires_approval else "confirmed"
        expires_at = None
        if requires_approval:
            ttl_hours = max(1, int(settings.SCHEDULING_APPROVAL_TTL_HOURS or 24))
            expires_at = datetime.now(timezone.utc) + timedelta(hours=ttl_hours)

        data = self._repository.create_booking(
            resource_id=resource_id,
            branch_code=branch_code,
            title=title,
            notes=notes,
            start_at=start_at,
            end_at=end_at,
            booked_by_user_id=booked_by_user_id,
            booked_by_name=booked_by_name,
            status=status,
            expires_at=expires_at,
        )

        if status == "pending":
            notify_booking_approval_requested(booking=data)
            return (
                data,
                "create_scheduling_booking",
                "Solicitação enviada. Aguarde a aprovação.",
            )

        return data, "create_scheduling_booking", "Reserva confirmada com sucesso."


__all__ = [
    "BookingConflictError",
    "CreateSchedulingBookingUseCase",
    "PluginsRepositoryError",
]

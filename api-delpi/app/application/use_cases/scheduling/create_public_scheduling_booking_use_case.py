from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.application.services.scheduling_portal_notification_service import (
    notify_booking_approval_requested,
)
from app.application.use_cases.scheduling.expire_pending_scheduling_bookings_use_case import (
    ExpirePendingSchedulingBookingsUseCase,
)
from app.infrastructure.persistence.plugins.plugin_base_repository import PluginsRepositoryError
from app.infrastructure.persistence.plugins.repositories.scheduling.postgres_scheduling_repository import (
    BookingConflictError,
    PostgresSchedulingRepository,
)


def public_resource_payload(resource: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": resource["id"],
        "branch_code": resource["branch_code"],
        "name": resource["name"],
        "resource_type": resource["resource_type"],
        "description": resource.get("description"),
        "capacity": resource.get("capacity"),
        "requires_approval": True,
    }


class CreatePublicSchedulingBookingUseCase:
    """Solicitação anônima via public-hub — sempre pendente de aprovação."""

    def __init__(self, repository: PostgresSchedulingRepository) -> None:
        self._repository = repository
        self._expire = ExpirePendingSchedulingBookingsUseCase(repository)

    def execute(
        self,
        *,
        public_token: str,
        requester_name: str,
        requester_email: str,
        requester_phone: str | None,
        title: str,
        notes: str | None,
        start_at: datetime,
        end_at: datetime,
    ) -> dict[str, Any]:
        resource = self._repository.get_resource_by_public_token(public_token)
        if not resource:
            raise PluginsRepositoryError("Link de agendamento inválido ou desativado.")

        branch_code = str(resource["branch_code"])
        resource_id = str(resource["id"])
        self._expire.execute(branch_code=branch_code)

        if end_at <= start_at:
            raise PluginsRepositoryError(
                "O horário de término deve ser posterior ao início."
            )

        now = datetime.now(timezone.utc)
        start_utc = start_at if start_at.tzinfo else start_at.replace(tzinfo=timezone.utc)
        if start_utc <= now:
            raise PluginsRepositoryError(
                "Não é possível solicitar um horário que já iniciou."
            )

        name = requester_name.strip()
        email = requester_email.strip().lower()
        phone = (requester_phone or "").strip() or None
        if len(name) < 2:
            raise PluginsRepositoryError("Informe o nome do solicitante.")
        if "@" not in email or len(email) < 5:
            raise PluginsRepositoryError("Informe um e-mail válido.")

        data = self._repository.create_booking(
            resource_id=resource_id,
            branch_code=branch_code,
            title=title.strip(),
            notes=notes,
            start_at=start_at,
            end_at=end_at,
            booked_by_user_id=f"public:{resource_id}",
            booked_by_name=name,
            status="pending",
            expires_at=start_at,
            requester_email=email,
            requester_phone=phone,
        )
        notify_booking_approval_requested(booking=data)
        return data


__all__ = [
    "BookingConflictError",
    "CreatePublicSchedulingBookingUseCase",
    "PluginsRepositoryError",
    "public_resource_payload",
]

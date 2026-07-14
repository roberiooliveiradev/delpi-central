from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from delpi_auth.authz_core import has_permission
from delpi_auth.authorization import require_any_permission
from delpi_auth.request_context import get_current_user

from app.application.security.api_delpi_permissions import (
    SCHEDULING_APPROVE_PERMISSIONS,
    SCHEDULING_BRANCH_APPROVE_PERMS,
    SCHEDULING_BRANCH_MANAGE_PERMS,
    SCHEDULING_BRANCH_VIEW_PERMS,
    SCHEDULING_MANAGE_PERMISSIONS,
    SCHEDULING_READ_PERMISSIONS,
)
from app.application.use_cases.scheduling.create_scheduling_booking_use_case import (
    CreateSchedulingBookingUseCase,
)
from app.application.use_cases.scheduling.decide_scheduling_booking_use_case import (
    DecideSchedulingBookingUseCase,
)
from app.application.use_cases.scheduling.expire_pending_scheduling_bookings_use_case import (
    ExpirePendingSchedulingBookingsUseCase,
)
from app.composition.scheduling_composer import build_scheduling_repository
from app.core.responses import error_response
from app.infrastructure.persistence.plugins.plugin_base_repository import PluginsRepositoryError
from app.infrastructure.persistence.plugins.repositories.scheduling.postgres_scheduling_repository import (
    BookingConflictError,
)
from app.interface.http.route_response_helpers import api_delpi_success
from app.shared.utils.person_name import format_person_name
from app.utils.logger import log_error

router = APIRouter(tags=["Agendamento"])


class CreateResourceBody(BaseModel):
    branch_code: str = Field(..., pattern="^(ES|SC)$")
    name: str = Field(..., min_length=2, max_length=200)
    resource_type: str = Field(
        ...,
        pattern="^(meeting_room|training_room|company_car|other)$",
    )
    description: str | None = Field(default=None, max_length=2000)
    capacity: int | None = Field(default=None, ge=1, le=9999)
    metadata: dict[str, Any] | None = None
    requires_approval: bool = False


class UpdateResourceBody(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    resource_type: str | None = Field(
        default=None,
        pattern="^(meeting_room|training_room|company_car|other)$",
    )
    description: str | None = Field(default=None, max_length=2000)
    capacity: int | None = Field(default=None, ge=1, le=9999)
    metadata: dict[str, Any] | None = None
    active: bool | None = None
    requires_approval: bool | None = None


class RecurrenceBody(BaseModel):
    frequency: str = Field(..., pattern="^(weekly|monthly)$")
    until: datetime
    interval: int = Field(default=1, ge=1, le=4)


class CreateBookingBody(BaseModel):
    branch_code: str = Field(..., pattern="^(ES|SC)$")
    resource_id: str
    title: str = Field(..., min_length=2, max_length=200)
    notes: str | None = Field(default=None, max_length=2000)
    start_at: datetime
    end_at: datetime
    recurrence: RecurrenceBody | None = None


class RejectBookingBody(BaseModel):
    reason: str = Field(..., min_length=3, max_length=2000)


def _current_user_id() -> str:
    user = get_current_user()
    if user is None:
        return "unknown"
    return str(getattr(user, "id", "unknown"))


def _current_user_name() -> str:
    user = get_current_user()
    if user is None:
        return "Usuário"
    return format_person_name(str(getattr(user, "name", "Usuário")))


def _is_superadmin() -> bool:
    user = get_current_user()
    return bool(user and getattr(user, "is_superadmin", False))


def _branch_view_allowed(branch: str) -> bool:
    if _is_superadmin():
        return True
    user = get_current_user()
    if user is None:
        return False
    view_perm = SCHEDULING_BRANCH_VIEW_PERMS[branch]
    manage_perm = SCHEDULING_BRANCH_MANAGE_PERMS[branch]
    approve_perm = SCHEDULING_BRANCH_APPROVE_PERMS[branch]
    return (
        has_permission(user, view_perm)
        or has_permission(user, manage_perm)
        or has_permission(user, approve_perm)
    )


def _branch_manage_allowed(branch: str) -> bool:
    if _is_superadmin():
        return True
    user = get_current_user()
    if user is None:
        return False
    return has_permission(user, SCHEDULING_BRANCH_MANAGE_PERMS[branch])


def _branch_approve_allowed(branch: str) -> bool:
    if _is_superadmin():
        return True
    user = get_current_user()
    if user is None:
        return False
    return has_permission(user, SCHEDULING_BRANCH_APPROVE_PERMS[branch])


def _branch_access_error(
    branch: str,
    *,
    require_manage: bool = False,
    require_approve: bool = False,
):
    if require_approve:
        allowed = _branch_approve_allowed(branch)
        message = "Sem permissão para aprovar agendamentos nesta filial."
    elif require_manage:
        allowed = _branch_manage_allowed(branch)
        message = "Sem permissão para gerenciar recursos nesta filial."
    else:
        allowed = _branch_view_allowed(branch)
        message = "Sem permissão para acessar esta filial."
    if allowed:
        return None
    return error_response(message, status_code=403)


def _parse_iso_datetime(value: str) -> datetime | None:
    try:
        normalized = value.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


@router.get("/resources")
@require_any_permission(SCHEDULING_READ_PERMISSIONS)
def list_resources(
    branch: str = Query(..., pattern="^(ES|SC)$"),
    active: bool = Query(True),
):
    branch_error = _branch_access_error(branch)
    if branch_error:
        return branch_error

    if not active and not _branch_manage_allowed(branch):
        return error_response(
            "Sem permissão para listar recursos inativos.",
            status_code=403,
        )

    try:
        repo = build_scheduling_repository()
        data = repo.list_resources(branch, active_only=active)
        return api_delpi_success(data, operation_id="list_scheduling_resources")
    except Exception as exc:
        log_error(f"Erro ao listar recursos de agendamento: {exc}")
        return error_response("Erro interno ao listar recursos.", status_code=500)


@router.post("/resources")
@require_any_permission(SCHEDULING_MANAGE_PERMISSIONS)
def create_resource(body: CreateResourceBody):
    branch_error = _branch_access_error(body.branch_code, require_manage=True)
    if branch_error:
        return branch_error

    try:
        repo = build_scheduling_repository()
        data = repo.create_resource(
            branch_code=body.branch_code,
            name=body.name,
            resource_type=body.resource_type,
            description=body.description,
            capacity=body.capacity,
            metadata=body.metadata,
            created_by_user_id=_current_user_id(),
            requires_approval=body.requires_approval,
        )
        return api_delpi_success(
            data,
            operation_id="create_scheduling_resource",
            message="Recurso cadastrado com sucesso.",
        )
    except PluginsRepositoryError as exc:
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro ao criar recurso de agendamento: {exc}")
        return error_response("Erro interno ao cadastrar recurso.", status_code=500)


@router.patch("/resources/{resource_id}")
@require_any_permission(SCHEDULING_MANAGE_PERMISSIONS)
def update_resource(resource_id: str, body: UpdateResourceBody):
    try:
        repo = build_scheduling_repository()
        existing = repo.get_resource(resource_id)
        if not existing:
            return error_response("Recurso não encontrado.", status_code=404)

        branch_error = _branch_access_error(str(existing["branch_code"]), require_manage=True)
        if branch_error:
            return branch_error

        data = repo.update_resource(
            resource_id,
            name=body.name,
            resource_type=body.resource_type,
            description=body.description,
            capacity=body.capacity,
            metadata=body.metadata,
            active=body.active,
            requires_approval=body.requires_approval,
        )
        return api_delpi_success(
            data,
            operation_id="update_scheduling_resource",
            message="Recurso atualizado com sucesso.",
        )
    except PluginsRepositoryError as exc:
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro ao atualizar recurso de agendamento: {exc}")
        return error_response("Erro interno ao atualizar recurso.", status_code=500)


@router.get("/bookings")
@require_any_permission(SCHEDULING_READ_PERMISSIONS)
def list_bookings(
    branch: str = Query(..., pattern="^(ES|SC)$"),
    from_at: str = Query(..., alias="from"),
    to_at: str = Query(..., alias="to"),
    resource_id: str | None = Query(default=None),
):
    branch_error = _branch_access_error(branch)
    if branch_error:
        return branch_error

    start = _parse_iso_datetime(from_at)
    end = _parse_iso_datetime(to_at)
    if not start or not end:
        return error_response("Parâmetros from/to inválidos.", status_code=400)
    if end <= start:
        return error_response("O fim deve ser posterior ao início.", status_code=400)

    try:
        repo = build_scheduling_repository()
        ExpirePendingSchedulingBookingsUseCase(repo).execute(branch_code=branch)
        data = repo.list_bookings(
            branch,
            from_at=start,
            to_at=end,
            resource_id=resource_id,
        )
        return api_delpi_success(data, operation_id="list_scheduling_bookings")
    except Exception as exc:
        log_error(f"Erro ao listar reservas: {exc}")
        return error_response("Erro interno ao listar reservas.", status_code=500)


@router.get("/bookings/pending")
@require_any_permission(SCHEDULING_READ_PERMISSIONS)
def list_pending_bookings(
    branch: str = Query(..., pattern="^(ES|SC)$"),
    mine: bool = Query(False),
):
    branch_error = _branch_access_error(branch)
    if branch_error:
        return branch_error

    if not mine and not _branch_approve_allowed(branch):
        return error_response(
            "Sem permissão para listar aprovações pendentes desta filial.",
            status_code=403,
        )

    try:
        repo = build_scheduling_repository()
        ExpirePendingSchedulingBookingsUseCase(repo).execute(branch_code=branch)
        booked_by = _current_user_id() if mine else None
        data = repo.list_pending_bookings(branch, booked_by_user_id=booked_by)
        return api_delpi_success(data, operation_id="list_pending_scheduling_bookings")
    except Exception as exc:
        log_error(f"Erro ao listar reservas pendentes: {exc}")
        return error_response("Erro interno ao listar pendências.", status_code=500)


@router.post("/bookings")
@require_any_permission(SCHEDULING_READ_PERMISSIONS)
def create_booking(body: CreateBookingBody):
    branch_error = _branch_access_error(body.branch_code)
    if branch_error:
        return branch_error

    if body.end_at <= body.start_at:
        return error_response("O horário de término deve ser posterior ao início.", status_code=400)

    try:
        repo = build_scheduling_repository()
        recurrence = None
        if body.recurrence:
            recurrence = {
                "frequency": body.recurrence.frequency,
                "until": body.recurrence.until,
                "interval": body.recurrence.interval,
            }
        data, operation_id, message = CreateSchedulingBookingUseCase(repo).execute(
            branch_code=body.branch_code,
            resource_id=body.resource_id,
            title=body.title,
            notes=body.notes,
            start_at=body.start_at,
            end_at=body.end_at,
            booked_by_user_id=_current_user_id(),
            booked_by_name=_current_user_name(),
            recurrence=recurrence,
        )
        return api_delpi_success(data, operation_id=operation_id, message=message)
    except BookingConflictError as exc:
        return error_response(str(exc), status_code=409)
    except PluginsRepositoryError as exc:
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro ao criar reserva: {exc}")
        return error_response("Erro interno ao criar reserva.", status_code=500)


@router.post("/bookings/{booking_id}/approve")
@require_any_permission(SCHEDULING_APPROVE_PERMISSIONS)
def approve_booking(booking_id: str):
    try:
        repo = build_scheduling_repository()
        booking = repo.get_booking(booking_id)
        if not booking:
            return error_response("Reserva não encontrada.", status_code=404)

        branch_error = _branch_access_error(
            str(booking["branch_code"]),
            require_approve=True,
        )
        if branch_error:
            return branch_error

        data = DecideSchedulingBookingUseCase(repo).execute(
            booking_id=booking_id,
            action="approve",
            actor_user_id=_current_user_id(),
            actor_name=_current_user_name(),
            is_superadmin=_is_superadmin(),
        )
        return api_delpi_success(
            data,
            operation_id="approve_scheduling_booking",
            message="Reserva confirmada com sucesso.",
        )
    except PluginsRepositoryError as exc:
        status = 403 if "própria solicitação" in str(exc) else 400
        return error_response(str(exc), status_code=status)
    except Exception as exc:
        log_error(f"Erro ao aprovar reserva: {exc}")
        return error_response("Erro interno ao aprovar reserva.", status_code=500)


@router.post("/bookings/{booking_id}/reject")
@require_any_permission(SCHEDULING_APPROVE_PERMISSIONS)
def reject_booking(booking_id: str, body: RejectBookingBody):
    try:
        repo = build_scheduling_repository()
        booking = repo.get_booking(booking_id)
        if not booking:
            return error_response("Reserva não encontrada.", status_code=404)

        branch_error = _branch_access_error(
            str(booking["branch_code"]),
            require_approve=True,
        )
        if branch_error:
            return branch_error

        data = DecideSchedulingBookingUseCase(repo).execute(
            booking_id=booking_id,
            action="reject",
            actor_user_id=_current_user_id(),
            actor_name=_current_user_name(),
            reason=body.reason,
            is_superadmin=_is_superadmin(),
        )
        return api_delpi_success(
            data,
            operation_id="reject_scheduling_booking",
            message="Reserva rejeitada.",
        )
    except PluginsRepositoryError as exc:
        status = 403 if "própria solicitação" in str(exc) else 400
        return error_response(str(exc), status_code=status)
    except Exception as exc:
        log_error(f"Erro ao rejeitar reserva: {exc}")
        return error_response("Erro interno ao rejeitar reserva.", status_code=500)


@router.patch("/bookings/{booking_id}/cancel")
@require_any_permission(SCHEDULING_READ_PERMISSIONS)
def cancel_booking(
    booking_id: str,
    scope: str = Query(default="occurrence", pattern="^(occurrence|future|all)$"),
):
    try:
        repo = build_scheduling_repository()
        booking = repo.get_booking(booking_id)
        if not booking:
            return error_response("Reserva não encontrada.", status_code=404)

        branch = str(booking["branch_code"])
        branch_error = _branch_access_error(branch)
        if branch_error:
            return branch_error

        user_id = _current_user_id()
        is_owner = str(booking["booked_by_user_id"]) == user_id
        can_manage = _branch_manage_allowed(branch)
        can_approve = _branch_approve_allowed(branch)
        if not is_owner and not can_manage and not can_approve and not _is_superadmin():
            return error_response("Sem permissão para cancelar esta reserva.", status_code=403)

        if booking.get("status") in {"cancelled", "rejected", "expired"}:
            return error_response("Reserva já encerrada.", status_code=400)

        if scope in ("future", "all") and not booking.get("recurrence_series_id"):
            return error_response(
                "Esta reserva não faz parte de uma série recorrente.",
                status_code=400,
            )

        data = repo.cancel_booking(booking_id, scope=scope)  # type: ignore[arg-type]
        if not data:
            return error_response("Não foi possível cancelar a reserva.", status_code=400)

        cancelled_count = int(data.get("cancelled_count", 1))
        if cancelled_count > 1:
            message = f"{cancelled_count} reservas da série canceladas com sucesso."
        else:
            message = "Reserva cancelada com sucesso."

        return api_delpi_success(
            data,
            operation_id="cancel_scheduling_booking",
            message=message,
        )
    except PluginsRepositoryError as exc:
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro ao cancelar reserva: {exc}")
        return error_response("Erro interno ao cancelar reserva.", status_code=500)

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from delpi_auth.authz_core import has_permission
from delpi_auth.authorization import require_any_permission
from delpi_auth.request_context import get_current_user

from app.composition.scheduling_composer import build_scheduling_repository
from app.core.responses import error_response, success_response
from app.infrastructure.persistence.plugins.plugin_base_repository import PluginsRepositoryError
from app.infrastructure.persistence.plugins.repositories.scheduling.postgres_scheduling_repository import (
    BookingConflictError,
)
from app.shared.utils.person_name import format_person_name
from app.utils.logger import log_error

router = APIRouter(tags=["Agendamento"])

READ_PERMISSIONS = [
    "api-delpi.access",
    "central-agendamento.view.filial-es",
    "central-agendamento.view.filial-sc",
    "central-agendamento.manage.filial-es",
    "central-agendamento.manage.filial-sc",
]

MANAGE_PERMISSIONS = [
    "api-delpi.access",
    "central-agendamento.manage.filial-es",
    "central-agendamento.manage.filial-sc",
]

BRANCH_VIEW_PERMS = {
    "ES": "central-agendamento.view.filial-es",
    "SC": "central-agendamento.view.filial-sc",
}

BRANCH_MANAGE_PERMS = {
    "ES": "central-agendamento.manage.filial-es",
    "SC": "central-agendamento.manage.filial-sc",
}


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


class CreateBookingBody(BaseModel):
    branch_code: str = Field(..., pattern="^(ES|SC)$")
    resource_id: str
    title: str = Field(..., min_length=2, max_length=200)
    notes: str | None = Field(default=None, max_length=2000)
    start_at: datetime
    end_at: datetime


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
    view_perm = BRANCH_VIEW_PERMS[branch]
    manage_perm = BRANCH_MANAGE_PERMS[branch]
    return has_permission(user, view_perm) or has_permission(user, manage_perm)


def _branch_manage_allowed(branch: str) -> bool:
    if _is_superadmin():
        return True
    user = get_current_user()
    if user is None:
        return False
    return has_permission(user, BRANCH_MANAGE_PERMS[branch])


def _branch_access_error(branch: str, *, require_manage: bool = False):
    allowed = _branch_manage_allowed(branch) if require_manage else _branch_view_allowed(branch)
    if allowed:
        return None
    message = (
        "Sem permissão para gerenciar recursos nesta filial."
        if require_manage
        else "Sem permissão para acessar esta filial."
    )
    return error_response(message, status_code=403)


def _parse_iso_datetime(value: str) -> datetime | None:
    try:
        normalized = value.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


@router.get("/resources")
@require_any_permission(READ_PERMISSIONS)
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
        return success_response(data=data)
    except Exception as exc:
        log_error(f"Erro ao listar recursos de agendamento: {exc}")
        return error_response("Erro interno ao listar recursos.", status_code=500)


@router.post("/resources")
@require_any_permission(MANAGE_PERMISSIONS)
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
        )
        return success_response(data=data, message="Recurso cadastrado com sucesso.")
    except PluginsRepositoryError as exc:
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro ao criar recurso de agendamento: {exc}")
        return error_response("Erro interno ao cadastrar recurso.", status_code=500)


@router.patch("/resources/{resource_id}")
@require_any_permission(MANAGE_PERMISSIONS)
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
        )
        return success_response(data=data, message="Recurso atualizado com sucesso.")
    except PluginsRepositoryError as exc:
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro ao atualizar recurso de agendamento: {exc}")
        return error_response("Erro interno ao atualizar recurso.", status_code=500)


@router.get("/bookings")
@require_any_permission(READ_PERMISSIONS)
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
        data = repo.list_bookings(
            branch,
            from_at=start,
            to_at=end,
            resource_id=resource_id,
        )
        return success_response(data=data)
    except Exception as exc:
        log_error(f"Erro ao listar reservas: {exc}")
        return error_response("Erro interno ao listar reservas.", status_code=500)


@router.post("/bookings")
@require_any_permission(READ_PERMISSIONS)
def create_booking(body: CreateBookingBody):
    branch_error = _branch_access_error(body.branch_code)
    if branch_error:
        return branch_error

    if body.end_at <= body.start_at:
        return error_response("O horário de término deve ser posterior ao início.", status_code=400)

    try:
        repo = build_scheduling_repository()
        resource = repo.get_resource(body.resource_id)
        if not resource:
            return error_response("Recurso não encontrado.", status_code=404)
        if str(resource["branch_code"]) != body.branch_code:
            return error_response("Recurso não pertence à filial informada.", status_code=400)
        if not resource.get("active", True):
            return error_response("Recurso inativo.", status_code=400)

        data = repo.create_booking(
            resource_id=body.resource_id,
            branch_code=body.branch_code,
            title=body.title,
            notes=body.notes,
            start_at=body.start_at,
            end_at=body.end_at,
            booked_by_user_id=_current_user_id(),
            booked_by_name=_current_user_name(),
        )
        return success_response(data=data, message="Reserva confirmada com sucesso.")
    except BookingConflictError as exc:
        return error_response(str(exc), status_code=409)
    except PluginsRepositoryError as exc:
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro ao criar reserva: {exc}")
        return error_response("Erro interno ao criar reserva.", status_code=500)


@router.patch("/bookings/{booking_id}/cancel")
@require_any_permission(READ_PERMISSIONS)
def cancel_booking(booking_id: str):
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
        if not is_owner and not can_manage and not _is_superadmin():
            return error_response("Sem permissão para cancelar esta reserva.", status_code=403)

        if booking.get("status") == "cancelled":
            return error_response("Reserva já cancelada.", status_code=400)

        data = repo.cancel_booking(booking_id)
        if not data:
            return error_response("Não foi possível cancelar a reserva.", status_code=400)
        data["resource_name"] = booking.get("resource_name")
        data["resource_type"] = booking.get("resource_type")
        return success_response(data=data, message="Reserva cancelada com sucesso.")
    except Exception as exc:
        log_error(f"Erro ao cancelar reserva: {exc}")
        return error_response("Erro interno ao cancelar reserva.", status_code=500)

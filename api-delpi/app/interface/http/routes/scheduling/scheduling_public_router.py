"""Rotas públicas (sem JWT) — agendamento via public-hub por token do recurso."""

from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Body, Query
from pydantic import BaseModel, Field, field_validator

from app.application.use_cases.scheduling.create_public_scheduling_booking_use_case import (
    CreatePublicSchedulingBookingUseCase,
    public_resource_payload,
)
from app.application.use_cases.scheduling.expire_pending_scheduling_bookings_use_case import (
    ExpirePendingSchedulingBookingsUseCase,
)
from app.composition.scheduling_composer import build_scheduling_repository
from app.core.responses import error_response
from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginsRepositoryError,
)
from app.infrastructure.persistence.plugins.repositories.scheduling.postgres_scheduling_repository import (
    BookingConflictError,
)
from app.interface.http.route_response_helpers import api_delpi_success
from app.utils.logger import log_error

router = APIRouter(prefix="/public/scheduling", tags=["Agendamento — público"])

_MAX_AVAILABILITY_DAYS = 62


class PublicBookingBody(BaseModel):
    requester_name: str = Field(..., min_length=2, max_length=200)
    requester_email: str = Field(..., min_length=5, max_length=320)
    requester_phone: str | None = Field(default=None, max_length=40)
    title: str = Field(..., min_length=2, max_length=200)
    notes: str | None = Field(default=None, max_length=2000)
    start_at: datetime
    end_at: datetime
    website: str | None = Field(default=None, max_length=200)

    @field_validator("requester_name", "title", mode="before")
    @classmethod
    def strip_required(cls, value: object) -> str:
        if not isinstance(value, str):
            raise ValueError("valor deve ser string")
        return value.strip()

    @field_validator("requester_email", mode="before")
    @classmethod
    def normalize_email(cls, value: object) -> str:
        if not isinstance(value, str):
            raise ValueError("e-mail deve ser string")
        return value.strip().lower()


def _parse_iso_datetime(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _iso(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


@router.get(
    "/resources/{public_token}",
    operation_id="get_public_scheduling_resource",
)
def get_public_scheduling_resource(public_token: str):
    try:
        repo = build_scheduling_repository()
        resource = repo.get_resource_by_public_token(public_token)
        if not resource:
            return error_response(
                "Link de agendamento inválido ou desativado.",
                status_code=404,
            )
        return api_delpi_success(
            public_resource_payload(resource),
            operation_id="get_public_scheduling_resource",
        )
    except Exception as exc:
        log_error(f"Erro ao carregar recurso público de agendamento: {exc}")
        return error_response("Erro interno ao carregar recurso.", status_code=500)


@router.get(
    "/resources/{public_token}/availability",
    operation_id="get_public_scheduling_availability",
)
def get_public_scheduling_availability(
    public_token: str,
    from_at: str = Query(..., alias="from"),
    to_at: str = Query(..., alias="to"),
):
    start = _parse_iso_datetime(from_at)
    end = _parse_iso_datetime(to_at)
    if not start or not end:
        return error_response("Parâmetros from/to inválidos.", status_code=400)
    if end <= start:
        return error_response("O fim deve ser posterior ao início.", status_code=400)
    if end - start > timedelta(days=_MAX_AVAILABILITY_DAYS):
        return error_response(
            f"Intervalo máximo de disponibilidade: {_MAX_AVAILABILITY_DAYS} dias.",
            status_code=400,
        )

    try:
        repo = build_scheduling_repository()
        resource = repo.get_resource_by_public_token(public_token)
        if not resource:
            return error_response(
                "Link de agendamento inválido ou desativado.",
                status_code=404,
            )
        ExpirePendingSchedulingBookingsUseCase(repo).execute(
            branch_code=str(resource["branch_code"]),
        )
        busy = repo.list_busy_slots(
            str(resource["id"]),
            from_at=start,
            to_at=end,
        )
        payload = {
            "resource_id": resource["id"],
            "busy": [
                {"start_at": _iso(row.get("start_at")), "end_at": _iso(row.get("end_at"))}
                for row in busy
            ],
        }
        return api_delpi_success(
            payload,
            operation_id="get_public_scheduling_availability",
        )
    except Exception as exc:
        log_error(f"Erro ao listar disponibilidade pública: {exc}")
        return error_response("Erro interno ao listar disponibilidade.", status_code=500)


@router.post(
    "/resources/{public_token}/bookings",
    operation_id="create_public_scheduling_booking",
)
def create_public_scheduling_booking(
    public_token: str,
    body: PublicBookingBody = Body(...),
):
    if (body.website or "").strip():
        return api_delpi_success(
            {
                "id": None,
                "status": "pending",
                "accepted": True,
            },
            operation_id="create_public_scheduling_booking",
            message="Solicitação enviada. Aguarde a aprovação.",
        )

    try:
        repo = build_scheduling_repository()
        data = CreatePublicSchedulingBookingUseCase(repo).execute(
            public_token=public_token,
            requester_name=body.requester_name,
            requester_email=body.requester_email,
            requester_phone=body.requester_phone,
            title=body.title,
            notes=body.notes,
            start_at=body.start_at,
            end_at=body.end_at,
        )
        return api_delpi_success(
            {
                "id": data.get("id"),
                "status": data.get("status"),
                "start_at": _iso(data.get("start_at")),
                "end_at": _iso(data.get("end_at")),
                "resource_name": data.get("resource_name"),
                "accepted": True,
            },
            operation_id="create_public_scheduling_booking",
            message="Solicitação enviada. Aguarde a aprovação.",
        )
    except BookingConflictError as exc:
        return error_response(str(exc), status_code=409)
    except PluginsRepositoryError as exc:
        message = str(exc)
        status = 404 if "inválido" in message.lower() or "desativado" in message.lower() else 400
        return error_response(message, status_code=status)
    except Exception as exc:
        log_error(f"Erro ao criar reserva pública: {exc}")
        return error_response("Erro interno ao solicitar agendamento.", status_code=500)
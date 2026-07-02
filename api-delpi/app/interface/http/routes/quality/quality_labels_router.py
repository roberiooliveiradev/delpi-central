from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Body, Query, Response
from pydantic import BaseModel, Field, field_validator

from delpi_auth.authorization import require_any_permission
from delpi_auth.request_context import get_current_user

from app.application.security.api_delpi_permissions import (
    QUALITY_LABELS_READ_PERMISSIONS,
    QUALITY_LABELS_WRITE_PERMISSIONS,
)
from app.application.use_cases.quality_labels.quality_labels_service import (
    ProductionOrderNotFoundError,
    QualityLabelsError,
)
from app.composition.quality_labels_composer import build_quality_labels_service
from app.core.responses import error_response, not_found_response
from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginsRepositoryError,
)
from app.interface.http.route_response_helpers import api_delpi_success
from app.shared.utils.person_name import format_person_name
from app.utils.logger import log_error

router = APIRouter(prefix="/labels", tags=["Quality Labels"])

_ALLOWED_RESULTS = {"approved", "rejected", "conditional"}


class CreateLabelBody(BaseModel):
    productionOrder: str = Field(min_length=1)
    branch: Optional[str] = None
    result: str = Field(default="approved")
    notes: Optional[str] = None

    @field_validator("productionOrder", "branch", "notes", mode="before")
    @classmethod
    def _strip(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("result", mode="before")
    @classmethod
    def _validate_result(cls, value: object) -> str:
        normalized = str(value or "approved").strip().lower()
        if normalized not in _ALLOWED_RESULTS:
            raise ValueError("result deve ser approved, rejected ou conditional.")
        return normalized


class SetActiveBody(BaseModel):
    isActive: bool


def _current_user_id() -> str:
    user = get_current_user()
    user_id = getattr(user, "id", None) if user else None
    return str(user_id) if user_id else "desconhecido"


def _current_user_name() -> str:
    user = get_current_user()
    if user is None:
        return "Inspetor"
    name = getattr(user, "name", None)
    if isinstance(name, str) and name.strip():
        return format_person_name(name)
    email = getattr(user, "email", None)
    if isinstance(email, str) and email.strip():
        return email.strip()
    return "Inspetor"


@router.get("/lookup-op/{production_order}")
@require_any_permission(QUALITY_LABELS_WRITE_PERMISSIONS)
def lookup_op(production_order: str, branch: Optional[str] = None):
    try:
        service = build_quality_labels_service()
        data = service.lookup_op(production_order=production_order, branch=branch)
        return api_delpi_success(
            data,
            operation_id="lookup_quality_label_op",
            message="OP localizada com sucesso.",
        )
    except ProductionOrderNotFoundError as exc:
        return not_found_response(str(exc))
    except QualityLabelsError as exc:
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro ao consultar OP para etiqueta de qualidade: {exc}")
        return error_response("Erro interno ao consultar a OP.", status_code=500)


@router.post("")
@require_any_permission(QUALITY_LABELS_WRITE_PERMISSIONS)
def create_label(body: Annotated[CreateLabelBody, Body(...)]):
    try:
        service = build_quality_labels_service()
        data = service.create_label(
            production_order=body.productionOrder,
            branch=body.branch,
            notes=body.notes,
            result=body.result,
            inspector_user_id=_current_user_id(),
            inspector_name=_current_user_name(),
        )
        return api_delpi_success(
            data,
            operation_id="create_quality_label",
            message="Etiqueta de qualidade registrada com sucesso.",
        )
    except ProductionOrderNotFoundError as exc:
        return not_found_response(str(exc))
    except QualityLabelsError as exc:
        return error_response(str(exc), status_code=400)
    except (PluginsRepositoryError, Exception) as exc:
        log_error(f"Erro ao registrar etiqueta de qualidade: {exc}")
        return error_response("Erro interno ao registrar a etiqueta.", status_code=500)


@router.get("")
@require_any_permission(QUALITY_LABELS_READ_PERMISSIONS)
def list_labels(
    search: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    try:
        service = build_quality_labels_service()
        data = service.list_labels(search=search, limit=limit, offset=offset)
        return api_delpi_success(
            data,
            operation_id="list_quality_labels",
            message="Etiquetas de qualidade recuperadas com sucesso.",
        )
    except Exception as exc:
        log_error(f"Erro ao listar etiquetas de qualidade: {exc}")
        return error_response("Erro interno ao listar as etiquetas.", status_code=500)


@router.get("/{label_id}")
@require_any_permission(QUALITY_LABELS_READ_PERMISSIONS)
def get_label(label_id: str):
    try:
        service = build_quality_labels_service()
        data = service.get_label(label_id=label_id)
        if data is None:
            return not_found_response("Etiqueta não encontrada.")
        return api_delpi_success(
            data,
            operation_id="get_quality_label",
            message="Etiqueta recuperada com sucesso.",
        )
    except Exception as exc:
        log_error(f"Erro ao buscar etiqueta de qualidade: {exc}")
        return error_response("Erro interno ao buscar a etiqueta.", status_code=500)


@router.get("/{label_id}/qr")
@require_any_permission(QUALITY_LABELS_READ_PERMISSIONS)
def get_label_qr(label_id: str):
    try:
        service = build_quality_labels_service()
        png = service.read_qr(label_id=label_id)
        if png is None:
            return not_found_response("QR da etiqueta não encontrado.")
        return Response(content=png, media_type="image/png")
    except Exception as exc:
        log_error(f"Erro ao ler QR da etiqueta de qualidade: {exc}")
        return error_response("Erro interno ao ler o QR.", status_code=500)


@router.patch("/{label_id}/active")
@require_any_permission(QUALITY_LABELS_WRITE_PERMISSIONS)
def set_label_active(label_id: str, body: Annotated[SetActiveBody, Body(...)]):
    try:
        service = build_quality_labels_service()
        data = service.set_active(label_id=label_id, is_active=body.isActive)
        if data is None:
            return not_found_response("Etiqueta não encontrada.")
        return api_delpi_success(
            data,
            operation_id="set_quality_label_active",
            message="Situação da etiqueta atualizada com sucesso.",
        )
    except Exception as exc:
        log_error(f"Erro ao atualizar situação da etiqueta: {exc}")
        return error_response("Erro interno ao atualizar a etiqueta.", status_code=500)

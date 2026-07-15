"""Rotas administrativas — Guias e Procedimentos."""

from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Body, Query
from pydantic import BaseModel, Field

from delpi_auth.authorization import require_any_permission
from delpi_auth.request_context import get_current_user

from app.application.security.api_delpi_permissions import (
    GUIAS_PROCEDIMENTOS_WRITE_PERMISSIONS,
)
from app.application.use_cases.guias_procedimentos.admin_guias_use_cases import (
    ActorContext,
)
from app.composition.guias_procedimentos_composer import (
    build_archive_procedure_use_case,
    build_create_department_use_case,
    build_create_procedure_use_case,
    build_get_admin_department_use_case,
    build_get_admin_procedure_use_case,
    build_list_admin_departments_use_case,
    build_list_admin_procedures_use_case,
    build_publish_procedure_use_case,
    build_restore_procedure_use_case,
    build_unpublish_procedure_use_case,
    build_update_department_use_case,
    build_update_procedure_use_case,
)
from app.core.responses import error_response, not_found_response
from app.domain.services.guias_procedimentos.exceptions import (
    GuiasConflictError,
    GuiasNotFoundError,
    GuiasValidationError,
)
from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginsRepositoryError,
)
from app.interface.http.route_response_helpers import api_delpi_success
from app.shared.utils.person_name import format_person_name
from app.utils.logger import log_error

router = APIRouter(tags=["Guias e Procedimentos — Admin"])


class DepartmentBody(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    slug: str = Field(..., min_length=2, max_length=120)
    description: str = Field(default="", max_length=4000)
    icon: str = Field(default="book-open", max_length=64)
    active: bool = True
    order_index: int = Field(default=0, ge=0)


class ProcedureBody(BaseModel):
    department_id: UUID
    title: str = Field(..., min_length=1, max_length=500)
    slug: str = Field(..., min_length=2, max_length=160)
    summary: str = Field(default="", max_length=4000)
    content_html: str = Field(default="")
    reading_time_minutes: int | None = Field(default=None, ge=1, le=480)
    order_index: int = Field(default=0, ge=0)
    status: str | None = None


def _actor() -> ActorContext:
    user = get_current_user()
    if user is None:
        return ActorContext(None, None)
    user_id = getattr(user, "id", None)
    name = getattr(user, "name", None)
    if isinstance(name, str) and name.strip():
        display = format_person_name(name)
    else:
        email = getattr(user, "email", None)
        display = email.strip() if isinstance(email, str) and email.strip() else None
    return ActorContext(str(user_id) if user_id else None, display)


def _handle_domain(exc: Exception):
    if isinstance(exc, GuiasNotFoundError):
        return not_found_response(str(exc))
    if isinstance(exc, GuiasConflictError):
        return error_response(str(exc), status_code=409, code="CONFLICT", recoverable=False)
    if isinstance(exc, GuiasValidationError):
        return error_response(str(exc), status_code=422, code="VALIDATION_ERROR")
    if isinstance(exc, PluginsRepositoryError):
        log_error(f"Erro de persistência guias admin: {exc}")
        return error_response("Erro interno de persistência.", status_code=500)
    log_error(f"Erro inesperado guias admin: {exc}")
    return error_response("Erro interno.", status_code=500)


# --- departments ---


@router.get("/admin/departments")
@require_any_permission(GUIAS_PROCEDIMENTOS_WRITE_PERMISSIONS)
def list_admin_departments():
    try:
        data = build_list_admin_departments_use_case().execute()
        return api_delpi_success(
            data,
            operation_id="list_guias_procedimentos_admin_departments",
            message="Departamentos (admin) recuperados com sucesso.",
        )
    except Exception as exc:
        return _handle_domain(exc)


@router.get("/admin/departments/{department_id}")
@require_any_permission(GUIAS_PROCEDIMENTOS_WRITE_PERMISSIONS)
def get_admin_department(department_id: UUID):
    try:
        data = build_get_admin_department_use_case().execute(str(department_id))
        return api_delpi_success(
            data,
            operation_id="get_guias_procedimentos_admin_department",
            message="Departamento recuperado com sucesso.",
        )
    except Exception as exc:
        return _handle_domain(exc)


@router.post("/admin/departments")
@require_any_permission(GUIAS_PROCEDIMENTOS_WRITE_PERMISSIONS)
def create_admin_department(body: Annotated[DepartmentBody, Body(...)]):
    try:
        data = build_create_department_use_case().execute(
            body.model_dump(),
            _actor(),
        )
        return api_delpi_success(
            data,
            operation_id="create_guias_procedimentos_admin_department",
            message="Departamento criado com sucesso.",
        )
    except Exception as exc:
        return _handle_domain(exc)


@router.put("/admin/departments/{department_id}")
@require_any_permission(GUIAS_PROCEDIMENTOS_WRITE_PERMISSIONS)
def update_admin_department(
    department_id: UUID,
    body: Annotated[DepartmentBody, Body(...)],
):
    try:
        data = build_update_department_use_case().execute(
            str(department_id),
            body.model_dump(),
            _actor(),
        )
        return api_delpi_success(
            data,
            operation_id="update_guias_procedimentos_admin_department",
            message="Departamento atualizado com sucesso.",
        )
    except Exception as exc:
        return _handle_domain(exc)


# --- procedures ---


@router.get("/admin/procedures")
@require_any_permission(GUIAS_PROCEDIMENTOS_WRITE_PERMISSIONS)
def list_admin_procedures(
    department_id: UUID | None = Query(default=None),
    status: str | None = Query(default=None),
    q: str | None = Query(default=None, max_length=200),
):
    try:
        data = build_list_admin_procedures_use_case().execute(
            department_id=str(department_id) if department_id else None,
            status=status,
            q=q,
        )
        return api_delpi_success(
            data,
            operation_id="list_guias_procedimentos_admin_procedures",
            message="Procedimentos (admin) recuperados com sucesso.",
        )
    except Exception as exc:
        return _handle_domain(exc)


@router.get("/admin/procedures/{procedure_id}")
@require_any_permission(GUIAS_PROCEDIMENTOS_WRITE_PERMISSIONS)
def get_admin_procedure(procedure_id: UUID):
    try:
        data = build_get_admin_procedure_use_case().execute(str(procedure_id))
        return api_delpi_success(
            data,
            operation_id="get_guias_procedimentos_admin_procedure",
            message="Procedimento recuperado com sucesso.",
        )
    except Exception as exc:
        return _handle_domain(exc)


@router.post("/admin/procedures")
@require_any_permission(GUIAS_PROCEDIMENTOS_WRITE_PERMISSIONS)
def create_admin_procedure(body: Annotated[ProcedureBody, Body(...)]):
    try:
        payload: dict[str, Any] = body.model_dump()
        payload["department_id"] = str(body.department_id)
        data = build_create_procedure_use_case().execute(payload, _actor())
        return api_delpi_success(
            data,
            operation_id="create_guias_procedimentos_admin_procedure",
            message="Procedimento criado com sucesso.",
        )
    except Exception as exc:
        return _handle_domain(exc)


@router.put("/admin/procedures/{procedure_id}")
@require_any_permission(GUIAS_PROCEDIMENTOS_WRITE_PERMISSIONS)
def update_admin_procedure(
    procedure_id: UUID,
    body: Annotated[ProcedureBody, Body(...)],
):
    try:
        payload: dict[str, Any] = body.model_dump(exclude_none=False)
        payload["department_id"] = str(body.department_id)
        # status no PUT é rejeitado no use case se vier diferente/null via exclude
        if body.status is None:
            payload.pop("status", None)
        data = build_update_procedure_use_case().execute(
            str(procedure_id),
            payload,
            _actor(),
        )
        return api_delpi_success(
            data,
            operation_id="update_guias_procedimentos_admin_procedure",
            message="Procedimento atualizado com sucesso.",
        )
    except Exception as exc:
        return _handle_domain(exc)


@router.post("/admin/procedures/{procedure_id}/publish")
@require_any_permission(GUIAS_PROCEDIMENTOS_WRITE_PERMISSIONS)
def publish_admin_procedure(procedure_id: UUID):
    try:
        data = build_publish_procedure_use_case().execute(str(procedure_id), _actor())
        return api_delpi_success(
            data,
            operation_id="publish_guias_procedimentos_admin_procedure",
            message="Procedimento publicado com sucesso.",
        )
    except Exception as exc:
        return _handle_domain(exc)


@router.post("/admin/procedures/{procedure_id}/unpublish")
@require_any_permission(GUIAS_PROCEDIMENTOS_WRITE_PERMISSIONS)
def unpublish_admin_procedure(procedure_id: UUID):
    try:
        data = build_unpublish_procedure_use_case().execute(str(procedure_id), _actor())
        return api_delpi_success(
            data,
            operation_id="unpublish_guias_procedimentos_admin_procedure",
            message="Procedimento despublicado com sucesso.",
        )
    except Exception as exc:
        return _handle_domain(exc)


@router.post("/admin/procedures/{procedure_id}/archive")
@require_any_permission(GUIAS_PROCEDIMENTOS_WRITE_PERMISSIONS)
def archive_admin_procedure(procedure_id: UUID):
    try:
        data = build_archive_procedure_use_case().execute(str(procedure_id), _actor())
        return api_delpi_success(
            data,
            operation_id="archive_guias_procedimentos_admin_procedure",
            message="Procedimento arquivado com sucesso.",
        )
    except Exception as exc:
        return _handle_domain(exc)


@router.post("/admin/procedures/{procedure_id}/restore")
@require_any_permission(GUIAS_PROCEDIMENTOS_WRITE_PERMISSIONS)
def restore_admin_procedure(procedure_id: UUID):
    try:
        data = build_restore_procedure_use_case().execute(str(procedure_id), _actor())
        return api_delpi_success(
            data,
            operation_id="restore_guias_procedimentos_admin_procedure",
            message="Procedimento restaurado como rascunho.",
        )
    except Exception as exc:
        return _handle_domain(exc)

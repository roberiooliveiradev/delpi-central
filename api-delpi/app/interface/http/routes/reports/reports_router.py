from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Body, Path, Query, Request
from pydantic import BaseModel, Field, field_validator

from delpi_auth.authz_core import has_any_permission
from delpi_auth.authorization import require_any_permission
from delpi_auth.request_context import get_current_user
from delpi_auth.service_token import request_has_valid_internal_service_token

from app.application.security.api_delpi_permissions import (
    REPORTS_READ_PERMISSIONS,
    REPORTS_WRITE_PERMISSIONS,
)
from app.composition.reports_composer import (
    build_create_report_definition_use_case,
    build_delete_report_schedule_use_case,
    build_get_report_definition_use_case,
    build_get_report_run_use_case,
    build_get_report_schedule_use_case,
    build_list_report_definitions_use_case,
    build_list_report_providers_use_case,
    build_list_report_recipients_use_case,
    build_list_report_runs_use_case,
    build_preview_safety_stock_shortage_30d_use_case,
    build_process_due_report_schedules_use_case,
    build_replace_report_recipients_use_case,
    build_run_report_definition_use_case,
    build_update_report_definition_use_case,
    build_upsert_report_schedule_use_case,
)
from app.core.responses import error_response, not_found_response
from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginsRepositoryError,
)
from app.interface.http.query_param_enums import BRANCH_QUERY_REQUIRED
from app.interface.http.route_response_helpers import api_delpi_success
from app.interface.http.routes.reports.reports_branch_access import branch_access_error
from app.utils.logger import log_error

router = APIRouter(tags=["Delpi Reports"])


class CreateReportDefinitionBody(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    provider_key: str = Field(min_length=1, max_length=100, alias="providerKey")
    params: dict[str, Any] = Field(default_factory=dict)
    active: bool = True

    model_config = {"populate_by_name": True}

    @field_validator("name", "provider_key", mode="before")
    @classmethod
    def strip_required(cls, value: object) -> str:
        if not isinstance(value, str):
            raise ValueError("deve ser string")
        text = value.strip()
        if not text:
            raise ValueError("não pode ser vazio")
        return text


class UpdateReportDefinitionBody(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    provider_key: str | None = Field(default=None, max_length=100, alias="providerKey")
    params: dict[str, Any] | None = None
    active: bool | None = None

    model_config = {"populate_by_name": True}

    @field_validator("name", "provider_key", mode="before")
    @classmethod
    def strip_optional(cls, value: object) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("deve ser string")
        text = value.strip()
        if not text:
            raise ValueError("não pode ser vazio")
        return text


class RecipientItemBody(BaseModel):
    user_id: str = Field(min_length=1, max_length=100, alias="userId")
    email: str = Field(min_length=3, max_length=320)

    model_config = {"populate_by_name": True}


class ReplaceRecipientsBody(BaseModel):
    items: list[RecipientItemBody] = Field(default_factory=list)


class UpsertScheduleBody(BaseModel):
    schedule_kind: str = Field(alias="scheduleKind")
    hour: int = Field(ge=0, le=23)
    minute: int = Field(ge=0, le=59)
    weekday: int | None = Field(default=None, ge=0, le=6)
    enabled: bool = True
    timezone: str = Field(default="America/Sao_Paulo", max_length=64)

    model_config = {"populate_by_name": True}

    @field_validator("schedule_kind", mode="before")
    @classmethod
    def normalize_kind(cls, value: object) -> str:
        text = str(value or "").strip().lower()
        if text not in {"daily", "weekly"}:
            raise ValueError("scheduleKind deve ser daily ou weekly")
        return text


def _permission_denied_if_missing(permission_codes: list[str]):
    user = get_current_user()
    if user is None:
        return error_response("Não autenticado.", status_code=401)
    if getattr(user, "is_superadmin", False):
        return None
    if not has_any_permission(user, permission_codes):
        return error_response("Sem permissão para esta operação.", status_code=403)
    return None


def _current_user_id() -> str | None:
    user = get_current_user()
    if user is None:
        return None
    user_id = getattr(user, "id", None)
    return str(user_id) if user_id else None


@router.get("/definitions", operation_id="list_report_definitions")
@require_any_permission(REPORTS_READ_PERMISSIONS)
def list_report_definitions():
    try:
        data = build_list_report_definitions_use_case().execute()
        return api_delpi_success(
            data,
            operation_id="list_report_definitions",
            message="Definições de relatório listadas com sucesso.",
        )
    except PluginsRepositoryError as exc:
        log_error(f"Erro ao listar definições Reports: {exc}")
        return error_response(
            "Erro interno ao listar definições de relatório.",
            status_code=500,
        )
    except Exception as exc:
        log_error(f"Erro inesperado ao listar definições Reports: {exc}")
        return error_response(
            "Erro interno ao listar definições de relatório.",
            status_code=500,
        )


@router.post("/definitions", operation_id="create_report_definition")
@require_any_permission(REPORTS_WRITE_PERMISSIONS)
def create_report_definition(
    body: Annotated[CreateReportDefinitionBody, Body(...)],
):
    try:
        data = build_create_report_definition_use_case().execute(
            name=body.name,
            provider_key=body.provider_key,
            params=body.params,
            active=body.active,
            created_by_user_id=_current_user_id(),
        )
        return api_delpi_success(
            data,
            operation_id="create_report_definition",
            message="Definição de relatório criada com sucesso.",
        )
    except PluginsRepositoryError as exc:
        log_error(f"Erro ao criar definição Reports: {exc}")
        return error_response(
            "Erro interno ao criar definição de relatório.",
            status_code=500,
        )
    except Exception as exc:
        log_error(f"Erro inesperado ao criar definição Reports: {exc}")
        return error_response(
            "Erro interno ao criar definição de relatório.",
            status_code=500,
        )


@router.get("/definitions/{definition_id}", operation_id="get_report_definition")
@require_any_permission(REPORTS_READ_PERMISSIONS)
def get_report_definition(
    definition_id: Annotated[UUID, Path(...)],
):
    try:
        data = build_get_report_definition_use_case().execute(str(definition_id))
        if data is None:
            return not_found_response("Definição de relatório não encontrada.")
        return api_delpi_success(
            data,
            operation_id="get_report_definition",
            message="Definição de relatório recuperada com sucesso.",
        )
    except PluginsRepositoryError as exc:
        log_error(f"Erro ao obter definição Reports: {exc}")
        return error_response(
            "Erro interno ao obter definição de relatório.",
            status_code=500,
        )
    except Exception as exc:
        log_error(f"Erro inesperado ao obter definição Reports: {exc}")
        return error_response(
            "Erro interno ao obter definição de relatório.",
            status_code=500,
        )


@router.patch("/definitions/{definition_id}", operation_id="update_report_definition")
@require_any_permission(REPORTS_WRITE_PERMISSIONS)
def update_report_definition(
    definition_id: Annotated[UUID, Path(...)],
    body: Annotated[UpdateReportDefinitionBody, Body(...)],
):
    try:
        data = build_update_report_definition_use_case().execute(
            definition_id=str(definition_id),
            name=body.name,
            provider_key=body.provider_key,
            params=body.params,
            active=body.active,
        )
        if data is None:
            return not_found_response("Definição de relatório não encontrada.")
        return api_delpi_success(
            data,
            operation_id="update_report_definition",
            message="Definição de relatório atualizada com sucesso.",
        )
    except PluginsRepositoryError as exc:
        log_error(f"Erro ao atualizar definição Reports: {exc}")
        return error_response(
            "Erro interno ao atualizar definição de relatório.",
            status_code=500,
        )
    except Exception as exc:
        log_error(f"Erro inesperado ao atualizar definição Reports: {exc}")
        return error_response(
            "Erro interno ao atualizar definição de relatório.",
            status_code=500,
        )


@router.get("/runs", operation_id="list_report_runs")
@require_any_permission(REPORTS_READ_PERMISSIONS)
def list_report_runs(
    definition_id: Annotated[UUID | None, Query(alias="definitionId")] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
):
    try:
        data = build_list_report_runs_use_case().execute(
            definition_id=str(definition_id) if definition_id else None,
            limit=limit,
        )
        return api_delpi_success(
            data,
            operation_id="list_report_runs",
            message="Execuções de relatório listadas com sucesso.",
        )
    except PluginsRepositoryError as exc:
        log_error(f"Erro ao listar runs Reports: {exc}")
        return error_response(
            "Erro interno ao listar execuções de relatório.",
            status_code=500,
        )
    except Exception as exc:
        log_error(f"Erro inesperado ao listar runs Reports: {exc}")
        return error_response(
            "Erro interno ao listar execuções de relatório.",
            status_code=500,
        )


@router.get("/providers", operation_id="list_report_providers")
@require_any_permission(REPORTS_READ_PERMISSIONS)
def list_report_providers():
    try:
        data = build_list_report_providers_use_case().execute()
        return api_delpi_success(
            data,
            operation_id="list_report_providers",
            message="Providers de relatório listados com sucesso.",
        )
    except Exception as exc:
        log_error(f"Erro inesperado ao listar providers Reports: {exc}")
        return error_response(
            "Erro interno ao listar providers de relatório.",
            status_code=500,
        )


@router.get(
    "/providers/safety_stock_shortage_30d/preview",
    operation_id="preview_report_provider_safety_stock_shortage_30d",
)
@require_any_permission(REPORTS_READ_PERMISSIONS)
def preview_safety_stock_shortage_30d(
    branch: str = BRANCH_QUERY_REQUIRED(),
    horizonDays: Annotated[int, Query(ge=1, le=365)] = 30,
    includeBlocked: Annotated[bool, Query()] = False,
    productGroup: Annotated[str | None, Query()] = None,
    unit: Annotated[str | None, Query()] = None,
    search: Annotated[str | None, Query()] = None,
    includeWithoutSafetyStock: Annotated[bool, Query()] = True,
):
    branch_error = branch_access_error(branch)
    if branch_error:
        return branch_error

    try:
        data = build_preview_safety_stock_shortage_30d_use_case().execute(
            {
                "branch": branch,
                "horizonDays": horizonDays,
                "includeBlocked": includeBlocked,
                "productGroup": productGroup,
                "unit": unit,
                "search": search,
                "includeWithoutSafetyStock": includeWithoutSafetyStock,
            }
        )
        return api_delpi_success(
            data,
            operation_id="preview_report_provider_safety_stock_shortage_30d",
            message="Preview de rupturas gerado com sucesso.",
        )
    except ValueError as exc:
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro inesperado no preview Reports shortage 30d: {exc}")
        return error_response(
            "Erro interno ao gerar preview do relatório.",
            status_code=500,
        )


@router.get(
    "/definitions/{definition_id}/recipients",
    operation_id="list_report_recipients",
)
@require_any_permission(REPORTS_READ_PERMISSIONS)
def list_report_recipients(definition_id: Annotated[UUID, Path(...)]):
    try:
        data = build_list_report_recipients_use_case().execute(str(definition_id))
        return api_delpi_success(
            data,
            operation_id="list_report_recipients",
            message="Destinatários listados com sucesso.",
        )
    except LookupError:
        return not_found_response("Definição de relatório não encontrada.")
    except PluginsRepositoryError as exc:
        log_error(f"Erro ao listar recipients Reports: {exc}")
        return error_response("Erro interno ao listar destinatários.", status_code=500)


@router.put(
    "/definitions/{definition_id}/recipients",
    operation_id="replace_report_recipients",
)
@require_any_permission(REPORTS_WRITE_PERMISSIONS)
def replace_report_recipients(
    definition_id: Annotated[UUID, Path(...)],
    body: Annotated[ReplaceRecipientsBody, Body(...)],
):
    try:
        data = build_replace_report_recipients_use_case().execute(
            definition_id=str(definition_id),
            items=[item.model_dump(by_alias=True) for item in body.items],
        )
        return api_delpi_success(
            data,
            operation_id="replace_report_recipients",
            message="Destinatários atualizados com sucesso.",
        )
    except LookupError:
        return not_found_response("Definição de relatório não encontrada.")
    except ValueError as exc:
        return error_response(str(exc), status_code=400)
    except PluginsRepositoryError as exc:
        log_error(f"Erro ao gravar recipients Reports: {exc}")
        return error_response("Erro interno ao gravar destinatários.", status_code=500)


@router.get(
    "/definitions/{definition_id}/schedule",
    operation_id="get_report_schedule",
)
@require_any_permission(REPORTS_READ_PERMISSIONS)
def get_report_schedule(definition_id: Annotated[UUID, Path(...)]):
    try:
        data = build_get_report_schedule_use_case().execute(str(definition_id))
        if data is None:
            return api_delpi_success(
                None,
                operation_id="get_report_schedule",
                message="Definição sem agenda.",
            )
        return api_delpi_success(
            data,
            operation_id="get_report_schedule",
            message="Agenda recuperada com sucesso.",
        )
    except LookupError:
        return not_found_response("Definição de relatório não encontrada.")
    except PluginsRepositoryError as exc:
        log_error(f"Erro ao obter schedule Reports: {exc}")
        return error_response("Erro interno ao obter agenda.", status_code=500)


@router.put(
    "/definitions/{definition_id}/schedule",
    operation_id="upsert_report_schedule",
)
@require_any_permission(REPORTS_WRITE_PERMISSIONS)
def upsert_report_schedule(
    definition_id: Annotated[UUID, Path(...)],
    body: Annotated[UpsertScheduleBody, Body(...)],
):
    try:
        data = build_upsert_report_schedule_use_case().execute(
            definition_id=str(definition_id),
            schedule_kind=body.schedule_kind,
            hour=body.hour,
            minute=body.minute,
            weekday=body.weekday,
            enabled=body.enabled,
            timezone_name=body.timezone,
        )
        return api_delpi_success(
            data,
            operation_id="upsert_report_schedule",
            message="Agenda salva com sucesso.",
        )
    except LookupError:
        return not_found_response("Definição de relatório não encontrada.")
    except ValueError as exc:
        return error_response(str(exc), status_code=400)
    except PluginsRepositoryError as exc:
        log_error(f"Erro ao gravar schedule Reports: {exc}")
        return error_response("Erro interno ao gravar agenda.", status_code=500)


@router.delete(
    "/definitions/{definition_id}/schedule",
    operation_id="delete_report_schedule",
)
@require_any_permission(REPORTS_WRITE_PERMISSIONS)
def delete_report_schedule(definition_id: Annotated[UUID, Path(...)]):
    try:
        deleted = build_delete_report_schedule_use_case().execute(str(definition_id))
        if not deleted:
            return not_found_response("Agenda não encontrada.")
        return api_delpi_success(
            {"deleted": True},
            operation_id="delete_report_schedule",
            message="Agenda removida com sucesso.",
        )
    except LookupError:
        return not_found_response("Definição de relatório não encontrada.")
    except PluginsRepositoryError as exc:
        log_error(f"Erro ao remover schedule Reports: {exc}")
        return error_response("Erro interno ao remover agenda.", status_code=500)


@router.post(
    "/definitions/{definition_id}/run",
    operation_id="run_report_definition",
)
@require_any_permission(REPORTS_WRITE_PERMISSIONS)
def run_report_definition(
    definition_id: Annotated[UUID, Path(...)],
    trigger: Annotated[str, Query()] = "manual",
):
    try:
        data = build_run_report_definition_use_case().execute(
            definition_id=str(definition_id),
            trigger=trigger,
        )
        return api_delpi_success(
            data,
            operation_id="run_report_definition",
            message="Execução de relatório concluída.",
        )
    except LookupError:
        return not_found_response("Definição de relatório não encontrada.")
    except ValueError as exc:
        return error_response(str(exc), status_code=400)
    except PluginsRepositoryError as exc:
        log_error(f"Erro ao executar report: {exc}")
        return error_response("Erro interno ao executar relatório.", status_code=500)
    except Exception as exc:
        log_error(f"Erro inesperado ao executar report: {exc}")
        return error_response("Erro interno ao executar relatório.", status_code=500)


@router.get("/runs/{run_id}", operation_id="get_report_run")
@require_any_permission(REPORTS_READ_PERMISSIONS)
def get_report_run(run_id: Annotated[UUID, Path(...)]):
    try:
        data = build_get_report_run_use_case().execute(str(run_id))
        if data is None:
            return not_found_response("Execução de relatório não encontrada.")
        return api_delpi_success(
            data,
            operation_id="get_report_run",
            message="Execução recuperada com sucesso.",
        )
    except PluginsRepositoryError as exc:
        log_error(f"Erro ao obter run Reports: {exc}")
        return error_response("Erro interno ao obter execução.", status_code=500)


@router.post(
    "/schedules/process-pending",
    operation_id="process_pending_report_schedules",
)
def process_pending_report_schedules(
    request: Request,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    if not request_has_valid_internal_service_token(request):
        denied = _permission_denied_if_missing(REPORTS_WRITE_PERMISSIONS)
        if denied is not None:
            return denied
    try:
        data = build_process_due_report_schedules_use_case().execute(limit=limit)
        return api_delpi_success(
            data,
            operation_id="process_pending_report_schedules",
            message="Agendas vencidas processadas.",
        )
    except PluginsRepositoryError as exc:
        log_error(f"Erro ao processar agendas Reports: {exc}")
        return error_response("Erro interno ao processar agendas.", status_code=500)
    except Exception as exc:
        log_error(f"Erro inesperado ao processar agendas Reports: {exc}")
        return error_response("Erro interno ao processar agendas.", status_code=500)

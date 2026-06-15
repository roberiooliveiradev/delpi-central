from __future__ import annotations

from fastapi import APIRouter, Body, Query
from pydantic import BaseModel, Field

from delpi_auth.authorization import require_any_permission
from delpi_auth.request_context import get_current_user

from app.application.security.api_delpi_permissions import (
    KAIZEN_RECORDS_READ_PERMISSIONS,
    KAIZEN_RECORDS_WRITE_PERMISSIONS,
)
from app.composition.kaizen_composer import (
    build_import_kaizens_from_sheet_use_case,
    build_kaizen_repository,
)
from app.core.responses import error_response, not_found_response
from app.interface.http.route_response_helpers import api_delpi_success
from app.infrastructure.persistence.plugins.plugin_base_repository import PluginsRepositoryError
from app.utils.logger import log_error

router = APIRouter(prefix="/kaizens/records", tags=["Kaizen — cadastro"])


class KaizenRecordBody(BaseModel):
    branch_code: str = Field(..., pattern="^(01|02)$")
    title: str = Field(..., min_length=2, max_length=500)
    accountable: str | None = Field(default=None, max_length=200)
    sector: str | None = Field(default=None, max_length=200)
    investment: float | None = None
    savings_type: str | None = Field(
        default=None,
        pattern="^(tempo|material|financeiro|qualitativo|misto)$",
    )
    seconds_per_occurrence: float | None = None
    occurrences_per_day: float | None = None
    hourly_cost: float | None = None
    quantity_saved_per_day: float | None = None
    unit_material_cost: float | None = None
    fixed_daily_savings: float | None = None
    status: str = Field(
        default="em_andamento",
        pattern="^(em_andamento|implantado|descontinuado|cancelado)$",
    )
    date_implemented: str | None = None
    date_discontinued: str | None = None
    notes: str | None = None


class ImportKaizensFromSheetBody(BaseModel):
    dry_run: bool = False


class UpdateKaizenRecordBody(BaseModel):
    branch_code: str | None = Field(default=None, pattern="^(01|02)$")
    title: str | None = Field(default=None, min_length=2, max_length=500)
    accountable: str | None = Field(default=None, max_length=200)
    sector: str | None = Field(default=None, max_length=200)
    investment: float | None = None
    savings_type: str | None = Field(
        default=None,
        pattern="^(tempo|material|financeiro|qualitativo|misto)$",
    )
    seconds_per_occurrence: float | None = None
    occurrences_per_day: float | None = None
    hourly_cost: float | None = None
    quantity_saved_per_day: float | None = None
    unit_material_cost: float | None = None
    fixed_daily_savings: float | None = None
    status: str | None = Field(
        default=None,
        pattern="^(em_andamento|implantado|descontinuado|cancelado)$",
    )
    date_implemented: str | None = None
    date_discontinued: str | None = None
    notes: str | None = None


def _current_user_id() -> str:
    user = get_current_user()
    if user is None:
        return "unknown"
    return str(getattr(user, "id", "unknown"))


def _body_to_fields(body: BaseModel) -> dict:
    return body.model_dump(exclude_unset=True)


@router.get("")
@require_any_permission(KAIZEN_RECORDS_READ_PERMISSIONS)
def list_kaizen_records(
    branch: str | None = Query(default=None, pattern="^(01|02)$"),
    status: str | None = Query(
        default=None,
        pattern="^(em_andamento|implantado|descontinuado|cancelado)$",
    ),
    savings_type: str | None = Query(
        default=None,
        pattern="^(tempo|material|financeiro|qualitativo|misto)$",
    ),
    title: str | None = Query(default=None),
    date_start: str | None = Query(default=None),
    date_end: str | None = Query(default=None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    try:
        repo = build_kaizen_repository()
        data = repo.list_records(
            branch_code=branch,
            status=status,
            savings_type=savings_type,
            title=title,
            date_start=date_start,
            date_end=date_end,
            page=page,
            page_size=page_size,
        )
        return api_delpi_success(
            data,
            operation_id="list_kaizen_records",
            shape="paged_list",
        )
    except PluginsRepositoryError as exc:
        log_error(f"Erro ao listar kaizens cadastrados: {exc}")
        return error_response(str(exc), status_code=500)
    except Exception as exc:
        log_error(f"Erro ao listar kaizens cadastrados: {exc}")
        return error_response("Erro interno ao listar kaizens.", status_code=500)


@router.post("")
@require_any_permission(KAIZEN_RECORDS_WRITE_PERMISSIONS)
def create_kaizen_record(body: KaizenRecordBody = Body(...)):
    try:
        repo = build_kaizen_repository()
        data = repo.create_record(
            fields=_body_to_fields(body),
            created_by_user_id=_current_user_id(),
        )
        return api_delpi_success(data, operation_id="create_kaizen_record")
    except PluginsRepositoryError as exc:
        log_error(f"Erro ao cadastrar kaizen: {exc}")
        return error_response(str(exc), status_code=500)
    except Exception as exc:
        log_error(f"Erro ao cadastrar kaizen: {exc}")
        return error_response("Erro interno ao cadastrar kaizen.", status_code=500)


@router.post("/import-from-sheet")
@require_any_permission(KAIZEN_RECORDS_WRITE_PERMISSIONS)
def import_kaizens_from_sheet(body: ImportKaizensFromSheetBody = Body(default_factory=ImportKaizensFromSheetBody)):
    try:
        use_case = build_import_kaizens_from_sheet_use_case()
        result = use_case.execute(
            created_by_user_id=_current_user_id(),
            dry_run=body.dry_run,
        )
        return api_delpi_success(
            result.to_dict(),
            operation_id="import_kaizens_from_sheet",
            shape="scalar",
        )
    except Exception as exc:
        log_error(f"Erro ao importar kaizens da planilha: {exc}")
        return error_response("Erro interno ao importar kaizens da planilha.", status_code=500)


@router.get("/{record_id}")
@require_any_permission(KAIZEN_RECORDS_READ_PERMISSIONS)
def get_kaizen_record(record_id: str):
    try:
        repo = build_kaizen_repository()
        data = repo.get_record(record_id)
        if data is None:
            return not_found_response("Kaizen não encontrado.")
        return api_delpi_success(data, operation_id="get_kaizen_record")
    except Exception as exc:
        log_error(f"Erro ao buscar kaizen cadastrado: {exc}")
        return error_response("Erro interno ao buscar kaizen.", status_code=500)


@router.put("/{record_id}")
@require_any_permission(KAIZEN_RECORDS_WRITE_PERMISSIONS)
def update_kaizen_record(record_id: str, body: UpdateKaizenRecordBody = Body(...)):
    try:
        repo = build_kaizen_repository()
        fields = _body_to_fields(body)
        if not fields:
            return error_response("Nenhum campo para atualizar.", status_code=400)

        data = repo.update_record(
            record_id,
            fields=fields,
            updated_by_user_id=_current_user_id(),
        )
        if data is None:
            return not_found_response("Kaizen não encontrado.")
        return api_delpi_success(data, operation_id="update_kaizen_record")
    except PluginsRepositoryError as exc:
        log_error(f"Erro ao atualizar kaizen: {exc}")
        return error_response(str(exc), status_code=500)
    except Exception as exc:
        log_error(f"Erro ao atualizar kaizen: {exc}")
        return error_response("Erro interno ao atualizar kaizen.", status_code=500)


@router.delete("/{record_id}")
@require_any_permission(KAIZEN_RECORDS_WRITE_PERMISSIONS)
def delete_kaizen_record(record_id: str):
    try:
        repo = build_kaizen_repository()
        deleted = repo.delete_record(record_id, updated_by_user_id=_current_user_id())
        if not deleted:
            return not_found_response("Kaizen não encontrado.")
        return api_delpi_success(
            {"id": record_id, "deleted": True},
            operation_id="delete_kaizen_record",
        )
    except Exception as exc:
        log_error(f"Erro ao excluir kaizen: {exc}")
        return error_response("Erro interno ao excluir kaizen.", status_code=500)

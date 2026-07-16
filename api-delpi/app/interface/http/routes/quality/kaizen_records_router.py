from __future__ import annotations

from fastapi import APIRouter, Body, File, Form, Query, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from delpi_auth.authorization import require_any_permission
from delpi_auth.request_context import get_current_user

from app.application.security.api_delpi_permissions import (
    KAIZEN_RECORDS_READ_PERMISSIONS,
    KAIZEN_RECORDS_WRITE_PERMISSIONS,
)
from app.application.services.kaizen.kaizen_evidence_storage import KaizenEvidenceStorageError
from app.composition.kaizen_composer import (
    build_import_kaizens_use_case,
    build_kaizen_evidence_repository,
    build_kaizen_evidence_storage,
    build_kaizen_repository,
)
from app.core.responses import error_response, not_found_response
from app.domain.services.kaizen.kaizen_status_date_rules import KaizenStatusDateError
from app.interface.http.openapi_agent_metadata import (
    QUALITY_KAIZEN_RECORD_BY_ID,
    QUALITY_KAIZEN_RECORDS_LIST,
)
from app.interface.http.route_response_helpers import api_delpi_success
from app.infrastructure.persistence.plugins.plugin_base_repository import PluginsRepositoryError
from app.utils.logger import log_error

router = APIRouter(prefix="/kaizens/records", tags=["Kaizen — cadastro"])


class KaizenParticipantBody(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    role: str = Field(default="participante", pattern="^(responsavel|participante|apoio)$")
    user_id: str | None = Field(default=None, max_length=100)


_STATUS_PATTERN = "^(recebido|aprovado|implantado|descontinuado|cancelado)$"


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
    realized_daily_savings: float | None = None
    status: str = Field(
        default="recebido",
        pattern=_STATUS_PATTERN,
    )
    date_implemented: str | None = None
    date_discontinued: str | None = None
    date_idea_received: str | None = None
    date_committee_approved: str | None = None
    notes: str | None = None
    process_description: str | None = None
    problem_description: str | None = None
    improvement_description: str | None = None
    expected_result: str | None = None
    category: str | None = Field(default=None, max_length=50)
    categories: list[str] | None = Field(default=None, max_length=10)
    participants: list[KaizenParticipantBody] | None = None
    effective_from: str | None = None
    change_reason: str | None = None
    parent_revision_id: str | None = None


KAIZEN_EXPORT_VERSION = 1


class ImportKaizensBody(BaseModel):
    items: list[dict] = Field(default_factory=list)
    dry_run: bool = False
    skip_existing: bool = True


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
    realized_daily_savings: float | None = None
    status: str | None = Field(
        default=None,
        pattern=_STATUS_PATTERN,
    )
    date_implemented: str | None = None
    date_discontinued: str | None = None
    date_idea_received: str | None = None
    date_committee_approved: str | None = None
    notes: str | None = None
    process_description: str | None = None
    problem_description: str | None = None
    improvement_description: str | None = None
    expected_result: str | None = None
    category: str | None = Field(default=None, max_length=50)
    categories: list[str] | None = Field(default=None, max_length=10)
    participants: list[KaizenParticipantBody] | None = None
    effective_from: str | None = None
    change_reason: str | None = None


class UpdateKaizenEvidenceBody(BaseModel):
    stage: str | None = Field(default=None, pattern="^(antes|depois|geral)$")
    description: str | None = None


class ImplementKaizenVersionBody(BaseModel):
    effective_from: str | None = None


def _current_user_id() -> str:
    user = get_current_user()
    if user is None:
        return "unknown"
    return str(getattr(user, "id", "unknown"))


def _current_user_name() -> str | None:
    user = get_current_user()
    if user is None:
        return None
    for attr in ("name", "full_name", "username", "email"):
        value = getattr(user, attr, None)
        if value:
            return str(value)
    return None


def _body_to_fields(body: BaseModel) -> dict:
    return body.model_dump(exclude_unset=True)


@router.get("", **QUALITY_KAIZEN_RECORDS_LIST)
@require_any_permission(KAIZEN_RECORDS_READ_PERMISSIONS)
def list_kaizen_records(
    branch: str | None = Query(default=None, pattern="^(01|02)$"),
    status: str | None = Query(
        default=None,
        pattern=_STATUS_PATTERN,
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
            actor_name=_current_user_name(),
        )
        return api_delpi_success(data, operation_id="create_kaizen_record")
    except KaizenStatusDateError as exc:
        return error_response(str(exc), status_code=400)
    except PluginsRepositoryError as exc:
        log_error(f"Erro ao cadastrar kaizen: {exc}")
        return error_response(str(exc), status_code=500)
    except Exception as exc:
        log_error(f"Erro ao cadastrar kaizen: {exc}")
        return error_response("Erro interno ao cadastrar kaizen.", status_code=500)


@router.get("/export")
@require_any_permission(KAIZEN_RECORDS_READ_PERMISSIONS)
def export_kaizen_records():
    try:
        from datetime import datetime, timezone

        repo = build_kaizen_repository()
        items = repo.export_records()
        return api_delpi_success(
            {
                "version": KAIZEN_EXPORT_VERSION,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "count": len(items),
                "items": items,
            },
            operation_id="export_kaizen_records",
            shape="scalar",
        )
    except PluginsRepositoryError as exc:
        log_error(f"Erro ao exportar kaizens: {exc}")
        return error_response(str(exc), status_code=500)
    except Exception as exc:
        log_error(f"Erro ao exportar kaizens: {exc}")
        return error_response("Erro interno ao exportar kaizens.", status_code=500)


@router.post("/import")
@require_any_permission(KAIZEN_RECORDS_WRITE_PERMISSIONS)
def import_kaizen_records(body: ImportKaizensBody = Body(...)):
    try:
        if not body.items:
            return error_response("Nenhum kaizen para importar (items vazio).", status_code=400)

        use_case = build_import_kaizens_use_case()
        result = use_case.execute(
            body.items,
            created_by_user_id=_current_user_id(),
            actor_name=_current_user_name(),
            dry_run=body.dry_run,
            skip_existing=body.skip_existing,
        )
        return api_delpi_success(
            result.to_dict(),
            operation_id="import_kaizen_records",
            shape="scalar",
        )
    except Exception as exc:
        log_error(f"Erro ao importar kaizens: {exc}")
        return error_response("Erro interno ao importar kaizens.", status_code=500)


@router.get("/summary")
@require_any_permission(KAIZEN_RECORDS_READ_PERMISSIONS)
def get_kaizen_records_summary(
    branch: str | None = Query(default=None, pattern="^(01|02)$"),
    date_start: str | None = Query(default=None),
    date_end: str | None = Query(default=None),
):
    try:
        repo = build_kaizen_repository()
        data = repo.summary(branch_code=branch, date_start=date_start, date_end=date_end)
        return api_delpi_success(
            data,
            operation_id="get_kaizen_records_summary",
            shape="scalar",
        )
    except PluginsRepositoryError as exc:
        log_error(f"Erro ao calcular indicadores de kaizen: {exc}")
        return error_response(str(exc), status_code=500)
    except Exception as exc:
        log_error(f"Erro ao calcular indicadores de kaizen: {exc}")
        return error_response("Erro interno ao calcular indicadores de kaizen.", status_code=500)


@router.get("/{record_id}", **QUALITY_KAIZEN_RECORD_BY_ID)
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
            actor_name=_current_user_name(),
        )
        if data is None:
            return not_found_response("Kaizen não encontrado.")
        return api_delpi_success(data, operation_id="update_kaizen_record")
    except KaizenStatusDateError as exc:
        return error_response(str(exc), status_code=400)
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
        deleted = repo.delete_record(
            record_id,
            updated_by_user_id=_current_user_id(),
            actor_name=_current_user_name(),
        )
        if not deleted:
            return not_found_response("Kaizen não encontrado.")
        return api_delpi_success(
            {"id": record_id, "deleted": True},
            operation_id="delete_kaizen_record",
        )
    except Exception as exc:
        log_error(f"Erro ao excluir kaizen: {exc}")
        return error_response("Erro interno ao excluir kaizen.", status_code=500)


# ---------------------------------------------------------------- revisões


@router.get("/{record_id}/revisions")
@require_any_permission(KAIZEN_RECORDS_READ_PERMISSIONS)
def list_kaizen_revisions(record_id: str):
    try:
        repo = build_kaizen_repository()
        if repo.get_record(record_id, with_participants=False) is None:
            return not_found_response("Kaizen não encontrado.")
        items = repo.list_revisions(record_id)
        return api_delpi_success(
            {"items": items},
            operation_id="list_kaizen_revisions",
            shape="paged_list",
        )
    except Exception as exc:
        log_error(f"Erro ao listar revisões do kaizen: {exc}")
        return error_response("Erro interno ao listar revisões do kaizen.", status_code=500)


@router.get("/{record_id}/revisions/{revision_number}")
@require_any_permission(KAIZEN_RECORDS_READ_PERMISSIONS)
def get_kaizen_revision(record_id: str, revision_number: int):
    try:
        repo = build_kaizen_repository()
        revision = repo.get_revision(record_id, revision_number)
        if revision is None:
            return not_found_response("Revisão não encontrada.")
        return api_delpi_success(revision, operation_id="get_kaizen_revision")
    except Exception as exc:
        log_error(f"Erro ao buscar revisão do kaizen: {exc}")
        return error_response("Erro interno ao buscar revisão do kaizen.", status_code=500)


@router.get("/{record_id}/at")
@require_any_permission(KAIZEN_RECORDS_READ_PERMISSIONS)
def get_kaizen_at_date(record_id: str, date: str = Query(..., description="Data YYYY-MM-DD")):
    try:
        repo = build_kaizen_repository()
        revision = repo.get_revision_at(record_id, date)
        if revision is None:
            return not_found_response("Nenhuma revisão vigente na data informada.")
        return api_delpi_success(revision, operation_id="get_kaizen_at_date")
    except Exception as exc:
        log_error(f"Erro ao buscar estado do kaizen na data: {exc}")
        return error_response("Erro interno ao buscar estado do kaizen na data.", status_code=500)


# ---------------------------------------------------------------- versões (ciclo de vida)


@router.post("/{record_id}/versions")
@require_any_permission(KAIZEN_RECORDS_WRITE_PERMISSIONS)
def create_kaizen_version(record_id: str, body: KaizenRecordBody = Body(...)):
    try:
        repo = build_kaizen_repository()
        data = repo.create_version(
            record_id,
            fields=_body_to_fields(body),
            created_by_user_id=_current_user_id(),
            actor_name=_current_user_name(),
        )
        if data is None:
            return not_found_response("Kaizen não encontrado.")
        return api_delpi_success(data, operation_id="create_kaizen_version")
    except PluginsRepositoryError as exc:
        log_error(f"Erro ao criar versão do kaizen: {exc}")
        return error_response(str(exc), status_code=500)
    except Exception as exc:
        log_error(f"Erro ao criar versão do kaizen: {exc}")
        return error_response("Erro interno ao criar versão do kaizen.", status_code=500)


@router.put("/{record_id}/versions/{revision_number}")
@require_any_permission(KAIZEN_RECORDS_WRITE_PERMISSIONS)
def update_kaizen_version(
    record_id: str,
    revision_number: int,
    body: UpdateKaizenRecordBody = Body(...),
):
    try:
        repo = build_kaizen_repository()
        fields = _body_to_fields(body)
        if not fields:
            return error_response("Nenhum campo para atualizar.", status_code=400)
        data = repo.update_version(
            record_id,
            revision_number,
            fields=fields,
            updated_by_user_id=_current_user_id(),
            actor_name=_current_user_name(),
        )
        if data is None:
            return not_found_response("Versão não encontrada.")
        return api_delpi_success(data, operation_id="update_kaizen_version")
    except KaizenStatusDateError as exc:
        return error_response(str(exc), status_code=400)
    except PluginsRepositoryError as exc:
        log_error(f"Erro ao atualizar versão do kaizen: {exc}")
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro ao atualizar versão do kaizen: {exc}")
        return error_response("Erro interno ao atualizar versão do kaizen.", status_code=500)


@router.delete("/{record_id}/versions/{revision_number}")
@require_any_permission(KAIZEN_RECORDS_WRITE_PERMISSIONS)
def delete_kaizen_version(record_id: str, revision_number: int):
    try:
        repo = build_kaizen_repository()
        deleted = repo.delete_version(
            record_id,
            revision_number,
            actor_user_id=_current_user_id(),
            actor_name=_current_user_name(),
        )
        if not deleted:
            return not_found_response("Versão não encontrada.")
        return api_delpi_success(
            {"record_id": record_id, "revision_number": revision_number, "deleted": True},
            operation_id="delete_kaizen_version",
        )
    except PluginsRepositoryError as exc:
        log_error(f"Erro ao excluir versão do kaizen: {exc}")
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro ao excluir versão do kaizen: {exc}")
        return error_response("Erro interno ao excluir versão do kaizen.", status_code=500)


@router.post("/{record_id}/versions/{revision_number}/implement")
@require_any_permission(KAIZEN_RECORDS_WRITE_PERMISSIONS)
def implement_kaizen_version(
    record_id: str,
    revision_number: int,
    body: ImplementKaizenVersionBody = Body(default_factory=ImplementKaizenVersionBody),
):
    try:
        repo = build_kaizen_repository()
        data = repo.implement_version(
            record_id,
            revision_number,
            effective_from=body.effective_from,
            updated_by_user_id=_current_user_id(),
            actor_name=_current_user_name(),
        )
        if data is None:
            return not_found_response("Versão não encontrada.")
        return api_delpi_success(data, operation_id="implement_kaizen_version")
    except PluginsRepositoryError as exc:
        log_error(f"Erro ao implantar versão do kaizen: {exc}")
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro ao implantar versão do kaizen: {exc}")
        return error_response("Erro interno ao implantar versão do kaizen.", status_code=500)


# ---------------------------------------------------------------- registro de alterações


@router.get("/{record_id}/history")
@require_any_permission(KAIZEN_RECORDS_READ_PERMISSIONS)
def list_kaizen_history(record_id: str):
    try:
        repo = build_kaizen_repository()
        if repo.get_record(record_id, with_participants=False) is None:
            return not_found_response("Kaizen não encontrado.")
        items = repo.list_history(record_id)
        return api_delpi_success(
            {"items": items},
            operation_id="list_kaizen_history",
            shape="paged_list",
        )
    except Exception as exc:
        log_error(f"Erro ao listar histórico do kaizen: {exc}")
        return error_response("Erro interno ao listar histórico do kaizen.", status_code=500)


@router.get("/{record_id}/audit-log")
@require_any_permission(KAIZEN_RECORDS_READ_PERMISSIONS)
def list_kaizen_audit_log(record_id: str):
    try:
        repo = build_kaizen_repository()
        if repo.get_record(record_id, with_participants=False) is None:
            return not_found_response("Kaizen não encontrado.")
        items = repo.list_audit_log(record_id)
        return api_delpi_success(
            {"items": items},
            operation_id="list_kaizen_audit_log",
            shape="paged_list",
        )
    except Exception as exc:
        log_error(f"Erro ao listar auditoria do kaizen: {exc}")
        return error_response("Erro interno ao listar auditoria do kaizen.", status_code=500)


@router.get("/{record_id}/savings-timeline")
@require_any_permission(KAIZEN_RECORDS_READ_PERMISSIONS)
def get_kaizen_savings_timeline(
    record_id: str,
    date_start: str | None = Query(default=None),
    date_end: str | None = Query(default=None),
):
    try:
        repo = build_kaizen_repository()
        if repo.get_record(record_id, with_participants=False) is None:
            return not_found_response("Kaizen não encontrado.")
        data = repo.savings_timeline(record_id, date_start=date_start, date_end=date_end)
        return api_delpi_success(
            data,
            operation_id="get_kaizen_savings_timeline",
            shape="scalar",
        )
    except Exception as exc:
        log_error(f"Erro ao calcular ganhos por período do kaizen: {exc}")
        return error_response("Erro interno ao calcular ganhos por período.", status_code=500)


# ---------------------------------------------------------------- evidências


@router.get("/{record_id}/evidences")
@require_any_permission(KAIZEN_RECORDS_READ_PERMISSIONS)
def list_kaizen_evidences(record_id: str):
    try:
        repo = build_kaizen_evidence_repository()
        items = repo.list_evidences(record_id)
        return api_delpi_success(
            {"items": items},
            operation_id="list_kaizen_evidences",
            shape="paged_list",
        )
    except Exception as exc:
        log_error(f"Erro ao listar evidências do kaizen: {exc}")
        return error_response("Erro interno ao listar evidências do kaizen.", status_code=500)


@router.post("/{record_id}/evidences")
@require_any_permission(KAIZEN_RECORDS_WRITE_PERMISSIONS)
async def attach_kaizen_evidence(
    record_id: str,
    evidence_type: str = Form(default="attachment"),
    stage: str = Form(default="geral"),
    description: str | None = Form(default=None),
    external_url: str | None = Form(default=None),
    revision_id: str | None = Form(default=None),
    file: UploadFile | None = File(default=None),
):
    try:
        record_repo = build_kaizen_repository()
        if record_repo.get_record(record_id, with_participants=False) is None:
            return not_found_response("Kaizen não encontrado.")

        repo = build_kaizen_evidence_repository()
        fields: dict = {
            "type": evidence_type,
            "stage": stage,
            "description": description,
            "revision_id": revision_id or None,
            "uploaded_by_user_id": _current_user_id(),
            "uploaded_by_name": _current_user_name(),
        }

        if evidence_type == "link":
            if not external_url:
                return error_response("URL obrigatória para evidência do tipo link.", status_code=400)
            fields["external_url"] = external_url
        else:
            if file is None:
                return error_response("Arquivo obrigatório.", status_code=400)
            content = await file.read()
            storage = build_kaizen_evidence_storage()
            try:
                stored_name = storage.save(
                    kaizen_id=record_id,
                    original_name=file.filename or "arquivo",
                    content=content,
                    mime_type=file.content_type,
                )
            except KaizenEvidenceStorageError as exc:
                return error_response(str(exc), status_code=400)
            fields.update(
                {
                    "file_name": file.filename,
                    "stored_name": stored_name,
                    "mime_type": file.content_type,
                    "size_bytes": len(content),
                }
            )

        data = repo.create_evidence(record_id, fields)
        return api_delpi_success(data, operation_id="attach_kaizen_evidence")
    except Exception as exc:
        log_error(f"Erro ao anexar evidência do kaizen: {exc}")
        return error_response("Erro interno ao anexar evidência do kaizen.", status_code=500)


@router.get("/{record_id}/evidences/{evidence_id}/file")
@require_any_permission(KAIZEN_RECORDS_READ_PERMISSIONS)
def download_kaizen_evidence(record_id: str, evidence_id: str):
    try:
        repo = build_kaizen_evidence_repository()
        evidence = repo.get_evidence(record_id, evidence_id)
        if not evidence or not evidence.get("stored_name"):
            return not_found_response("Evidência não encontrada.")
        storage = build_kaizen_evidence_storage()
        try:
            path = storage.resolve_file(kaizen_id=record_id, stored_name=evidence["stored_name"])
        except KaizenEvidenceStorageError:
            return not_found_response("Arquivo não encontrado.")
        return FileResponse(
            path,
            media_type=evidence.get("mime_type") or "application/octet-stream",
            filename=evidence.get("file_name") or evidence["stored_name"],
        )
    except Exception as exc:
        log_error(f"Erro ao baixar evidência do kaizen: {exc}")
        return error_response("Erro interno ao baixar evidência do kaizen.", status_code=500)


@router.patch("/{record_id}/evidences/{evidence_id}")
@require_any_permission(KAIZEN_RECORDS_WRITE_PERMISSIONS)
def update_kaizen_evidence(
    record_id: str,
    evidence_id: str,
    body: UpdateKaizenEvidenceBody = Body(...),
):
    try:
        repo = build_kaizen_evidence_repository()
        data = repo.update_evidence(record_id, evidence_id, body.model_dump(exclude_unset=True))
        if data is None:
            return not_found_response("Evidência não encontrada.")
        return api_delpi_success(data, operation_id="update_kaizen_evidence")
    except Exception as exc:
        log_error(f"Erro ao atualizar evidência do kaizen: {exc}")
        return error_response("Erro interno ao atualizar evidência do kaizen.", status_code=500)


@router.delete("/{record_id}/evidences/{evidence_id}")
@require_any_permission(KAIZEN_RECORDS_WRITE_PERMISSIONS)
def delete_kaizen_evidence(record_id: str, evidence_id: str):
    try:
        repo = build_kaizen_evidence_repository()
        removed = repo.delete_evidence(record_id, evidence_id)
        if not removed:
            return not_found_response("Evidência não encontrada.")
        stored_name = removed.get("stored_name")
        if stored_name:
            build_kaizen_evidence_storage().delete_file(kaizen_id=record_id, stored_name=stored_name)
        return api_delpi_success(
            {"id": evidence_id, "deleted": True},
            operation_id="delete_kaizen_evidence",
        )
    except Exception as exc:
        log_error(f"Erro ao excluir evidência do kaizen: {exc}")
        return error_response("Erro interno ao excluir evidência do kaizen.", status_code=500)

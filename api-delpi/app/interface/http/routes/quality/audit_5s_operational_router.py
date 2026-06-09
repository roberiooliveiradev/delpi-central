from __future__ import annotations

from fastapi import APIRouter, Body, File, Form, Query, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from delpi_auth.authorization import require_any_permission
from delpi_auth.request_context import get_current_user

from app.application.security.api_delpi_permissions import (
    AUDIT_5S_READ_PERMISSIONS,
    AUDIT_5S_WRITE_PERMISSIONS,
)

from app.application.services.audit_5s.nc_attachment_storage import (
    Audit5sNcAttachmentStorage,
    Audit5sNcAttachmentStorageError,
)
from app.composition.audit_5s_composer import (
    build_audit_5s_repository,
    build_get_audit_5s_dashboard_use_case,
)
from app.application.services.audit_5s.realtime_publisher import (
    publish_audit_updated,
    publish_response_updated,
)
from app.core.responses import error_response
from app.interface.http.route_response_helpers import api_delpi_success
from app.infrastructure.persistence.plugins.plugin_base_repository import PluginsRepositoryError
from app.shared.utils.person_name import format_person_name
from app.utils.logger import log_error

router = APIRouter(prefix="/audit-5s", tags=["Auditoria 5S"])


class CreateAreaBody(BaseModel):
    branch_code: str = Field(..., pattern="^(01|02)$")
    name: str = Field(..., min_length=2, max_length=200)


class AuditorBody(BaseModel):
    user_id: str
    display_name: str


class CreateAuditBody(BaseModel):
    branch_code: str = Field(..., pattern="^(01|02)$")
    audit_date: str
    area_id: str
    area_responsible: str = Field(..., min_length=2, max_length=200)
    shift: str = Field(..., pattern="^(TURNO_1|TURNO_2|TURNO_3|ADMINISTRATIVO)$")
    auditors: list[AuditorBody] = Field(default_factory=list)


class UpsertResponseBody(BaseModel):
    score: int | None = Field(default=None)
    is_not_applicable: bool = False
    observation: str | None = None
    version: int | None = None


class CreateNonconformityBody(BaseModel):
    response_id: str
    description: str = Field(..., min_length=3)
    responsible_name: str = Field(..., min_length=2, max_length=200)
    due_date: str
    root_cause: str | None = None
    corrective_action: str | None = None
    priority: str | None = Field(default=None, pattern="^(high|medium|low)$")


class UpdateNonconformityBody(BaseModel):
    description: str | None = Field(default=None, min_length=3)
    responsible_name: str | None = Field(default=None, min_length=2, max_length=200)
    due_date: str | None = None
    root_cause: str | None = None
    corrective_action: str | None = None
    priority: str | None = Field(default=None, pattern="^(high|medium|low)$")


class AddNcActionBody(BaseModel):
    description: str = Field(..., min_length=3)


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


@router.get("/areas")
@require_any_permission(AUDIT_5S_READ_PERMISSIONS)
def list_areas(
    branch: str = Query(..., pattern="^(01|02)$"),
    active: bool = Query(True),
):
    try:
        repo = build_audit_5s_repository()
        data = repo.list_areas(branch, active_only=active)
        return api_delpi_success(data, operation_id="list_audit_5s_areas")
    except Exception as exc:
        log_error(f"Erro ao listar áreas 5S: {exc}")
        return error_response("Erro interno ao listar áreas.", status_code=500)


@router.post("/areas")
@require_any_permission(AUDIT_5S_WRITE_PERMISSIONS)
def create_area(body: CreateAreaBody = Body(...)):
    try:
        repo = build_audit_5s_repository()
        data = repo.create_area(
            branch_code=body.branch_code,
            name=body.name,
            created_by_user_id=_current_user_id(),
        )
        return api_delpi_success(data, operation_id="create_audit_5s_area")
    except PluginsRepositoryError as exc:
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro ao cadastrar área 5S: {exc}")
        return error_response("Erro interno ao cadastrar área.", status_code=500)


@router.get("/criteria")
@require_any_permission(AUDIT_5S_READ_PERMISSIONS)
def list_criteria(catalog_version: int | None = Query(None, ge=1)):
    try:
        repo = build_audit_5s_repository()
        data = repo.list_criteria_catalog(catalog_version)
        return api_delpi_success(data, operation_id="list_audit_5s_criteria")
    except Exception as exc:
        log_error(f"Erro ao listar critérios 5S: {exc}")
        return error_response("Erro interno ao listar critérios.", status_code=500)


@router.get("/audits")
@require_any_permission(AUDIT_5S_READ_PERMISSIONS)
def list_audits(
    branch: str = Query(..., pattern="^(01|02)$"),
    status: str | None = Query(None),
):
    try:
        repo = build_audit_5s_repository()
        data = repo.list_audits(branch, status=status)
        return api_delpi_success(data, operation_id="list_audit_5s_audits")
    except Exception as exc:
        log_error(f"Erro ao listar auditorias 5S: {exc}")
        return error_response("Erro interno ao listar auditorias.", status_code=500)


@router.post("/audits")
@require_any_permission(AUDIT_5S_WRITE_PERMISSIONS)
def create_audit(body: CreateAuditBody = Body(...)):
    try:
        user_id = _current_user_id()
        auditors = [
            {
                "user_id": item.user_id,
                "display_name": format_person_name(item.display_name),
            }
            for item in body.auditors
        ]
        if not any(a["user_id"] == user_id for a in auditors):
            auditors.append({"user_id": user_id, "display_name": _current_user_name()})

        repo = build_audit_5s_repository()
        data = repo.create_audit(
            branch_code=body.branch_code,
            audit_date=body.audit_date,
            area_id=body.area_id,
            area_responsible=body.area_responsible,
            shift=body.shift,
            created_by_user_id=user_id,
            auditors=auditors,
        )
        return api_delpi_success(data, operation_id="create_audit_5s_audit")
    except PluginsRepositoryError as exc:
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro ao criar auditoria 5S: {exc}")
        return error_response("Erro interno ao criar auditoria.", status_code=500)


@router.get("/audits/{audit_id}")
@require_any_permission(AUDIT_5S_READ_PERMISSIONS)
def get_audit(audit_id: str):
    try:
        repo = build_audit_5s_repository()
        data = repo.get_audit(audit_id)
        if not data:
            return error_response("Auditoria não encontrada.", status_code=404)
        return api_delpi_success(data, operation_id="get_audit_5s_audit")
    except Exception as exc:
        log_error(f"Erro ao buscar auditoria 5S: {exc}")
        return error_response("Erro interno ao buscar auditoria.", status_code=500)


@router.post("/audits/{audit_id}/delete")
@require_any_permission(AUDIT_5S_WRITE_PERMISSIONS)
def delete_audit(audit_id: str):
    audit_id = audit_id.strip()
    if not audit_id:
        return error_response("Identificador da auditoria inválido.", status_code=400)

    try:
        repo = build_audit_5s_repository()
        audit = repo.get_audit_delete_target(audit_id)
        if not audit:
            return error_response("Auditoria não encontrada.", status_code=404)
        if audit["status"] != "draft":
            return error_response(
                "Somente auditorias em avaliação podem ser excluídas.",
                status_code=422,
            )

        attachments = repo.list_nc_attachments_for_audit(audit_id)
        storage = Audit5sNcAttachmentStorage()
        for nc_id in {str(item["nonconformity_id"]) for item in attachments}:
            storage.delete_nonconformity_dir(nc_id)

        repo.delete_audit(audit_id)
        return api_delpi_success(
            None,
            operation_id="delete_audit_5s_audit",
            message="Auditoria excluída com sucesso.",
        )
    except PluginsRepositoryError as exc:
        message = str(exc)
        status_code = 404 if "não encontrada" in message.lower() else 422
        return error_response(message, status_code=status_code)
    except Audit5sNcAttachmentStorageError as exc:
        return error_response(str(exc), status_code=422)
    except Exception as exc:
        log_error(f"Erro ao excluir auditoria 5S: {exc}")
        return error_response("Erro interno ao excluir auditoria.", status_code=500)


@router.post("/audits/{audit_id}/join")
@require_any_permission(AUDIT_5S_WRITE_PERMISSIONS)
def join_audit(audit_id: str):
    try:
        repo = build_audit_5s_repository()
        audit = repo.get_audit(audit_id)
        if not audit:
            return error_response("Auditoria não encontrada.", status_code=404)

        user_id = _current_user_id()
        display_name = _current_user_name()
        repo.ensure_auditor(
            audit_id=audit_id,
            user_id=user_id,
            display_name=display_name,
        )
        data = repo.get_audit(audit_id)
        if not data:
            return error_response("Auditoria não encontrada.", status_code=404)
        return api_delpi_success(data, operation_id="join_audit_5s_audit")
    except PluginsRepositoryError as exc:
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro ao registrar participação na auditoria 5S: {exc}")
        return error_response("Erro interno ao registrar participação.", status_code=500)


@router.put("/audits/{audit_id}/responses/{criterion_id}")
@require_any_permission(AUDIT_5S_WRITE_PERMISSIONS)
async def upsert_response(
    audit_id: str,
    criterion_id: str,
    body: UpsertResponseBody = Body(...),
):
    try:
        if body.is_not_applicable:
            score = None
        elif body.score not in (1, 3, 5):
            return error_response("Nota inválida. Use 1, 3, 5 ou NA.", status_code=400)
        else:
            score = body.score

        repo = build_audit_5s_repository()
        data = repo.upsert_response(
            audit_id=audit_id,
            criterion_id=criterion_id,
            score=score,
            is_not_applicable=body.is_not_applicable,
            observation=body.observation,
            updated_by_user_id=_current_user_id(),
            expected_version=body.version,
        )
        audit = repo.get_audit(audit_id)
        try:
            await publish_response_updated(
                audit_id=audit_id,
                response=data,
                audit=audit or {},
                actor_user_id=_current_user_id(),
                actor_display_name=_current_user_name(),
            )
        except Exception as publish_exc:
            log_error(f"Falha ao publicar evento realtime 5S: {publish_exc}")
        return api_delpi_success({"response": data, "audit": audit}, operation_id="upsert_audit_5s_response")
    except PluginsRepositoryError as exc:
        return error_response(str(exc), status_code=422)
    except Exception as exc:
        log_error(f"Erro ao salvar resposta 5S: {exc}")
        return error_response("Erro interno ao salvar resposta.", status_code=500)


@router.post("/audits/{audit_id}/complete-evaluation")
@require_any_permission(AUDIT_5S_WRITE_PERMISSIONS)
async def complete_evaluation(audit_id: str):
    try:
        repo = build_audit_5s_repository()
        data = repo.complete_evaluation(audit_id)
        try:
            await publish_audit_updated(
                audit_id=audit_id,
                audit=data,
                event_type="evaluation_complete",
                actor_user_id=_current_user_id(),
                actor_display_name=_current_user_name(),
            )
        except Exception as publish_exc:
            log_error(f"Falha ao publicar evento realtime 5S: {publish_exc}")
        return api_delpi_success(data, operation_id="complete_audit_5s_evaluation")
    except PluginsRepositoryError as exc:
        return error_response(str(exc), status_code=422)
    except Exception as exc:
        log_error(f"Erro ao concluir avaliação 5S: {exc}")
        return error_response("Erro interno ao concluir avaliação.", status_code=500)


@router.get("/audits/{audit_id}/nc-candidates")
@require_any_permission(AUDIT_5S_READ_PERMISSIONS)
def list_nc_candidates(audit_id: str):
    try:
        repo = build_audit_5s_repository()
        data = repo.list_nc_candidates(audit_id)
        return api_delpi_success(data, operation_id="list_audit_5s_nc_candidates")
    except PluginsRepositoryError as exc:
        return error_response(str(exc), status_code=404)
    except Exception as exc:
        log_error(f"Erro ao listar NC candidatas 5S: {exc}")
        return error_response("Erro interno ao listar NC candidatas.", status_code=500)


@router.get("/audits/{audit_id}/nonconformities")
@require_any_permission(AUDIT_5S_READ_PERMISSIONS)
def list_audit_nonconformities(audit_id: str):
    try:
        repo = build_audit_5s_repository()
        data = repo.list_nonconformities(audit_id)
        return api_delpi_success(data, operation_id="list_audit_5s_nonconformities")
    except Exception as exc:
        log_error(f"Erro ao listar NCs 5S: {exc}")
        return error_response("Erro interno ao listar NCs.", status_code=500)


@router.post("/audits/{audit_id}/nonconformities")
@require_any_permission(AUDIT_5S_WRITE_PERMISSIONS)
async def create_nonconformity(audit_id: str, body: CreateNonconformityBody = Body(...)):
    try:
        repo = build_audit_5s_repository()
        data = repo.create_nonconformity(
            audit_id=audit_id,
            response_id=body.response_id,
            description=body.description,
            responsible_name=body.responsible_name,
            due_date=body.due_date,
            root_cause=body.root_cause,
            corrective_action=body.corrective_action,
            priority=body.priority,
            created_by_user_id=_current_user_id(),
        )
        audit = repo.get_audit(audit_id)
        if audit:
            try:
                await publish_audit_updated(
                    audit_id=audit_id,
                    audit=audit,
                    event_type="nc_created",
                    actor_user_id=_current_user_id(),
                    actor_display_name=_current_user_name(),
                )
            except Exception as publish_exc:
                log_error(f"Falha ao publicar evento realtime 5S: {publish_exc}")
        return api_delpi_success(data, operation_id="create_audit_5s_nonconformity")
    except PluginsRepositoryError as exc:
        return error_response(str(exc), status_code=422)
    except Exception as exc:
        log_error(f"Erro ao criar NC 5S: {exc}")
        return error_response("Erro interno ao criar NC.", status_code=500)


@router.patch("/nonconformities/{nc_id}")
@require_any_permission(AUDIT_5S_WRITE_PERMISSIONS)
async def update_nonconformity(nc_id: str, body: UpdateNonconformityBody = Body(...)):
    try:
        repo = build_audit_5s_repository()
        data = repo.update_nonconformity(
            nonconformity_id=nc_id,
            description=body.description,
            responsible_name=body.responsible_name,
            due_date=body.due_date,
            root_cause=body.root_cause,
            corrective_action=body.corrective_action,
            priority=body.priority,
            actor_user_id=_current_user_id(),
        )
        audit_id = str(data["audit_id"])
        audit = repo.get_audit(audit_id)
        if audit:
            try:
                await publish_audit_updated(
                    audit_id=audit_id,
                    audit=audit,
                    event_type="nc_updated",
                    actor_user_id=_current_user_id(),
                    actor_display_name=_current_user_name(),
                )
            except Exception as publish_exc:
                log_error(f"Falha ao publicar evento realtime 5S: {publish_exc}")
        return api_delpi_success(data, operation_id="update_audit_5s_nonconformity")
    except PluginsRepositoryError as exc:
        return error_response(str(exc), status_code=422)
    except Exception as exc:
        log_error(f"Erro ao atualizar NC 5S: {exc}")
        return error_response("Erro interno ao atualizar NC.", status_code=500)


@router.get("/nonconformities/{nc_id}/actions")
@require_any_permission(AUDIT_5S_READ_PERMISSIONS)
def list_nc_actions(nc_id: str):
    try:
        repo = build_audit_5s_repository()
        data = repo.list_nc_actions(nc_id)
        return api_delpi_success(data, operation_id="list_audit_5s_nc_actions")
    except Exception as exc:
        log_error(f"Erro ao listar ações NC 5S: {exc}")
        return error_response("Erro interno ao listar ações.", status_code=500)


@router.post("/nonconformities/{nc_id}/actions")
@require_any_permission(AUDIT_5S_WRITE_PERMISSIONS)
def add_nc_action(nc_id: str, body: AddNcActionBody = Body(...)):
    try:
        repo = build_audit_5s_repository()
        data = repo.add_nc_action(
            nonconformity_id=nc_id,
            description=body.description,
            actor_user_id=_current_user_id(),
            actor_display_name=_current_user_name(),
        )
        return api_delpi_success(data, operation_id="create_audit_5s_nc_action")
    except PluginsRepositoryError as exc:
        return error_response(str(exc), status_code=422)
    except Exception as exc:
        log_error(f"Erro ao registrar ação NC 5S: {exc}")
        return error_response("Erro interno ao registrar ação.", status_code=500)


@router.get("/audits/{audit_id}/nc-attachments")
@require_any_permission(AUDIT_5S_READ_PERMISSIONS)
def list_audit_nc_attachments(audit_id: str):
    try:
        repo = build_audit_5s_repository()
        data = repo.list_nc_attachments_for_audit(audit_id)
        return api_delpi_success(data, operation_id="list_audit_5s_audit_nc_attachments")
    except Exception as exc:
        log_error(f"Erro ao listar evidências NC 5S: {exc}")
        return error_response("Erro interno ao listar evidências.", status_code=500)


@router.get("/nonconformities/{nc_id}/attachments")
@require_any_permission(AUDIT_5S_READ_PERMISSIONS)
def list_nc_attachments(nc_id: str):
    try:
        repo = build_audit_5s_repository()
        data = repo.list_nc_attachments(nc_id)
        return api_delpi_success(data, operation_id="list_audit_5s_nc_attachments")
    except Exception as exc:
        log_error(f"Erro ao listar evidências NC 5S: {exc}")
        return error_response("Erro interno ao listar evidências.", status_code=500)


@router.post("/nonconformities/{nc_id}/attachments")
@require_any_permission(AUDIT_5S_WRITE_PERMISSIONS)
async def upload_nc_attachment(
    nc_id: str,
    attachment_type: str = Form(..., pattern="^(before|after)$"),
    file: UploadFile = File(...),
):
    try:
        content = await file.read()
        storage = Audit5sNcAttachmentStorage()
        storage.validate_upload(
            mime_type=file.content_type,
            size_bytes=len(content),
        )
        stored_name = storage.save(
            nonconformity_id=nc_id,
            attachment_type=attachment_type,
            original_name=file.filename or f"{attachment_type}.jpg",
            content=content,
            mime_type=file.content_type,
        )
        repo = build_audit_5s_repository()
        data = repo.upsert_nc_attachment(
            nonconformity_id=nc_id,
            attachment_type=attachment_type,
            original_name=file.filename or f"{attachment_type}.jpg",
            stored_name=stored_name,
            mime_type=file.content_type,
            size_bytes=len(content),
            uploaded_by_user_id=_current_user_id(),
        )
        return api_delpi_success(data, operation_id="attach_audit_5s_evidence", message="Evidência anexada com sucesso.")
    except (PluginsRepositoryError, Audit5sNcAttachmentStorageError) as exc:
        return error_response(str(exc), status_code=422)
    except Exception as exc:
        log_error(f"Erro ao anexar evidência NC 5S: {exc}")
        return error_response("Erro interno ao anexar evidência.", status_code=500)


@router.get("/nonconformities/{nc_id}/attachments/{attachment_id}/file")
@require_any_permission(AUDIT_5S_READ_PERMISSIONS)
def download_nc_attachment(nc_id: str, attachment_id: str):
    try:
        repo = build_audit_5s_repository()
        attachment = repo.get_nc_attachment(attachment_id)
        if not attachment or str(attachment["nonconformity_id"]) != nc_id:
            return error_response("Evidência não encontrada.", status_code=404)

        storage = Audit5sNcAttachmentStorage()
        file_path = storage.resolve_file(
            nonconformity_id=nc_id,
            stored_name=str(attachment["stored_name"]),
        )
        return FileResponse(
            path=file_path,
            media_type=attachment.get("mime_type") or "application/octet-stream",
            filename=str(attachment.get("original_name") or attachment["stored_name"]),
        )
    except (PluginsRepositoryError, Audit5sNcAttachmentStorageError) as exc:
        return error_response(str(exc), status_code=404)
    except Exception as exc:
        log_error(f"Erro ao baixar evidência NC 5S: {exc}")
        return error_response("Erro interno ao baixar evidência.", status_code=500)


@router.post("/nonconformities/{nc_id}/complete-action")
@require_any_permission(AUDIT_5S_WRITE_PERMISSIONS)
async def complete_nc_action(nc_id: str):
    try:
        repo = build_audit_5s_repository()
        data = repo.complete_nc_action(
            nonconformity_id=nc_id,
            actor_user_id=_current_user_id(),
        )
        audit_id = str(data["audit_id"])
        audit = repo.get_audit(audit_id)
        if audit:
            try:
                await publish_audit_updated(
                    audit_id=audit_id,
                    audit=audit,
                    event_type="nc_action_completed",
                    actor_user_id=_current_user_id(),
                    actor_display_name=_current_user_name(),
                )
            except Exception as publish_exc:
                log_error(f"Falha ao publicar evento realtime 5S: {publish_exc}")
        return api_delpi_success(data, operation_id="complete_audit_5s_nc_action", message="Ação finalizada com sucesso.")
    except PluginsRepositoryError as exc:
        return error_response(str(exc), status_code=422)
    except Exception as exc:
        log_error(f"Erro ao finalizar ação NC 5S: {exc}")
        return error_response("Erro interno ao finalizar ação.", status_code=500)


@router.get("/analytics/dashboard")
@require_any_permission(AUDIT_5S_READ_PERMISSIONS)
def get_audit_5s_dashboard(
    branch: str = Query(..., pattern="^(01|02)$"),
    date_start: str = Query(..., alias="date_start"),
    date_end: str = Query(..., alias="date_end"),
    area_id: str | None = Query(None),
    shift: str | None = Query(None, pattern="^(TURNO_1|TURNO_2|TURNO_3|ADMINISTRATIVO)$"),
    audit_status: str | None = Query(
        None,
        alias="audit_status",
        pattern="^(draft|evaluation_complete|nc_in_progress|closed)$",
    ),
    senso_order: int | None = Query(None, ge=1, le=5),
    granularity: str = Query("month", pattern="^(day|week|month)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    try:
        use_case = build_get_audit_5s_dashboard_use_case()
        result = use_case.execute(
            branch_code=branch,
            date_start=date_start,
            date_end=date_end,
            area_id=area_id,
            shift=shift,
            audit_status=audit_status,
            senso_order=senso_order,
            granularity=granularity,
            page=page,
            page_size=page_size,
        )
        return api_delpi_success(result.to_dict(), operation_id="get_audit_5s_analytics_dashboard")
    except ValueError as exc:
        return error_response(str(exc), status_code=400)
    except PluginsRepositoryError as exc:
        return error_response(str(exc), status_code=422)
    except Exception as exc:
        log_error(f"Erro ao carregar dashboard 5S: {exc}")
        return error_response("Erro interno ao carregar dashboard.", status_code=500)


@router.post("/audits/{audit_id}/close")
@require_any_permission(AUDIT_5S_WRITE_PERMISSIONS)
async def close_audit(audit_id: str):
    try:
        repo = build_audit_5s_repository()
        data = repo.close_audit(audit_id)
        try:
            await publish_audit_updated(
                audit_id=audit_id,
                audit=data,
                event_type="closed",
                actor_user_id=_current_user_id(),
                actor_display_name=_current_user_name(),
            )
        except Exception as publish_exc:
            log_error(f"Falha ao publicar evento realtime 5S: {publish_exc}")
        return api_delpi_success(data, operation_id="close_audit_5s_audit")
    except PluginsRepositoryError as exc:
        return error_response(str(exc), status_code=422)
    except Exception as exc:
        log_error(f"Erro ao encerrar auditoria 5S: {exc}")
        return error_response("Erro interno ao encerrar auditoria.", status_code=500)

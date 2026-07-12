from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Body, File, Form, Query, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from delpi_auth.authorization import require_any_permission
from delpi_auth.request_context import get_current_user

from app.application.security.api_delpi_permissions import (
    AUDIT_5S_READ_PERMISSIONS,
    AUDIT_5S_WRITE_PERMISSIONS,
)

from app.application.dto.audit_5s.list_audit_5s_nc_board_request import (
    ListAudit5sNcBoardRequest,
)
from app.application.services.audit_5s.nc_attachment_storage import (
    Audit5sNcAttachmentStorage,
    Audit5sNcAttachmentStorageError,
)
from app.application.services.audit_5s.response_attachment_storage import (
    Audit5sResponseAttachmentStorage,
    Audit5sResponseAttachmentStorageError,
)
from app.application.services.audit_5s.catalog_publish_service import (
    CatalogPublishValidationError,
    catalogs_are_equal,
    validate_publish_payload,
)
from app.application.services.audit_5s.scoring_service import (
    can_attach_criterion_photo,
    is_nc_candidate,
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
from app.interface.http.routes.quality.audit_5s_branch_access import branch_access_error
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


class UpdateAuditBody(BaseModel):
    audit_date: str | None = None
    area_id: str | None = None
    area_responsible: str | None = Field(default=None, min_length=2, max_length=200)
    shift: str | None = Field(
        default=None,
        pattern="^(TURNO_1|TURNO_2|TURNO_3|ADMINISTRATIVO)$",
    )
    auditors: list[AuditorBody] | None = None


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


class CatalogCriterionBody(BaseModel):
    senso_order: int = Field(..., ge=1, le=5)
    sort_order: int = Field(..., ge=1)
    code: str = Field(..., min_length=3, max_length=20)
    description: str = Field(..., min_length=3, max_length=2000)


class CatalogSensoNameBody(BaseModel):
    senso_sort_order: int = Field(..., ge=1, le=5)
    name: str = Field(..., min_length=2, max_length=100)


class PublishCatalogBody(BaseModel):
    branch_code: str = Field(..., pattern="^(01|02)$")
    criteria: list[CatalogCriterionBody] = Field(..., min_length=1)
    senso_names: list[CatalogSensoNameBody] | None = None
    notes: str | None = Field(default=None, max_length=500)


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
def list_criteria(
    catalog_version: int | None = Query(None, ge=1),
    branch: str | None = Query(None, pattern="^(01|02)$"),
):
    try:
        repo = build_audit_5s_repository()
        version = catalog_version
        if version is None and branch is not None:
            version = repo.resolve_catalog_version(branch)
        data = repo.list_criteria_catalog(version)
        return api_delpi_success(data, operation_id="list_audit_5s_criteria")
    except Exception as exc:
        log_error(f"Erro ao listar critérios 5S: {exc}")
        return error_response("Erro interno ao listar critérios.", status_code=500)


@router.get("/catalog")
@require_any_permission(AUDIT_5S_READ_PERMISSIONS)
def get_catalog(branch: str = Query(..., pattern="^(01|02)$")):
    branch_error = branch_access_error(branch)
    if branch_error is not None:
        return branch_error
    try:
        repo = build_audit_5s_repository()
        data = repo.get_active_catalog(branch)
        return api_delpi_success(data, operation_id="get_audit_5s_catalog")
    except Exception as exc:
        log_error(f"Erro ao carregar catálogo 5S: {exc}")
        return error_response("Erro interno ao carregar catálogo.", status_code=500)


@router.get("/catalog/publications")
@require_any_permission(AUDIT_5S_READ_PERMISSIONS)
def list_catalog_publications(branch: str = Query(..., pattern="^(01|02)$")):
    branch_error = branch_access_error(branch)
    if branch_error is not None:
        return branch_error
    try:
        repo = build_audit_5s_repository()
        data = repo.list_catalog_publications(branch)
        return api_delpi_success(data, operation_id="list_audit_5s_catalog_publications")
    except Exception as exc:
        log_error(f"Erro ao listar publicações do catálogo 5S: {exc}")
        return error_response("Erro interno ao listar publicações.", status_code=500)


@router.put("/catalog/publish")
@require_any_permission(AUDIT_5S_WRITE_PERMISSIONS)
def publish_catalog(body: PublishCatalogBody = Body(...)):
    branch_error = branch_access_error(body.branch_code, require_audit=True)
    if branch_error is not None:
        return branch_error
    try:
        repo = build_audit_5s_repository()
        normalized_criteria = validate_publish_payload(
            criteria=[item.model_dump() for item in body.criteria],
            senso_names=(
                [item.model_dump() for item in body.senso_names]
                if body.senso_names is not None
                else None
            ),
        )
        active = repo.get_active_catalog(body.branch_code)
        next_senso_names = (
            [item.model_dump() for item in body.senso_names]
            if body.senso_names is not None
            else None
        )
        if catalogs_are_equal(
            current_criteria=active["criteria"],
            next_criteria=normalized_criteria,
            current_senso_names=active["senso_names"],
            next_senso_names=next_senso_names,
        ):
            return error_response("Nenhuma alteração detectada.", status_code=409)

        data = repo.publish_catalog(
            branch_code=body.branch_code,
            criteria=normalized_criteria,
            senso_names=next_senso_names,
            published_by_user_id=_current_user_id(),
            notes=body.notes,
        )
        return api_delpi_success(data, operation_id="publish_audit_5s_catalog")
    except CatalogPublishValidationError as exc:
        return error_response(str(exc), status_code=400)
    except PluginsRepositoryError as exc:
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro ao publicar catálogo 5S: {exc}")
        return error_response("Erro interno ao publicar catálogo.", status_code=500)


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


@router.patch("/audits/{audit_id}")
@require_any_permission(AUDIT_5S_WRITE_PERMISSIONS)
async def update_audit(audit_id: str, body: UpdateAuditBody = Body(...)):
    audit_id = audit_id.strip()
    if not audit_id:
        return error_response("Identificador da auditoria inválido.", status_code=400)

    if (
        body.audit_date is None
        and body.area_id is None
        and body.area_responsible is None
        and body.shift is None
        and body.auditors is None
    ):
        return error_response("Informe ao menos um campo para atualizar.", status_code=400)

    try:
        auditors = None
        if body.auditors is not None:
            auditors = [
                {
                    "user_id": item.user_id,
                    "display_name": format_person_name(item.display_name),
                }
                for item in body.auditors
            ]

        repo = build_audit_5s_repository()
        data = repo.update_audit(
            audit_id=audit_id,
            audit_date=body.audit_date,
            area_id=body.area_id,
            area_responsible=body.area_responsible,
            shift=body.shift,
            auditors=auditors,
        )
        try:
            await publish_audit_updated(
                audit_id=audit_id,
                audit=data,
                event_type="header_updated",
                actor_user_id=_current_user_id(),
                actor_display_name=_current_user_name(),
            )
        except Exception as publish_exc:
            log_error(f"Falha ao publicar evento realtime 5S: {publish_exc}")
        return api_delpi_success(
            data,
            operation_id="update_audit_5s_audit",
            message="Cabeçalho da auditoria atualizado com sucesso.",
        )
    except PluginsRepositoryError as exc:
        message = str(exc)
        status_code = 404 if "não encontrada" in message.lower() else 422
        return error_response(message, status_code=status_code)
    except Exception as exc:
        log_error(f"Erro ao atualizar auditoria 5S: {exc}")
        return error_response("Erro interno ao atualizar auditoria.", status_code=500)


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


@router.post("/audits/{audit_id}/force-delete")
@require_any_permission(AUDIT_5S_WRITE_PERMISSIONS)
def force_delete_audit(audit_id: str):
    audit_id = audit_id.strip()
    if not audit_id:
        return error_response("Identificador da auditoria inválido.", status_code=400)

    try:
        repo = build_audit_5s_repository()
        audit = repo.get_audit_delete_target(audit_id)
        if not audit:
            return error_response("Auditoria não encontrada.", status_code=404)

        branch_error = branch_access_error(audit["branch_code"], require_audit=True)
        if branch_error is not None:
            return branch_error

        repo.force_delete_audit(audit_id)
        return api_delpi_success(
            None,
            operation_id="force_delete_audit_5s_audit",
            message="Auditoria excluída permanentemente.",
        )
    except PluginsRepositoryError as exc:
        message = str(exc)
        status_code = 404 if "não encontrada" in message.lower() else 422
        return error_response(message, status_code=status_code)
    except (Audit5sNcAttachmentStorageError, Audit5sResponseAttachmentStorageError) as exc:
        return error_response(str(exc), status_code=422)
    except Exception as exc:
        log_error(f"Erro ao excluir auditoria 5S (force-delete): {exc}")
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


@router.get("/audits/{audit_id}/responses/{criterion_id}/attachments")
@require_any_permission(AUDIT_5S_READ_PERMISSIONS)
def list_response_attachments(audit_id: str, criterion_id: str):
    try:
        repo = build_audit_5s_repository()
        attachment = repo.get_response_attachment_for_criterion(
            audit_id=audit_id,
            criterion_id=criterion_id,
        )
        data = [attachment] if attachment else []
        return api_delpi_success(
            data,
            operation_id="list_audit_5s_response_attachments",
        )
    except Exception as exc:
        log_error(f"Erro ao listar foto do critério 5S: {exc}")
        return error_response("Erro interno ao listar foto do critério.", status_code=500)


@router.post("/audits/{audit_id}/responses/{criterion_id}/attachments")
@require_any_permission(AUDIT_5S_WRITE_PERMISSIONS)
async def upload_response_attachment(
    audit_id: str,
    criterion_id: str,
    file: UploadFile = File(...),
):
    try:
        content = await file.read()
        storage = Audit5sResponseAttachmentStorage()
        storage.validate_upload(
            mime_type=file.content_type,
            size_bytes=len(content),
        )
        repo = build_audit_5s_repository()
        response = repo.get_response_for_criterion(
            audit_id=audit_id,
            criterion_id=criterion_id,
        )
        if not response:
            return error_response(
                "Salve a nota do critério antes de anexar a foto.",
                status_code=422,
            )
        if not can_attach_criterion_photo(
            response.get("score"), bool(response.get("is_not_applicable"))
        ):
            return error_response(
                "Foto do critério disponível após informar a nota (1, 3 ou 5).",
                status_code=422,
            )

        file_name, storage_path = storage.save(
            response_id=str(response["id"]),
            original_name=file.filename or "criterion.jpg",
            content=content,
            mime_type=file.content_type,
        )
        data = repo.upsert_response_attachment(
            audit_id=audit_id,
            criterion_id=criterion_id,
            original_name=file.filename or "criterion.jpg",
            file_name=file_name,
            storage_path=storage_path,
            mime_type=file.content_type,
            size_bytes=len(content),
            uploaded_by_user_id=_current_user_id(),
        )
        return api_delpi_success(
            data,
            operation_id="attach_audit_5s_response_photo",
            message="Foto do critério anexada com sucesso.",
        )
    except (PluginsRepositoryError, Audit5sResponseAttachmentStorageError) as exc:
        return error_response(str(exc), status_code=422)
    except Exception as exc:
        log_error(f"Erro ao anexar foto do critério 5S: {exc}")
        return error_response("Erro interno ao anexar foto do critério.", status_code=500)


@router.get("/audits/{audit_id}/responses/{criterion_id}/attachments/{attachment_id}/file")
@require_any_permission(AUDIT_5S_READ_PERMISSIONS)
def download_response_attachment(audit_id: str, criterion_id: str, attachment_id: str):
    try:
        repo = build_audit_5s_repository()
        attachment = repo.get_response_attachment(attachment_id)
        if (
            not attachment
            or str(attachment["audit_id"]) != audit_id
            or str(attachment["criterion_id"]) != criterion_id
        ):
            return error_response("Foto do critério não encontrada.", status_code=404)

        storage = Audit5sResponseAttachmentStorage()
        file_path = storage.resolve_file(
            response_id=str(attachment["response_id"]),
            file_name=str(attachment["file_name"]),
        )
        return FileResponse(
            path=file_path,
            media_type=attachment.get("mime_type") or "application/octet-stream",
            filename=str(attachment.get("original_name") or attachment["file_name"]),
        )
    except (PluginsRepositoryError, Audit5sResponseAttachmentStorageError) as exc:
        return error_response(str(exc), status_code=404)
    except Exception as exc:
        log_error(f"Erro ao baixar foto do critério 5S: {exc}")
        return error_response("Erro interno ao baixar foto do critério.", status_code=500)


@router.delete("/audits/{audit_id}/responses/{criterion_id}/attachments/{attachment_id}")
@require_any_permission(AUDIT_5S_WRITE_PERMISSIONS)
def delete_response_attachment(audit_id: str, criterion_id: str, attachment_id: str):
    try:
        repo = build_audit_5s_repository()
        repo.delete_response_attachment(
            audit_id=audit_id,
            criterion_id=criterion_id,
            attachment_id=attachment_id,
        )
        return api_delpi_success(
            {"deleted": True},
            operation_id="delete_audit_5s_response_photo",
            message="Foto do critério removida.",
        )
    except PluginsRepositoryError as exc:
        return error_response(str(exc), status_code=422)
    except Exception as exc:
        log_error(f"Erro ao remover foto do critério 5S: {exc}")
        return error_response("Erro interno ao remover foto do critério.", status_code=500)


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


@router.post("/audits/{audit_id}/reopen-evaluation")
@require_any_permission(AUDIT_5S_WRITE_PERMISSIONS)
async def reopen_evaluation(audit_id: str):
    audit_id = audit_id.strip()
    if not audit_id:
        return error_response("Identificador da auditoria inválido.", status_code=400)

    try:
        repo = build_audit_5s_repository()
        audit = repo.get_audit(audit_id)
        if not audit:
            return error_response("Auditoria não encontrada.", status_code=404)

        branch_error = branch_access_error(audit["branch_code"], require_audit=True)
        if branch_error is not None:
            return branch_error

        data = repo.reopen_evaluation(audit_id)
        try:
            await publish_audit_updated(
                audit_id=audit_id,
                audit=data,
                event_type="evaluation_reopened",
                actor_user_id=_current_user_id(),
                actor_display_name=_current_user_name(),
            )
        except Exception as publish_exc:
            log_error(f"Falha ao publicar evento realtime 5S: {publish_exc}")
        return api_delpi_success(
            data,
            operation_id="reopen_audit_5s_evaluation",
            message="Auditoria reaberta para avaliação.",
        )
    except PluginsRepositoryError as exc:
        return error_response(str(exc), status_code=422)
    except Exception as exc:
        log_error(f"Erro ao reabrir avaliação 5S: {exc}")
        return error_response("Erro interno ao reabrir avaliação.", status_code=500)


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


@router.get("/nonconformities")
@require_any_permission(AUDIT_5S_READ_PERMISSIONS)
def list_audit_5s_nonconformities_board(
    branch: str = Query(..., pattern="^(01|02)$"),
    date_start: str = Query(..., alias="date_start"),
    date_end: str = Query(..., alias="date_end"),
    area_id: str | None = Query(None),
    shift: str | None = Query(None, pattern="^(TURNO_1|TURNO_2|TURNO_3|ADMINISTRATIVO)$"),
    status: str | None = Query(None, pattern="^(open|in_progress|closed|cancelled)$"),
    priority: str | None = Query(None, pattern="^(high|medium|low)$"),
    responsible: str | None = Query(None),
    overdue_only: bool = Query(False),
    senso_order: int | None = Query(None, ge=1, le=5),
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort: str = Query(
        "due_date_asc",
        pattern="^(due_date_asc|due_date_desc|created_desc|priority_desc)$",
    ),
):
    denied = branch_access_error(branch)
    if denied is not None:
        return denied
    try:
        parsed_start = date.fromisoformat(date_start)
        parsed_end = date.fromisoformat(date_end)
    except ValueError:
        return error_response("Período inválido.", status_code=400)
    if parsed_start > parsed_end:
        return error_response("Data inicial não pode ser maior que a final.", status_code=400)
    try:
        repo = build_audit_5s_repository()
        request = ListAudit5sNcBoardRequest(
            branch_code=branch,
            date_start=parsed_start,
            date_end=parsed_end,
            area_id=area_id,
            shift=shift,
            status=status,
            priority=priority,
            responsible=responsible,
            overdue_only=overdue_only,
            senso_order=senso_order,
            search=search,
            page=page,
            page_size=page_size,
            sort=sort,
        )
        data = repo.list_nonconformities_board(request)
        return api_delpi_success(data, operation_id="list_audit_5s_nonconformities_board")
    except PluginsRepositoryError as exc:
        return error_response(str(exc), status_code=422)
    except Exception as exc:
        log_error(f"Erro ao listar board de NCs 5S: {exc}")
        return error_response("Erro interno ao listar não conformidades.", status_code=500)


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

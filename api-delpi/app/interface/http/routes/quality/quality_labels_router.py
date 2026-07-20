from __future__ import annotations

from typing import Annotated, Any, Optional

from fastapi import APIRouter, Body, File, Form, Query, Response, UploadFile
from pydantic import BaseModel, Field, field_validator

from delpi_auth.authorization import require_any_permission
from delpi_auth.request_context import get_current_user

from app.application.security.api_delpi_permissions import (
    QUALITY_LABELS_READ_PERMISSIONS,
    QUALITY_LABELS_WRITE_PERMISSIONS,
)
from app.application.services.quality_labels.quality_labels_certificate_service import (
    QualityLabelsCertificateError,
)
from app.application.services.quality_labels.quality_labels_signature_storage import (
    QualityLabelsSignatureError,
)
from app.application.use_cases.quality_labels.quality_labels_service import (
    ProductionOrderNotFoundError,
    QualityLabelsError,
)
from app.composition.quality_labels_composer import (
    build_quality_labels_certificate_service,
    build_quality_labels_inspector_service,
    build_quality_labels_service,
)
from app.infrastructure.persistence.plugins.repositories.quality_labels.postgres_quality_labels_checklist_template_repository import (
    PostgresQualityLabelsChecklistTemplateRepository,
)
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
    inspectedQuantity: Optional[int] = Field(default=None, ge=0)

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


class InspectorProfileBody(BaseModel):
    displayName: str = Field(min_length=1)
    roleTitle: Optional[str] = None

    @field_validator("displayName", "roleTitle", mode="before")
    @classmethod
    def _strip(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value


class CertificateItemBody(BaseModel):
    position: Optional[int] = None
    description: str = Field(default="")
    status: str = Field(default="A")
    isCustom: bool = False


class CertificateBody(BaseModel):
    sampleType: str = Field(default="fornecimento")
    quantity: Optional[str] = None
    sampleQuantity: Optional[str] = None
    customerCode: Optional[str] = None
    customerStore: Optional[str] = None
    customerName: Optional[str] = None
    customerItem: Optional[str] = None
    customerItemRev: Optional[str] = None
    customerSource: Optional[str] = None
    delpiNotes: Optional[str] = None
    customerNotes: Optional[str] = None
    items: list[CertificateItemBody] = Field(default_factory=list)
    issue: bool = False


def _parse_branches(raw: Optional[str]) -> list[str] | None:
    if not raw:
        return None
    values = [part.strip() for part in raw.split(",") if part.strip()]
    return values or None


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


@router.get("/search-ops", operation_id="search_quality_label_ops")
@require_any_permission(QUALITY_LABELS_WRITE_PERMISSIONS)
def search_ops(
    q: str = Query(..., min_length=1),
    branches: Optional[str] = None,
    limit: int = Query(8, ge=1, le=20),
):
    try:
        service = build_quality_labels_service()
        data = service.search_ops(
            term=q,
            branches=_parse_branches(branches),
            limit=limit,
        )
        return api_delpi_success(
            {"items": data},
            operation_id="search_quality_label_ops",
            message="Ordens de produção encontradas.",
        )
    except Exception as exc:
        log_error(f"Erro ao buscar OPs para etiqueta de qualidade: {exc}")
        return error_response("Erro interno ao buscar as OPs.", status_code=500)


@router.get("/audit-events", operation_id="list_quality_label_audit_events")
@require_any_permission(QUALITY_LABELS_READ_PERMISSIONS)
def list_audit_events(
    search: Optional[str] = None,
    eventTypes: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    try:
        service = build_quality_labels_service()
        data = service.list_audit_events(
            search=search,
            event_types=_parse_branches(eventTypes),
            limit=limit,
            offset=offset,
        )
        return api_delpi_success(
            data,
            operation_id="list_quality_label_audit_events",
            message="Eventos de auditoria recuperados com sucesso.",
        )
    except Exception as exc:
        log_error(f"Erro ao listar auditoria de etiquetas de qualidade: {exc}")
        return error_response("Erro interno ao listar a auditoria.", status_code=500)


@router.get("/checklist-template", operation_id="list_quality_label_checklist_template")
@require_any_permission(QUALITY_LABELS_READ_PERMISSIONS)
def list_checklist_template():
    try:
        repository = PostgresQualityLabelsChecklistTemplateRepository()
        rows = repository.list_active()
        return api_delpi_success(
            {"items": [repository.to_payload(row) for row in rows]},
            operation_id="list_quality_label_checklist_template",
            message="Template do checklist recuperado com sucesso.",
        )
    except Exception as exc:
        log_error(f"Erro ao listar template do checklist: {exc}")
        return error_response("Erro interno ao listar o template.", status_code=500)


@router.get("/inspectors/me", operation_id="get_quality_label_inspector")
@require_any_permission(QUALITY_LABELS_READ_PERMISSIONS)
def get_my_inspector():
    try:
        service = build_quality_labels_inspector_service()
        data = service.get_profile(user_id=_current_user_id())
        if data is None:
            data = {
                "userId": _current_user_id(),
                "displayName": _current_user_name(),
                "roleTitle": None,
                "hasSignature": False,
                "signatureUpdatedAt": None,
            }
        return api_delpi_success(
            data,
            operation_id="get_quality_label_inspector",
            message="Perfil do inspetor recuperado com sucesso.",
        )
    except Exception as exc:
        log_error(f"Erro ao buscar perfil do inspetor: {exc}")
        return error_response("Erro interno ao buscar o inspetor.", status_code=500)


@router.put("/inspectors/me", operation_id="save_quality_label_inspector")
@require_any_permission(QUALITY_LABELS_WRITE_PERMISSIONS)
def save_my_inspector(body: Annotated[InspectorProfileBody, Body(...)]):
    try:
        service = build_quality_labels_inspector_service()
        data = service.save_profile(
            user_id=_current_user_id(),
            display_name=body.displayName,
            role_title=body.roleTitle,
        )
        return api_delpi_success(
            data,
            operation_id="save_quality_label_inspector",
            message="Perfil do inspetor salvo com sucesso.",
        )
    except Exception as exc:
        log_error(f"Erro ao salvar perfil do inspetor: {exc}")
        return error_response("Erro interno ao salvar o inspetor.", status_code=500)


@router.post("/inspectors/me/signature")
@require_any_permission(QUALITY_LABELS_WRITE_PERMISSIONS)
async def upload_my_signature(signature: UploadFile = File(...)):
    try:
        content = await signature.read()
        service = build_quality_labels_inspector_service()
        data = service.set_signature(
            user_id=_current_user_id(),
            display_name=_current_user_name(),
            content=content,
            mime_type=signature.content_type,
        )
        return api_delpi_success(
            data,
            operation_id="upload_quality_label_inspector_signature",
            message="Assinatura registrada com sucesso.",
        )
    except QualityLabelsSignatureError as exc:
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro ao registrar assinatura do inspetor: {exc}")
        return error_response("Erro interno ao registrar a assinatura.", status_code=500)


@router.get("/inspectors/me/signature")
@require_any_permission(QUALITY_LABELS_READ_PERMISSIONS)
def get_my_signature():
    try:
        service = build_quality_labels_inspector_service()
        png = service.read_signature(user_id=_current_user_id())
        if png is None:
            return not_found_response("Assinatura não encontrada.")
        return Response(content=png, media_type="image/png")
    except Exception as exc:
        log_error(f"Erro ao ler assinatura do inspetor: {exc}")
        return error_response("Erro interno ao ler a assinatura.", status_code=500)


@router.get("/lookup-op/{production_order}", operation_id="lookup_quality_label_op")
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


@router.post("", operation_id="create_quality_label")
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
            inspected_quantity=body.inspectedQuantity,
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


@router.get("", operation_id="list_quality_labels")
@require_any_permission(QUALITY_LABELS_READ_PERMISSIONS)
def list_labels(
    search: Optional[str] = None,
    branches: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    try:
        service = build_quality_labels_service()
        data = service.list_labels(
            search=search,
            branches=_parse_branches(branches),
            limit=limit,
            offset=offset,
        )
        return api_delpi_success(
            data,
            operation_id="list_quality_labels",
            message="Etiquetas de qualidade recuperadas com sucesso.",
        )
    except Exception as exc:
        log_error(f"Erro ao listar etiquetas de qualidade: {exc}")
        return error_response("Erro interno ao listar as etiquetas.", status_code=500)


@router.get("/{label_id}", operation_id="get_quality_label")
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


@router.patch("/{label_id}/active", operation_id="set_quality_label_active")
@require_any_permission(QUALITY_LABELS_WRITE_PERMISSIONS)
def set_label_active(label_id: str, body: Annotated[SetActiveBody, Body(...)]):
    try:
        service = build_quality_labels_service()
        data = service.set_active(
            label_id=label_id,
            is_active=body.isActive,
            actor_user_id=_current_user_id(),
            actor_name=_current_user_name(),
        )
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


@router.get("/{label_id}/certificate", operation_id="get_quality_label_certificate")
@require_any_permission(QUALITY_LABELS_READ_PERMISSIONS)
def get_certificate(label_id: str):
    try:
        service = build_quality_labels_certificate_service()
        data = service.get_or_init(label_id=label_id)
        return api_delpi_success(
            data,
            operation_id="get_quality_label_certificate",
            message="Certificado recuperado com sucesso.",
        )
    except QualityLabelsCertificateError as exc:
        return not_found_response(str(exc))
    except Exception as exc:
        log_error(f"Erro ao buscar certificado de qualidade: {exc}")
        return error_response("Erro interno ao buscar o certificado.", status_code=500)


@router.put("/{label_id}/certificate", operation_id="save_quality_label_certificate")
@require_any_permission(QUALITY_LABELS_WRITE_PERMISSIONS)
def save_certificate(label_id: str, body: Annotated[CertificateBody, Body(...)]):
    try:
        service = build_quality_labels_certificate_service()
        payload: dict[str, Any] = body.model_dump()
        payload["items"] = [item for item in payload.get("items", [])]
        data = service.save(
            label_id=label_id,
            data=payload,
            issue=bool(body.issue),
            actor_user_id=_current_user_id(),
            actor_name=_current_user_name(),
        )
        return api_delpi_success(
            data,
            operation_id="save_quality_label_certificate",
            message="Certificado salvo com sucesso.",
        )
    except QualityLabelsCertificateError as exc:
        return not_found_response(str(exc))
    except Exception as exc:
        log_error(f"Erro ao salvar certificado de qualidade: {exc}")
        return error_response("Erro interno ao salvar o certificado.", status_code=500)


@router.get("/{label_id}/certificate/pdf")
@require_any_permission(QUALITY_LABELS_READ_PERMISSIONS)
def get_certificate_pdf(label_id: str):
    try:
        service = build_quality_labels_certificate_service()
        pdf = service.read_pdf(label_id=label_id)
        if pdf is None:
            return not_found_response("Certificado não encontrado.")
        return Response(
            content=pdf,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'inline; filename="certificado-{label_id}.pdf"'
            },
        )
    except Exception as exc:
        log_error(f"Erro ao gerar PDF do certificado: {exc}")
        return error_response("Erro interno ao gerar o PDF.", status_code=500)


@router.delete("/{label_id}", operation_id="delete_quality_label")
@require_any_permission(QUALITY_LABELS_WRITE_PERMISSIONS)
def delete_label(label_id: str):
    try:
        service = build_quality_labels_service()
        deleted = service.delete_label(
            label_id=label_id,
            actor_user_id=_current_user_id(),
            actor_name=_current_user_name(),
        )
        if not deleted:
            return not_found_response("Etiqueta não encontrada.")
        return api_delpi_success(
            {"id": label_id, "deleted": True},
            operation_id="delete_quality_label",
            message="Etiqueta excluída com sucesso.",
        )
    except Exception as exc:
        log_error(f"Erro ao excluir etiqueta de qualidade: {exc}")
        return error_response("Erro interno ao excluir a etiqueta.", status_code=500)

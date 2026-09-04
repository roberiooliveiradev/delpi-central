
from __future__ import annotations

from fastapi import APIRouter, File, Form, Query, UploadFile
from app.interface.http.pagination_query import (
    PAGE_SIZE_QUERY,
)

from fastapi.responses import FileResponse, RedirectResponse, StreamingResponse
from pydantic import BaseModel, Field

from delpi_auth.authorization import require_any_permission

from app.application.security.api_delpi_permissions import (
    PLANEJAMENTO_ORCAMENTARIO_ACCESS_PERMISSIONS,
    PLANEJAMENTO_ORCAMENTARIO_ADMIN_PERMISSIONS,
    PLANEJAMENTO_ORCAMENTARIO_CAPEX_APPROVE_PERMISSIONS,
    PLANEJAMENTO_ORCAMENTARIO_CAPEX_CONSOLIDATION_VIEW_PERMISSIONS,
    PLANEJAMENTO_ORCAMENTARIO_CAPEX_EXPORT_PERMISSIONS,
    PLANEJAMENTO_ORCAMENTARIO_CAPEX_SUBMIT_PERMISSIONS,
    PLANEJAMENTO_ORCAMENTARIO_GUIDANCE_MANAGE_PERMISSIONS,
    PLANEJAMENTO_ORCAMENTARIO_GUIDANCE_VIEW_PERMISSIONS,
    PLANEJAMENTO_ORCAMENTARIO_PERSONNEL_APPROVE_PERMISSIONS,
    PLANEJAMENTO_ORCAMENTARIO_PERSONNEL_EDIT_PERMISSIONS,
    PLANEJAMENTO_ORCAMENTARIO_PERSONNEL_SUBMIT_PERMISSIONS,
    PLANEJAMENTO_ORCAMENTARIO_PERSONNEL_VIEW_PERMISSIONS,
    PLANEJAMENTO_ORCAMENTARIO_SCOPES_MANAGE_PERMISSIONS,
)
from app.composition.planejamento_orcamentario_composer import (
    build_budget_planning_use_cases,
    build_budget_responsibility_use_cases,
    build_capex_attachment_use_cases,
    build_capex_category_use_cases,
    build_capex_consolidation_use_cases,
    build_capex_investment_use_cases,
    build_capex_plan_use_cases,
    build_personnel_plan_use_cases,
)
from app.core.responses import error_response
from app.domain.services.planejamento_orcamentario.exceptions import BudgetPlanningError
from app.infrastructure.persistence.plugins.plugin_base_repository import PluginsRepositoryError
from app.interface.http.route_response_helpers import api_delpi_success
from app.interface.http.routes.planejamento_orcamentario.deps import (
    build_actor,
    handle_budget_error,
)
from app.utils.logger import log_error

router = APIRouter(
    prefix="/planejamento-orcamentario",
    tags=["Planejamento Orçamentário"],
)


class ExerciseCreateBody(BaseModel):
    year: int = Field(..., ge=2000, le=2100)
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    preparation_starts_at: str | None = None
    filling_starts_at: str | None = None
    deadline_at: str | None = None
    closed_at: str | None = None


class ExerciseUpdateBody(BaseModel):
    name: str | None = None
    description: str | None = None
    preparation_starts_at: str | None = None
    filling_starts_at: str | None = None
    deadline_at: str | None = None
    closed_at: str | None = None
    status: str | None = None


class ExerciseTransitionBody(BaseModel):
    action: str
    comment: str | None = None


class GuidanceUpdateBody(BaseModel):
    title: str | None = None
    board_message: str | None = None
    sender_name: str | None = None
    sender_role: str | None = None
    objective: str | None = None
    general_guidance: str | None = None
    additional_notes: str | None = None
    premises: list[dict] | None = None
    schedule: list[dict] | None = None


class DocumentMetaBody(BaseModel):
    display_name: str | None = None
    description: str | None = None
    display_order: int | None = None
    external_url: str | None = None


class ScopeCreateBody(BaseModel):
    user_sub: str
    user_name: str | None = None
    user_email: str | None = None
    unit_code: str
    area_code: str | None = None
    cost_center_code: str | None = None
    scope_level: str
    role_in_scope: str = "editor"
    valid_from: str | None = None
    valid_to: str | None = None


class ScopeUpdateBody(BaseModel):
    user_name: str | None = None
    user_email: str | None = None
    unit_code: str | None = None
    area_code: str | None = None
    cost_center_code: str | None = None
    scope_level: str | None = None
    role_in_scope: str | None = None
    valid_from: str | None = None
    valid_to: str | None = None


class CostCenterBody(BaseModel):
    code: str
    name: str
    unit_code: str
    branch: str | None = None
    unit_name: str | None = None
    area_code: str | None = None
    area_name: str | None = None


class CostCenterIconBody(BaseModel):
    branch: str
    code: str
    icon_key: str | None = None


class CostCenterFromErpBody(BaseModel):
    branch: str
    code: str
    unit_id: str
    area_code: str | None = None


class BudgetResponsibilityCreateBody(BaseModel):
    exercise_id: str
    module: str = "capex"
    user_sub: str
    user_name_snapshot: str | None = None
    user_email_snapshot: str | None = None
    unit_id: str
    area_id: str | None = None
    cost_center_id: str
    responsibility_type: str
    valid_from: str | None = None
    valid_until: str | None = None


class BudgetResponsibilityUpdateBody(BaseModel):
    responsibility_type: str | None = None
    valid_from: str | None = None
    valid_until: str | None = None
    user_name_snapshot: str | None = None
    user_email_snapshot: str | None = None


class BudgetResponsibilityDeactivateBody(BaseModel):
    reason: str | None = None


class CapexCategoryCreateBody(BaseModel):
    code: str
    name: str
    description: str | None = None
    display_order: int | None = 0
    icon_key: str | None = None


class CapexCategoryUpdateBody(BaseModel):
    code: str | None = None
    name: str | None = None
    description: str | None = None
    display_order: int | None = None
    icon_key: str | None = None


class CapexCategoryDeactivateBody(BaseModel):
    reason: str | None = None


class CapexInvestmentCreateBody(BaseModel):
    exercise_id: str
    cost_center_id: str
    unit_id: str | None = None
    area_id: str | None = None
    category_id: str | None = None
    accounting_account_code: str | None = None
    description: str | None = None
    justification: str | None = None
    probable_supplier_name: str | None = None
    probable_supplier_code: str | None = None
    estimated_amount: str | float | int | None = None
    currency: str | None = "BRL"
    required_date: str | None = None
    priority: str | None = None
    origin: str | None = None
    classification: str | None = None
    shift: str | None = None
    application: str | None = None
    observations: str | None = None


class CapexInvestmentUpdateBody(BaseModel):
    version: int
    cost_center_id: str | None = None
    category_id: str | None = None
    accounting_account_code: str | None = None
    description: str | None = None
    justification: str | None = None
    probable_supplier_name: str | None = None
    probable_supplier_code: str | None = None
    estimated_amount: str | float | int | None = None
    currency: str | None = None
    required_date: str | None = None
    priority: str | None = None
    origin: str | None = None
    classification: str | None = None
    shift: str | None = None
    application: str | None = None
    observations: str | None = None


class CapexInvestmentArchiveBody(BaseModel):
    reason: str | None = None


class CapexPlanResolveBody(BaseModel):
    exercise_id: str
    cost_center_id: str
    unit_id: str | None = None


class CapexPlanSubmitBody(BaseModel):
    version: int = Field(..., ge=1)
    comment: str | None = None


class CapexPlanDecisionBody(BaseModel):
    version: int = Field(..., ge=1)
    comment: str | None = None


class CapexPlanRejectBody(BaseModel):
    version: int = Field(..., ge=1)
    comment: str = Field(..., min_length=1)


class CapexPlanRequestChangesBody(BaseModel):
    version: int = Field(..., ge=1)
    comment: str = Field(..., min_length=1)


class PersonnelPlanResolveBody(BaseModel):
    exercise_id: str
    unit_id: str
    cost_center_id: str


class PersonnelLineCreateBody(BaseModel):
    position_name: str
    headcount_dec_2025: int | None = None
    headcount_oct_2026: int | None = None
    headcount_forecast: int | None = None
    headcount_dec_2027: int | None = None
    observations: str | None = None


class PersonnelLineUpdateBody(BaseModel):
    version: int = Field(..., ge=1)
    position_name: str | None = None
    headcount_dec_2025: int | None = None
    headcount_oct_2026: int | None = None
    headcount_forecast: int | None = None
    headcount_dec_2027: int | None = None
    observations: str | None = None


class PersonnelPlanSubmitBody(BaseModel):
    version: int = Field(..., ge=1)
    comment: str | None = None


class PersonnelPlanDecisionBody(BaseModel):
    version: int = Field(..., ge=1)
    comment: str | None = None


class PersonnelPlanRejectBody(BaseModel):
    version: int = Field(..., ge=1)
    comment: str = Field(..., min_length=1)


class PersonnelPlanRequestChangesBody(BaseModel):
    version: int = Field(..., ge=1)
    comment: str = Field(..., min_length=1)


def _run(fn):
    try:
        return fn()
    except BudgetPlanningError as exc:
        return handle_budget_error(exc)
    except PluginsRepositoryError as exc:
        return error_response(str(exc), status_code=422, code="budget_persistence_error")
    except Exception as exc:
        log_error(f"planejamento-orcamentario error: {exc}")
        return error_response("Erro interno no Planejamento Orçamentário.", status_code=500)


# -------- user --------
@router.get("/context", operation_id="get_planejamento_orcamentario_context")
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_ACCESS_PERMISSIONS)
def get_context():
    return _run(lambda: api_delpi_success(
        build_budget_planning_use_cases().get_context(build_actor()),
        operation_id="get_planejamento_orcamentario_context",
        message="Contexto do planejamento orçamentário.",
    ))


@router.get("/guidance/current", operation_id="get_planejamento_orcamentario_guidance_current")
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_GUIDANCE_VIEW_PERMISSIONS)
def get_guidance_current():
    return _run(lambda: api_delpi_success(
        build_budget_planning_use_cases().get_current_guidance_for_user(build_actor()),
        operation_id="get_planejamento_orcamentario_guidance_current",
        message="Orientações vigentes.",
    ))


@router.post(
    "/guidance/current/acknowledge",
    operation_id="acknowledge_planejamento_orcamentario_guidance",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_ACCESS_PERMISSIONS)
def acknowledge_guidance():
    return _run(lambda: api_delpi_success(
        build_budget_planning_use_cases().acknowledge_current_guidance(build_actor()),
        operation_id="acknowledge_planejamento_orcamentario_guidance",
        message="Leitura confirmada.",
    ))


@router.get(
    "/guidance/current/documents",
    operation_id="list_planejamento_orcamentario_guidance_documents",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_GUIDANCE_VIEW_PERMISSIONS)
def list_guidance_documents():
    return _run(lambda: api_delpi_success(
        {"items": build_budget_planning_use_cases().list_current_documents(build_actor())},
        operation_id="list_planejamento_orcamentario_guidance_documents",
        message="Documentos de apoio.",
    ))


@router.get(
    "/documents/{document_id}/download",
    operation_id="download_planejamento_orcamentario_document",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_GUIDANCE_VIEW_PERMISSIONS)
def download_document(document_id: str):
    try:
        result = build_budget_planning_use_cases().resolve_download(build_actor(), document_id)
        if result["kind"] == "external":
            return RedirectResponse(url=str(result["url"]), status_code=302)
        return FileResponse(
            path=str(result["path"]),
            media_type=result["mime_type"],
            filename=result["filename"],
        )
    except BudgetPlanningError as exc:
        return handle_budget_error(exc)
    except Exception as exc:
        log_error(f"download document error: {exc}")
        return error_response("Erro ao baixar documento.", status_code=500)


# -------- admin exercises --------
@router.get("/admin/exercises", operation_id="list_planejamento_orcamentario_admin_exercises")
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_ADMIN_PERMISSIONS)
def admin_list_exercises():
    return _run(lambda: api_delpi_success(
        {"items": build_budget_planning_use_cases().list_exercises()},
        operation_id="list_planejamento_orcamentario_admin_exercises",
        message="Exercícios listados.",
    ))


@router.post("/admin/exercises", operation_id="create_planejamento_orcamentario_admin_exercise")
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_ADMIN_PERMISSIONS)
def admin_create_exercise(body: ExerciseCreateBody):
    return _run(lambda: api_delpi_success(
        build_budget_planning_use_cases().create_exercise(build_actor(), body.model_dump()),
        operation_id="create_planejamento_orcamentario_admin_exercise",
        message="Exercício criado.",
    ))


@router.get("/admin/exercises/{exercise_id}", operation_id="get_planejamento_orcamentario_admin_exercise")
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_ADMIN_PERMISSIONS)
def admin_get_exercise(exercise_id: str):
    return _run(lambda: api_delpi_success(
        build_budget_planning_use_cases().get_exercise(exercise_id),
        operation_id="get_planejamento_orcamentario_admin_exercise",
        message="Exercício.",
    ))


@router.put("/admin/exercises/{exercise_id}", operation_id="update_planejamento_orcamentario_admin_exercise")
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_ADMIN_PERMISSIONS)
def admin_update_exercise(exercise_id: str, body: ExerciseUpdateBody):
    return _run(lambda: api_delpi_success(
        build_budget_planning_use_cases().update_exercise(
            build_actor(), exercise_id, body.model_dump(exclude_unset=True)
        ),
        operation_id="update_planejamento_orcamentario_admin_exercise",
        message="Exercício atualizado.",
    ))


@router.post(
    "/admin/exercises/{exercise_id}/transitions",
    operation_id="transition_planejamento_orcamentario_admin_exercise",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_ADMIN_PERMISSIONS)
def admin_transition_exercise(exercise_id: str, body: ExerciseTransitionBody):
    return _run(lambda: api_delpi_success(
        build_budget_planning_use_cases().transition_exercise(
            build_actor(), exercise_id, action=body.action, comment=body.comment
        ),
        operation_id="transition_planejamento_orcamentario_admin_exercise",
        message="Transição aplicada.",
    ))


# -------- admin guidance --------
@router.get(
    "/admin/exercises/{exercise_id}/guidance",
    operation_id="get_planejamento_orcamentario_admin_guidance",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_GUIDANCE_MANAGE_PERMISSIONS)
def admin_get_guidance(exercise_id: str):
    uc = build_budget_planning_use_cases()
    return _run(lambda: api_delpi_success(
        {
            "draft": uc.get_or_create_guidance_draft(build_actor(), exercise_id),
            "published_versions": uc.list_guidance_versions(exercise_id),
        },
        operation_id="get_planejamento_orcamentario_admin_guidance",
        message="Orientações administrativas.",
    ))


@router.post(
    "/admin/exercises/{exercise_id}/guidance",
    operation_id="create_planejamento_orcamentario_admin_guidance_draft",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_GUIDANCE_MANAGE_PERMISSIONS)
def admin_create_guidance(exercise_id: str):
    return _run(lambda: api_delpi_success(
        build_budget_planning_use_cases().get_or_create_guidance_draft(build_actor(), exercise_id),
        operation_id="create_planejamento_orcamentario_admin_guidance_draft",
        message="Rascunho de orientações.",
    ))


@router.put(
    "/admin/guidance/{guidance_id}",
    operation_id="update_planejamento_orcamentario_admin_guidance",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_GUIDANCE_MANAGE_PERMISSIONS)
def admin_update_guidance(guidance_id: str, body: GuidanceUpdateBody):
    return _run(lambda: api_delpi_success(
        build_budget_planning_use_cases().update_guidance_draft(
            build_actor(), guidance_id, body.model_dump(exclude_unset=True)
        ),
        operation_id="update_planejamento_orcamentario_admin_guidance",
        message="Rascunho atualizado.",
    ))


@router.post(
    "/admin/guidance/{guidance_id}/publish",
    operation_id="publish_planejamento_orcamentario_admin_guidance",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_GUIDANCE_MANAGE_PERMISSIONS)
def admin_publish_guidance(guidance_id: str):
    return _run(lambda: api_delpi_success(
        build_budget_planning_use_cases().publish_guidance(build_actor(), guidance_id),
        operation_id="publish_planejamento_orcamentario_admin_guidance",
        message="Orientações publicadas.",
    ))


@router.get(
    "/admin/guidance/{guidance_id}/documents",
    operation_id="list_planejamento_orcamentario_admin_documents",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_GUIDANCE_MANAGE_PERMISSIONS)
def admin_list_documents(guidance_id: str):
    return _run(lambda: api_delpi_success(
        {"items": build_budget_planning_use_cases().list_admin_documents(guidance_id)},
        operation_id="list_planejamento_orcamentario_admin_documents",
        message="Documentos das orientações.",
    ))


@router.post(
    "/admin/guidance/{guidance_id}/documents",
    operation_id="upload_planejamento_orcamentario_admin_document",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_GUIDANCE_MANAGE_PERMISSIONS)
async def admin_upload_document(
    guidance_id: str,
    file: UploadFile | None = File(None),
    display_name: str = Form(""),
    description: str = Form(""),
    display_order: int = Form(0),
    document_kind: str = Form(""),
    external_url: str = Form(""),
    exercise_id: str = Form(...),
):
    actor = build_actor()
    uc = build_budget_planning_use_cases()

    async def _inner():
        if external_url.strip():
            return uc.upload_document(
                actor,
                exercise_id=exercise_id,
                guidance_id=guidance_id,
                display_name=display_name or external_url,
                original_name=display_name or "link",
                content=b"",
                mime_type=None,
                description=description or None,
                display_order=display_order,
                external_url=external_url.strip(),
            )
        if file is None:
            raise BudgetPlanningError(
                "Arquivo ou URL externa é obrigatório.",
                code="budget_document_type_not_allowed",
                status_code=422,
            )
        content = await file.read()
        return uc.upload_document(
            actor,
            exercise_id=exercise_id,
            guidance_id=guidance_id,
            display_name=display_name or (file.filename or "documento"),
            original_name=file.filename or "documento",
            content=content,
            mime_type=file.content_type,
            description=description or None,
            display_order=display_order,
            document_kind=document_kind.strip() or None,
        )

    try:
        data = await _inner()
        return api_delpi_success(
            data,
            operation_id="upload_planejamento_orcamentario_admin_document",
            message="Documento registrado.",
        )
    except BudgetPlanningError as exc:
        return handle_budget_error(exc)
    except Exception as exc:
        log_error(f"upload document error: {exc}")
        return error_response("Erro ao enviar documento.", status_code=500)


@router.put(
    "/admin/documents/{document_id}",
    operation_id="update_planejamento_orcamentario_admin_document",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_GUIDANCE_MANAGE_PERMISSIONS)
def admin_update_document(document_id: str, body: DocumentMetaBody):
    return _run(lambda: api_delpi_success(
        build_budget_planning_use_cases().update_document(
            build_actor(), document_id, body.model_dump(exclude_unset=True)
        ),
        operation_id="update_planejamento_orcamentario_admin_document",
        message="Documento atualizado.",
    ))


@router.post(
    "/admin/documents/{document_id}/archive",
    operation_id="archive_planejamento_orcamentario_admin_document",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_GUIDANCE_MANAGE_PERMISSIONS)
def admin_archive_document(document_id: str):
    return _run(lambda: api_delpi_success(
        build_budget_planning_use_cases().archive_document(build_actor(), document_id),
        operation_id="archive_planejamento_orcamentario_admin_document",
        message="Documento arquivado.",
    ))


# -------- admin scopes --------
@router.get("/admin/scopes", operation_id="list_planejamento_orcamentario_admin_scopes")
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_SCOPES_MANAGE_PERMISSIONS)
def admin_list_scopes():
    uc = build_budget_planning_use_cases()
    return _run(lambda: api_delpi_success(
        {"items": uc.list_scopes(), "catalog": uc.list_org_catalog()},
        operation_id="list_planejamento_orcamentario_admin_scopes",
        message="Escopos e catálogo.",
    ))


@router.post("/admin/scopes", operation_id="create_planejamento_orcamentario_admin_scope")
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_SCOPES_MANAGE_PERMISSIONS)
def admin_create_scope(body: ScopeCreateBody):
    return _run(lambda: api_delpi_success(
        build_budget_planning_use_cases().create_scope(build_actor(), body.model_dump()),
        operation_id="create_planejamento_orcamentario_admin_scope",
        message="Escopo criado.",
    ))


@router.put("/admin/scopes/{scope_id}", operation_id="update_planejamento_orcamentario_admin_scope")
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_SCOPES_MANAGE_PERMISSIONS)
def admin_update_scope(scope_id: str, body: ScopeUpdateBody):
    return _run(lambda: api_delpi_success(
        build_budget_planning_use_cases().update_scope(
            build_actor(), scope_id, body.model_dump(exclude_unset=True)
        ),
        operation_id="update_planejamento_orcamentario_admin_scope",
        message="Escopo atualizado.",
    ))


@router.post(
    "/admin/scopes/{scope_id}/deactivate",
    operation_id="deactivate_planejamento_orcamentario_admin_scope",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_SCOPES_MANAGE_PERMISSIONS)
def admin_deactivate_scope(scope_id: str):
    return _run(lambda: api_delpi_success(
        build_budget_planning_use_cases().deactivate_scope(build_actor(), scope_id),
        operation_id="deactivate_planejamento_orcamentario_admin_scope",
        message="Escopo desativado.",
    ))


@router.post(
    "/admin/org/cost-centers",
    operation_id="upsert_planejamento_orcamentario_admin_cost_center",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_SCOPES_MANAGE_PERMISSIONS)
def admin_upsert_cost_center(body: CostCenterBody):
    return _run(lambda: api_delpi_success(
        build_budget_planning_use_cases().create_org_cost_center(build_actor(), body.model_dump()),
        operation_id="upsert_planejamento_orcamentario_admin_cost_center",
        message="Centro de custo do catálogo interno.",
    ))


@router.post(
    "/admin/org/cost-centers/from-erp",
    operation_id="create_planejamento_orcamentario_admin_cost_center_from_erp",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_SCOPES_MANAGE_PERMISSIONS)
def admin_create_cost_center_from_erp(body: CostCenterFromErpBody):
    return _run(lambda: api_delpi_success(
        build_budget_planning_use_cases().create_org_cost_center_from_erp(
            build_actor(), body.model_dump()
        ),
        operation_id="create_planejamento_orcamentario_admin_cost_center_from_erp",
        message="Centro de custo cadastrado a partir do ERP.",
    ))


@router.patch(
    "/admin/org/cost-centers/icon",
    operation_id="update_planejamento_orcamentario_admin_cost_center_icon",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_SCOPES_MANAGE_PERMISSIONS)
def admin_update_cost_center_icon(body: CostCenterIconBody):
    return _run(lambda: api_delpi_success(
        build_budget_planning_use_cases().update_org_cost_center_icon(
            build_actor(), body.model_dump()
        ),
        operation_id="update_planejamento_orcamentario_admin_cost_center_icon",
        message="Ícone do centro de custo atualizado.",
    ))


@router.get(
    "/org/erp-cost-centers",
    operation_id="list_planejamento_orcamentario_org_erp_cost_centers",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_ACCESS_PERMISSIONS)
def list_erp_cost_centers(branch: str = Query(..., description="Filial 01 ou 02")):
    return _run(lambda: api_delpi_success(
        {
            "items": build_budget_planning_use_cases().list_erp_cost_centers(branch=branch),
            "branch": branch,
        },
        operation_id="list_planejamento_orcamentario_org_erp_cost_centers",
        message="Centros de custo ERP por filial.",
    ))


# -------- admin budget responsibilities (Fase 2A.1) --------
@router.get(
    "/admin/budget-responsibilities",
    operation_id="list_planejamento_orcamentario_admin_budget_responsibilities",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_SCOPES_MANAGE_PERMISSIONS)
def admin_list_budget_responsibilities(
    exercise_id: str | None = None,
    module: str | None = None,
    user_sub: str | None = None,
    unit_id: str | None = None,
    area_id: str | None = None,
    cost_center_id: str | None = None,
    responsibility_type: str | None = None,
    is_active: bool | None = None,
    page: int = 1,
    page_size: int = 50,
):
    return _run(lambda: api_delpi_success(
        build_budget_responsibility_use_cases().list_responsibilities(
            build_actor(),
            exercise_id=exercise_id,
            module=module,
            user_sub=user_sub,
            unit_id=unit_id,
            area_id=area_id,
            cost_center_id=cost_center_id,
            responsibility_type=responsibility_type,
            is_active=is_active,
            page=page,
            page_size=page_size,
        ),
        operation_id="list_planejamento_orcamentario_admin_budget_responsibilities",
        message="Responsabilidades orçamentárias.",
    ))


@router.post(
    "/admin/budget-responsibilities",
    operation_id="create_planejamento_orcamentario_admin_budget_responsibility",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_SCOPES_MANAGE_PERMISSIONS)
def admin_create_budget_responsibility(body: BudgetResponsibilityCreateBody):
    return _run(lambda: api_delpi_success(
        build_budget_responsibility_use_cases().create_responsibility(
            build_actor(), body.model_dump()
        ),
        operation_id="create_planejamento_orcamentario_admin_budget_responsibility",
        message="Responsabilidade orçamentária criada.",
    ))


@router.get(
    "/admin/budget-responsibilities/{responsibility_id}",
    operation_id="get_planejamento_orcamentario_admin_budget_responsibility",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_SCOPES_MANAGE_PERMISSIONS)
def admin_get_budget_responsibility(responsibility_id: str):
    return _run(lambda: api_delpi_success(
        build_budget_responsibility_use_cases().get_responsibility(
            build_actor(), responsibility_id
        ),
        operation_id="get_planejamento_orcamentario_admin_budget_responsibility",
        message="Responsabilidade orçamentária.",
    ))


@router.put(
    "/admin/budget-responsibilities/{responsibility_id}",
    operation_id="update_planejamento_orcamentario_admin_budget_responsibility",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_SCOPES_MANAGE_PERMISSIONS)
def admin_update_budget_responsibility(
    responsibility_id: str, body: BudgetResponsibilityUpdateBody
):
    return _run(lambda: api_delpi_success(
        build_budget_responsibility_use_cases().update_responsibility(
            build_actor(), responsibility_id, body.model_dump(exclude_unset=True)
        ),
        operation_id="update_planejamento_orcamentario_admin_budget_responsibility",
        message="Responsabilidade orçamentária atualizada.",
    ))


@router.post(
    "/admin/budget-responsibilities/{responsibility_id}/deactivate",
    operation_id="deactivate_planejamento_orcamentario_admin_budget_responsibility",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_SCOPES_MANAGE_PERMISSIONS)
def admin_deactivate_budget_responsibility(
    responsibility_id: str, body: BudgetResponsibilityDeactivateBody | None = None
):
    reason = body.reason if body else None
    return _run(lambda: api_delpi_success(
        build_budget_responsibility_use_cases().deactivate_responsibility(
            build_actor(), responsibility_id, reason=reason
        ),
        operation_id="deactivate_planejamento_orcamentario_admin_budget_responsibility",
        message="Responsabilidade orçamentária desativada.",
    ))


@router.post(
    "/admin/budget-responsibilities/{responsibility_id}/reactivate",
    operation_id="reactivate_planejamento_orcamentario_admin_budget_responsibility",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_SCOPES_MANAGE_PERMISSIONS)
def admin_reactivate_budget_responsibility(responsibility_id: str):
    return _run(lambda: api_delpi_success(
        build_budget_responsibility_use_cases().reactivate_responsibility(
            build_actor(), responsibility_id
        ),
        operation_id="reactivate_planejamento_orcamentario_admin_budget_responsibility",
        message="Responsabilidade orçamentária reativada.",
    ))


@router.get(
    "/capex/my-responsibilities",
    operation_id="list_planejamento_orcamentario_capex_my_responsibilities",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_ACCESS_PERMISSIONS)
def list_capex_my_responsibilities(
    exercise_id: str | None = None,
    module: str | None = "capex",
):
    """Lista vínculos do usuário autenticado (JWT). Ignora qualquer user_sub de query."""
    return _run(lambda: api_delpi_success(
        build_budget_responsibility_use_cases().list_my_responsibilities(
            build_actor(),
            module=module,
            exercise_id=exercise_id,
        ),
        operation_id="list_planejamento_orcamentario_capex_my_responsibilities",
        message="Minhas responsabilidades CAPEX.",
    ))


# -------- capex categories (Fase 2A.3) --------
@router.get(
    "/capex/categories",
    operation_id="list_planejamento_orcamentario_capex_categories",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_ACCESS_PERMISSIONS)
def list_capex_categories():
    return _run(lambda: api_delpi_success(
        build_capex_category_use_cases().list_active_categories(build_actor()),
        operation_id="list_planejamento_orcamentario_capex_categories",
        message="Categorias CAPEX ativas.",
    ))


@router.get(
    "/admin/capex/categories",
    operation_id="list_planejamento_orcamentario_admin_capex_categories",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_SCOPES_MANAGE_PERMISSIONS)
def admin_list_capex_categories(
    is_active: bool | None = None,
    q: str | None = None,
):
    return _run(lambda: api_delpi_success(
        build_capex_category_use_cases().list_admin_categories(
            build_actor(),
            is_active=is_active,
            q=q,
        ),
        operation_id="list_planejamento_orcamentario_admin_capex_categories",
        message="Catálogo administrativo de categorias CAPEX.",
    ))


@router.post(
    "/admin/capex/categories",
    operation_id="create_planejamento_orcamentario_admin_capex_category",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_SCOPES_MANAGE_PERMISSIONS)
def admin_create_capex_category(body: CapexCategoryCreateBody):
    return _run(lambda: api_delpi_success(
        build_capex_category_use_cases().create_category(
            build_actor(), body.model_dump()
        ),
        operation_id="create_planejamento_orcamentario_admin_capex_category",
        message="Categoria CAPEX criada.",
    ))


@router.put(
    "/admin/capex/categories/{category_id}",
    operation_id="update_planejamento_orcamentario_admin_capex_category",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_SCOPES_MANAGE_PERMISSIONS)
def admin_update_capex_category(category_id: str, body: CapexCategoryUpdateBody):
    return _run(lambda: api_delpi_success(
        build_capex_category_use_cases().update_category(
            build_actor(), category_id, body.model_dump(exclude_unset=True)
        ),
        operation_id="update_planejamento_orcamentario_admin_capex_category",
        message="Categoria CAPEX atualizada.",
    ))


@router.post(
    "/admin/capex/categories/{category_id}/deactivate",
    operation_id="deactivate_planejamento_orcamentario_admin_capex_category",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_SCOPES_MANAGE_PERMISSIONS)
def admin_deactivate_capex_category(
    category_id: str, body: CapexCategoryDeactivateBody | None = None
):
    reason = body.reason if body else None
    return _run(lambda: api_delpi_success(
        build_capex_category_use_cases().deactivate_category(
            build_actor(), category_id, reason=reason
        ),
        operation_id="deactivate_planejamento_orcamentario_admin_capex_category",
        message="Categoria CAPEX desativada.",
    ))


@router.post(
    "/admin/capex/categories/{category_id}/reactivate",
    operation_id="reactivate_planejamento_orcamentario_admin_capex_category",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_SCOPES_MANAGE_PERMISSIONS)
def admin_reactivate_capex_category(category_id: str):
    return _run(lambda: api_delpi_success(
        build_capex_category_use_cases().reactivate_category(
            build_actor(), category_id
        ),
        operation_id="reactivate_planejamento_orcamentario_admin_capex_category",
        message="Categoria CAPEX reativada.",
    ))


@router.post(
    "/admin/capex/categories/{category_id}/icon-image",
    operation_id="upload_planejamento_orcamentario_admin_capex_category_icon_image",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_SCOPES_MANAGE_PERMISSIONS)
async def admin_upload_capex_category_icon_image(
    category_id: str,
    file: UploadFile = File(...),
):
    try:
        content = await file.read()
        data = build_capex_category_use_cases().upload_icon_image(
            build_actor(),
            category_id,
            original_name=file.filename or "icon.png",
            content=content,
            mime_type=file.content_type,
        )
        return api_delpi_success(
            data,
            operation_id="upload_planejamento_orcamentario_admin_capex_category_icon_image",
            message="Imagem do ícone da categoria atualizada.",
        )
    except BudgetPlanningError as exc:
        return handle_budget_error(exc)
    except Exception as exc:
        log_error(f"upload category icon error: {type(exc).__name__}")
        return error_response("Erro ao enviar imagem do ícone.", status_code=500)


@router.delete(
    "/admin/capex/categories/{category_id}/icon-image",
    operation_id="clear_planejamento_orcamentario_admin_capex_category_icon_image",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_SCOPES_MANAGE_PERMISSIONS)
def admin_clear_capex_category_icon_image(category_id: str):
    return _run(lambda: api_delpi_success(
        build_capex_category_use_cases().clear_icon_image(build_actor(), category_id),
        operation_id="clear_planejamento_orcamentario_admin_capex_category_icon_image",
        message="Imagem do ícone removida.",
    ))


@router.get(
    "/capex/categories/{category_id}/icon-image",
    operation_id="get_planejamento_orcamentario_capex_category_icon_image",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_ACCESS_PERMISSIONS)
def get_capex_category_icon_image(category_id: str):
    try:
        result = build_capex_category_use_cases().resolve_icon_image(
            build_actor(), category_id
        )
        return FileResponse(
            path=str(result["path"]),
            media_type=result["mime_type"],
            filename=result["filename"],
        )
    except BudgetPlanningError as exc:
        return handle_budget_error(exc)
    except Exception as exc:
        log_error(f"get category icon error: {type(exc).__name__}")
        return error_response("Erro ao obter imagem do ícone.", status_code=500)


# -------- capex investments (Fase 2B.1) --------
@router.get(
    "/capex/investments",
    operation_id="list_planejamento_orcamentario_capex_investments",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_ACCESS_PERMISSIONS)
def list_capex_investments(
    exercise_id: str | None = None,
    unit_id: str | None = None,
    cost_center_id: str | None = None,
    category_id: str | None = None,
    priority: str | None = None,
    origin: str | None = None,
    status: str | None = None,
    q: str | None = None,
    page: int = 1,
    page_size: int = 50,
):
    return _run(lambda: api_delpi_success(
        build_capex_investment_use_cases().list_investments(
            build_actor(),
            exercise_id=exercise_id,
            unit_id=unit_id,
            cost_center_id=cost_center_id,
            category_id=category_id,
            priority=priority,
            origin=origin,
            status=status,
            q=q,
            page=page,
            page_size=page_size,
        ),
        operation_id="list_planejamento_orcamentario_capex_investments",
        message="Investimentos CAPEX.",
    ))


@router.post(
    "/capex/investments",
    operation_id="create_planejamento_orcamentario_capex_investment",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_ACCESS_PERMISSIONS)
def create_capex_investment(body: CapexInvestmentCreateBody):
    return _run(lambda: api_delpi_success(
        build_capex_investment_use_cases().create_investment(
            build_actor(), body.model_dump()
        ),
        operation_id="create_planejamento_orcamentario_capex_investment",
        message="Investimento CAPEX criado.",
    ))


@router.get(
    "/capex/investments/{investment_id}",
    operation_id="get_planejamento_orcamentario_capex_investment",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_ACCESS_PERMISSIONS)
def get_capex_investment(investment_id: str):
    return _run(lambda: api_delpi_success(
        build_capex_investment_use_cases().get_investment(
            build_actor(), investment_id
        ),
        operation_id="get_planejamento_orcamentario_capex_investment",
        message="Investimento CAPEX.",
    ))


@router.put(
    "/capex/investments/{investment_id}",
    operation_id="update_planejamento_orcamentario_capex_investment",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_ACCESS_PERMISSIONS)
def update_capex_investment(investment_id: str, body: CapexInvestmentUpdateBody):
    return _run(lambda: api_delpi_success(
        build_capex_investment_use_cases().update_investment(
            build_actor(), investment_id, body.model_dump(exclude_unset=True)
        ),
        operation_id="update_planejamento_orcamentario_capex_investment",
        message="Investimento CAPEX atualizado.",
    ))


@router.post(
    "/capex/investments/{investment_id}/archive",
    operation_id="archive_planejamento_orcamentario_capex_investment",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_ACCESS_PERMISSIONS)
def archive_capex_investment(
    investment_id: str, body: CapexInvestmentArchiveBody | None = None
):
    reason = body.reason if body else None
    return _run(lambda: api_delpi_success(
        build_capex_investment_use_cases().archive_investment(
            build_actor(), investment_id, reason=reason
        ),
        operation_id="archive_planejamento_orcamentario_capex_investment",
        message="Investimento CAPEX arquivado.",
    ))


# -------- capex investment attachments (Fase 2B.3) --------
@router.get(
    "/capex/investments/{investment_id}/attachments",
    operation_id="list_planejamento_orcamentario_capex_investment_attachments",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_ACCESS_PERMISSIONS)
def list_capex_investment_attachments(investment_id: str):
    return _run(lambda: api_delpi_success(
        build_capex_attachment_use_cases().list_attachments(
            build_actor(), investment_id
        ),
        operation_id="list_planejamento_orcamentario_capex_investment_attachments",
        message="Anexos do investimento CAPEX.",
    ))


@router.post(
    "/capex/investments/{investment_id}/attachments",
    operation_id="upload_planejamento_orcamentario_capex_investment_attachment",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_ACCESS_PERMISSIONS)
async def upload_capex_investment_attachment(
    investment_id: str,
    file: UploadFile = File(...),
    attachment_type: str = Form(...),
    display_name: str = Form(...),
    description: str = Form(""),
    idempotency_key: str = Form(""),
):
    actor = build_actor()
    uc = build_capex_attachment_use_cases()
    try:
        content = await file.read()
        data = uc.upload_attachment(
            actor,
            investment_id=investment_id,
            attachment_type=attachment_type,
            display_name=display_name,
            description=description or None,
            original_filename=file.filename or "arquivo",
            content=content,
            mime_type=file.content_type,
            idempotency_key=idempotency_key or None,
        )
        return api_delpi_success(
            data,
            operation_id="upload_planejamento_orcamentario_capex_investment_attachment",
            message="Anexo CAPEX registrado.",
        )
    except BudgetPlanningError as exc:
        return handle_budget_error(exc)
    except Exception as exc:
        log_error(f"upload capex attachment error: {type(exc).__name__}")
        return error_response("Erro ao enviar anexo CAPEX.", status_code=500)


@router.get(
    "/capex/attachments/{attachment_id}/download",
    operation_id="download_planejamento_orcamentario_capex_attachment",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_ACCESS_PERMISSIONS)
def download_capex_attachment(attachment_id: str):
    try:
        result = build_capex_attachment_use_cases().resolve_download(
            build_actor(), attachment_id
        )
        return FileResponse(
            path=str(result["path"]),
            media_type=result["mime_type"],
            filename=result["filename"],
        )
    except BudgetPlanningError as exc:
        return handle_budget_error(exc)
    except Exception as exc:
        log_error(f"download capex attachment error: {type(exc).__name__}")
        return error_response("Erro ao baixar anexo CAPEX.", status_code=500)


@router.post(
    "/capex/attachments/{attachment_id}/archive",
    operation_id="archive_planejamento_orcamentario_capex_attachment",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_ACCESS_PERMISSIONS)
def archive_capex_attachment(attachment_id: str):
    return _run(lambda: api_delpi_success(
        build_capex_attachment_use_cases().archive_attachment(
            build_actor(), attachment_id
        ),
        operation_id="archive_planejamento_orcamentario_capex_attachment",
        message="Anexo CAPEX arquivado.",
    ))


# -------- capex plans / workflow (Fase 2C.1) --------
@router.get(
    "/capex/plans",
    operation_id="list_planejamento_orcamentario_capex_plans",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_ACCESS_PERMISSIONS)
def list_capex_plans(
    exercise_id: str | None = None,
    unit_id: str | None = None,
    area_id: str | None = None,
    cost_center_id: str | None = None,
    status: str | None = None,
    submitted_by: str | None = None,
    page: int = 1,
    page_size: int = 50,
):
    return _run(lambda: api_delpi_success(
        build_capex_plan_use_cases().list_plans(
            build_actor(),
            exercise_id=exercise_id,
            unit_id=unit_id,
            area_id=area_id,
            cost_center_id=cost_center_id,
            status=status,
            submitted_by=submitted_by,
            page=page,
            page_size=page_size,
        ),
        operation_id="list_planejamento_orcamentario_capex_plans",
        message="Planejamentos CAPEX.",
    ))


@router.post(
    "/capex/plans/resolve",
    operation_id="resolve_planejamento_orcamentario_capex_plan",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_ACCESS_PERMISSIONS)
def resolve_capex_plan(body: CapexPlanResolveBody):
    return _run(lambda: api_delpi_success(
        build_capex_plan_use_cases().resolve_plan(
            build_actor(),
            exercise_id=body.exercise_id,
            cost_center_id=body.cost_center_id,
            unit_id=body.unit_id,
        ),
        operation_id="resolve_planejamento_orcamentario_capex_plan",
        message="Planejamento CAPEX resolvido.",
    ))


@router.get(
    "/capex/plans/{plan_id}",
    operation_id="get_planejamento_orcamentario_capex_plan",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_ACCESS_PERMISSIONS)
def get_capex_plan(plan_id: str):
    return _run(lambda: api_delpi_success(
        build_capex_plan_use_cases().get_plan_detail(build_actor(), plan_id),
        operation_id="get_planejamento_orcamentario_capex_plan",
        message="Planejamento CAPEX.",
    ))


@router.post(
    "/capex/plans/{plan_id}/submit",
    operation_id="submit_planejamento_orcamentario_capex_plan",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_CAPEX_SUBMIT_PERMISSIONS)
def submit_capex_plan(plan_id: str, body: CapexPlanSubmitBody):
    return _run(lambda: api_delpi_success(
        build_capex_plan_use_cases().submit_plan(
            build_actor(),
            plan_id,
            version=body.version,
            comment=body.comment,
        ),
        operation_id="submit_planejamento_orcamentario_capex_plan",
        message="Planejamento CAPEX submetido.",
    ))


@router.get(
    "/capex/plans/{plan_id}/history",
    operation_id="list_planejamento_orcamentario_capex_plan_history",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_ACCESS_PERMISSIONS)
def list_capex_plan_history(plan_id: str):
    return _run(lambda: api_delpi_success(
        build_capex_plan_use_cases().list_history(build_actor(), plan_id),
        operation_id="list_planejamento_orcamentario_capex_plan_history",
        message="Histórico do planejamento CAPEX.",
    ))


@router.get(
    "/capex/review-queue",
    operation_id="list_planejamento_orcamentario_capex_review_queue",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_CAPEX_APPROVE_PERMISSIONS)
def list_capex_review_queue(
    exercise_id: str | None = None,
    unit_id: str | None = None,
    area_id: str | None = None,
    cost_center_id: str | None = None,
    status: str | None = None,
    submitted_by: str | None = None,
    page: int = 1,
    page_size: int = 50,
):
    return _run(lambda: api_delpi_success(
        build_capex_plan_use_cases().list_review_queue(
            build_actor(),
            exercise_id=exercise_id,
            unit_id=unit_id,
            area_id=area_id,
            cost_center_id=cost_center_id,
            status=status,
            submitted_by=submitted_by,
            page=page,
            page_size=page_size,
        ),
        operation_id="list_planejamento_orcamentario_capex_review_queue",
        message="Fila de aprovação CAPEX.",
    ))


@router.get(
    "/capex/review/{plan_id}",
    operation_id="get_planejamento_orcamentario_capex_review",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_CAPEX_APPROVE_PERMISSIONS)
def get_capex_review(plan_id: str):
    return _run(lambda: api_delpi_success(
        build_capex_plan_use_cases().get_review_detail(build_actor(), plan_id),
        operation_id="get_planejamento_orcamentario_capex_review",
        message="Revisão do planejamento CAPEX.",
    ))


@router.post(
    "/capex/review/{plan_id}/request-changes",
    operation_id="request_changes_planejamento_orcamentario_capex_plan",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_CAPEX_APPROVE_PERMISSIONS)
def request_changes_capex_plan(plan_id: str, body: CapexPlanRequestChangesBody):
    return _run(lambda: api_delpi_success(
        build_capex_plan_use_cases().request_changes(
            build_actor(),
            plan_id,
            version=body.version,
            comment=body.comment,
        ),
        operation_id="request_changes_planejamento_orcamentario_capex_plan",
        message="Ajustes solicitados no planejamento CAPEX.",
    ))


@router.post(
    "/capex/review/{plan_id}/reject",
    operation_id="reject_planejamento_orcamentario_capex_plan",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_CAPEX_APPROVE_PERMISSIONS)
def reject_capex_plan(plan_id: str, body: CapexPlanRejectBody):
    return _run(lambda: api_delpi_success(
        build_capex_plan_use_cases().reject_plan(
            build_actor(),
            plan_id,
            version=body.version,
            comment=body.comment,
        ),
        operation_id="reject_planejamento_orcamentario_capex_plan",
        message="Planejamento CAPEX reprovado.",
    ))


@router.post(
    "/capex/review/{plan_id}/approve",
    operation_id="approve_planejamento_orcamentario_capex_plan",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_CAPEX_APPROVE_PERMISSIONS)
def approve_capex_plan(plan_id: str, body: CapexPlanDecisionBody):
    return _run(lambda: api_delpi_success(
        build_capex_plan_use_cases().approve_plan(
            build_actor(),
            plan_id,
            version=body.version,
            comment=body.comment,
        ),
        operation_id="approve_planejamento_orcamentario_capex_plan",
        message="Planejamento CAPEX aprovado.",
    ))


@router.post(
    "/capex/review/{plan_id}/investments/{investment_id}/approve",
    operation_id="approve_planejamento_orcamentario_capex_investment",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_CAPEX_APPROVE_PERMISSIONS)
def approve_capex_investment(plan_id: str, investment_id: str, body: CapexPlanDecisionBody):
    return _run(lambda: api_delpi_success(
        build_capex_plan_use_cases().decide_investment(
            build_actor(),
            plan_id,
            investment_id,
            version=body.version,
            action="approve",
            comment=body.comment,
        ),
        operation_id="approve_planejamento_orcamentario_capex_investment",
        message="Investimento CAPEX aprovado.",
    ))


@router.post(
    "/capex/review/{plan_id}/investments/{investment_id}/reject",
    operation_id="reject_planejamento_orcamentario_capex_investment",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_CAPEX_APPROVE_PERMISSIONS)
def reject_capex_investment(plan_id: str, investment_id: str, body: CapexPlanRejectBody):
    return _run(lambda: api_delpi_success(
        build_capex_plan_use_cases().decide_investment(
            build_actor(),
            plan_id,
            investment_id,
            version=body.version,
            action="reject",
            comment=body.comment,
        ),
        operation_id="reject_planejamento_orcamentario_capex_investment",
        message="Investimento CAPEX reprovado.",
    ))


def _consolidation_filter_kwargs(
    *,
    exercise_id: str | None,
    year: int | None,
    unit_id: str | None,
    area_id: str | None,
    cost_center_id: str | None,
    category_id: str | None,
    priority: str | None,
    origin: str | None,
    plan_status: str | None,
    required_date_from: str | None,
    required_date_to: str | None,
) -> dict:
    return {
        "exercise_id": exercise_id,
        "year": year,
        "unit_id": unit_id,
        "area_id": area_id,
        "cost_center_id": cost_center_id,
        "category_id": category_id,
        "priority": priority,
        "origin": origin,
        "plan_status": plan_status,
        "required_date_from": required_date_from,
        "required_date_to": required_date_to,
    }


@router.get(
    "/capex/consolidation/summary",
    operation_id="get_planejamento_orcamentario_capex_consolidation_summary",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_CAPEX_CONSOLIDATION_VIEW_PERMISSIONS)
def get_capex_consolidation_summary(
    exercise_id: str | None = Query(None),
    year: int | None = Query(None),
    unit_id: str | None = Query(None),
    area_id: str | None = Query(None),
    cost_center_id: str | None = Query(None),
    category_id: str | None = Query(None),
    priority: str | None = Query(None),
    origin: str | None = Query(None),
    plan_status: str | None = Query(None),
    required_date_from: str | None = Query(None),
    required_date_to: str | None = Query(None),
):
    return _run(lambda: api_delpi_success(
        build_capex_consolidation_use_cases().get_summary(
            build_actor(),
            **_consolidation_filter_kwargs(
                exercise_id=exercise_id,
                year=year,
                unit_id=unit_id,
                area_id=area_id,
                cost_center_id=cost_center_id,
                category_id=category_id,
                priority=priority,
                origin=origin,
                plan_status=plan_status,
                required_date_from=required_date_from,
                required_date_to=required_date_to,
            ),
        ),
        operation_id="get_planejamento_orcamentario_capex_consolidation_summary",
        message="Resumo consolidado CAPEX.",
    ))


@router.get(
    "/capex/consolidation/by-unit",
    operation_id="list_planejamento_orcamentario_capex_consolidation_by_unit",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_CAPEX_CONSOLIDATION_VIEW_PERMISSIONS)
def list_capex_consolidation_by_unit(
    exercise_id: str | None = Query(None),
    year: int | None = Query(None),
    unit_id: str | None = Query(None),
    area_id: str | None = Query(None),
    cost_center_id: str | None = Query(None),
    category_id: str | None = Query(None),
    priority: str | None = Query(None),
    origin: str | None = Query(None),
    plan_status: str | None = Query(None),
    required_date_from: str | None = Query(None),
    required_date_to: str | None = Query(None),
):
    return _run(lambda: api_delpi_success(
        build_capex_consolidation_use_cases().get_grouping(
            build_actor(),
            group_by="unit",
            **_consolidation_filter_kwargs(
                exercise_id=exercise_id,
                year=year,
                unit_id=unit_id,
                area_id=area_id,
                cost_center_id=cost_center_id,
                category_id=category_id,
                priority=priority,
                origin=origin,
                plan_status=plan_status,
                required_date_from=required_date_from,
                required_date_to=required_date_to,
            ),
        ),
        operation_id="list_planejamento_orcamentario_capex_consolidation_by_unit",
        message="Consolidação CAPEX por unidade.",
    ))


@router.get(
    "/capex/consolidation/by-area",
    operation_id="list_planejamento_orcamentario_capex_consolidation_by_area",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_CAPEX_CONSOLIDATION_VIEW_PERMISSIONS)
def list_capex_consolidation_by_area(
    exercise_id: str | None = Query(None),
    year: int | None = Query(None),
    unit_id: str | None = Query(None),
    area_id: str | None = Query(None),
    cost_center_id: str | None = Query(None),
    category_id: str | None = Query(None),
    priority: str | None = Query(None),
    origin: str | None = Query(None),
    plan_status: str | None = Query(None),
    required_date_from: str | None = Query(None),
    required_date_to: str | None = Query(None),
):
    return _run(lambda: api_delpi_success(
        build_capex_consolidation_use_cases().get_grouping(
            build_actor(),
            group_by="area",
            **_consolidation_filter_kwargs(
                exercise_id=exercise_id,
                year=year,
                unit_id=unit_id,
                area_id=area_id,
                cost_center_id=cost_center_id,
                category_id=category_id,
                priority=priority,
                origin=origin,
                plan_status=plan_status,
                required_date_from=required_date_from,
                required_date_to=required_date_to,
            ),
        ),
        operation_id="list_planejamento_orcamentario_capex_consolidation_by_area",
        message="Consolidação CAPEX por área.",
    ))


@router.get(
    "/capex/consolidation/by-cost-center",
    operation_id="list_planejamento_orcamentario_capex_consolidation_by_cost_center",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_CAPEX_CONSOLIDATION_VIEW_PERMISSIONS)
def list_capex_consolidation_by_cost_center(
    exercise_id: str | None = Query(None),
    year: int | None = Query(None),
    unit_id: str | None = Query(None),
    area_id: str | None = Query(None),
    cost_center_id: str | None = Query(None),
    category_id: str | None = Query(None),
    priority: str | None = Query(None),
    origin: str | None = Query(None),
    plan_status: str | None = Query(None),
    required_date_from: str | None = Query(None),
    required_date_to: str | None = Query(None),
):
    return _run(lambda: api_delpi_success(
        build_capex_consolidation_use_cases().get_grouping(
            build_actor(),
            group_by="cost_center",
            **_consolidation_filter_kwargs(
                exercise_id=exercise_id,
                year=year,
                unit_id=unit_id,
                area_id=area_id,
                cost_center_id=cost_center_id,
                category_id=category_id,
                priority=priority,
                origin=origin,
                plan_status=plan_status,
                required_date_from=required_date_from,
                required_date_to=required_date_to,
            ),
        ),
        operation_id="list_planejamento_orcamentario_capex_consolidation_by_cost_center",
        message="Consolidação CAPEX por centro de custo.",
    ))


@router.get(
    "/capex/consolidation/by-category",
    operation_id="list_planejamento_orcamentario_capex_consolidation_by_category",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_CAPEX_CONSOLIDATION_VIEW_PERMISSIONS)
def list_capex_consolidation_by_category(
    exercise_id: str | None = Query(None),
    year: int | None = Query(None),
    unit_id: str | None = Query(None),
    area_id: str | None = Query(None),
    cost_center_id: str | None = Query(None),
    category_id: str | None = Query(None),
    priority: str | None = Query(None),
    origin: str | None = Query(None),
    plan_status: str | None = Query(None),
    required_date_from: str | None = Query(None),
    required_date_to: str | None = Query(None),
):
    return _run(lambda: api_delpi_success(
        build_capex_consolidation_use_cases().get_grouping(
            build_actor(),
            group_by="category",
            **_consolidation_filter_kwargs(
                exercise_id=exercise_id,
                year=year,
                unit_id=unit_id,
                area_id=area_id,
                cost_center_id=cost_center_id,
                category_id=category_id,
                priority=priority,
                origin=origin,
                plan_status=plan_status,
                required_date_from=required_date_from,
                required_date_to=required_date_to,
            ),
        ),
        operation_id="list_planejamento_orcamentario_capex_consolidation_by_category",
        message="Consolidação CAPEX por categoria.",
    ))


@router.get(
    "/capex/consolidation/by-priority",
    operation_id="list_planejamento_orcamentario_capex_consolidation_by_priority",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_CAPEX_CONSOLIDATION_VIEW_PERMISSIONS)
def list_capex_consolidation_by_priority(
    exercise_id: str | None = Query(None),
    year: int | None = Query(None),
    unit_id: str | None = Query(None),
    area_id: str | None = Query(None),
    cost_center_id: str | None = Query(None),
    category_id: str | None = Query(None),
    priority: str | None = Query(None),
    origin: str | None = Query(None),
    plan_status: str | None = Query(None),
    required_date_from: str | None = Query(None),
    required_date_to: str | None = Query(None),
):
    return _run(lambda: api_delpi_success(
        build_capex_consolidation_use_cases().get_grouping(
            build_actor(),
            group_by="priority",
            **_consolidation_filter_kwargs(
                exercise_id=exercise_id,
                year=year,
                unit_id=unit_id,
                area_id=area_id,
                cost_center_id=cost_center_id,
                category_id=category_id,
                priority=priority,
                origin=origin,
                plan_status=plan_status,
                required_date_from=required_date_from,
                required_date_to=required_date_to,
            ),
        ),
        operation_id="list_planejamento_orcamentario_capex_consolidation_by_priority",
        message="Consolidação CAPEX por prioridade.",
    ))


@router.get(
    "/capex/consolidation/by-origin",
    operation_id="list_planejamento_orcamentario_capex_consolidation_by_origin",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_CAPEX_CONSOLIDATION_VIEW_PERMISSIONS)
def list_capex_consolidation_by_origin(
    exercise_id: str | None = Query(None),
    year: int | None = Query(None),
    unit_id: str | None = Query(None),
    area_id: str | None = Query(None),
    cost_center_id: str | None = Query(None),
    category_id: str | None = Query(None),
    priority: str | None = Query(None),
    origin: str | None = Query(None),
    plan_status: str | None = Query(None),
    required_date_from: str | None = Query(None),
    required_date_to: str | None = Query(None),
):
    return _run(lambda: api_delpi_success(
        build_capex_consolidation_use_cases().get_grouping(
            build_actor(),
            group_by="origin",
            **_consolidation_filter_kwargs(
                exercise_id=exercise_id,
                year=year,
                unit_id=unit_id,
                area_id=area_id,
                cost_center_id=cost_center_id,
                category_id=category_id,
                priority=priority,
                origin=origin,
                plan_status=plan_status,
                required_date_from=required_date_from,
                required_date_to=required_date_to,
            ),
        ),
        operation_id="list_planejamento_orcamentario_capex_consolidation_by_origin",
        message="Consolidação CAPEX por origem.",
    ))


@router.get(
    "/capex/consolidation/by-month",
    operation_id="list_planejamento_orcamentario_capex_consolidation_by_month",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_CAPEX_CONSOLIDATION_VIEW_PERMISSIONS)
def list_capex_consolidation_by_month(
    exercise_id: str | None = Query(None),
    year: int | None = Query(None),
    unit_id: str | None = Query(None),
    area_id: str | None = Query(None),
    cost_center_id: str | None = Query(None),
    category_id: str | None = Query(None),
    priority: str | None = Query(None),
    origin: str | None = Query(None),
    plan_status: str | None = Query(None),
    required_date_from: str | None = Query(None),
    required_date_to: str | None = Query(None),
):
    return _run(lambda: api_delpi_success(
        build_capex_consolidation_use_cases().get_grouping(
            build_actor(),
            group_by="month",
            **_consolidation_filter_kwargs(
                exercise_id=exercise_id,
                year=year,
                unit_id=unit_id,
                area_id=area_id,
                cost_center_id=cost_center_id,
                category_id=category_id,
                priority=priority,
                origin=origin,
                plan_status=plan_status,
                required_date_from=required_date_from,
                required_date_to=required_date_to,
            ),
        ),
        operation_id="list_planejamento_orcamentario_capex_consolidation_by_month",
        message="Consolidação CAPEX por mês da Data Rcbto.",
    ))


@router.get(
    "/capex/consolidation/by-plan-status",
    operation_id="list_planejamento_orcamentario_capex_consolidation_by_plan_status",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_CAPEX_CONSOLIDATION_VIEW_PERMISSIONS)
def list_capex_consolidation_by_plan_status(
    exercise_id: str | None = Query(None),
    year: int | None = Query(None),
    unit_id: str | None = Query(None),
    area_id: str | None = Query(None),
    cost_center_id: str | None = Query(None),
    category_id: str | None = Query(None),
    priority: str | None = Query(None),
    origin: str | None = Query(None),
    plan_status: str | None = Query(None),
    required_date_from: str | None = Query(None),
    required_date_to: str | None = Query(None),
):
    return _run(lambda: api_delpi_success(
        build_capex_consolidation_use_cases().get_grouping(
            build_actor(),
            group_by="plan_status",
            **_consolidation_filter_kwargs(
                exercise_id=exercise_id,
                year=year,
                unit_id=unit_id,
                area_id=area_id,
                cost_center_id=cost_center_id,
                category_id=category_id,
                priority=priority,
                origin=origin,
                plan_status=plan_status,
                required_date_from=required_date_from,
                required_date_to=required_date_to,
            ),
        ),
        operation_id="list_planejamento_orcamentario_capex_consolidation_by_plan_status",
        message="Consolidação CAPEX por status do planejamento.",
    ))


@router.get(
    "/capex/consolidation/details",
    operation_id="list_planejamento_orcamentario_capex_consolidation_details",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_CAPEX_CONSOLIDATION_VIEW_PERMISSIONS)
def list_capex_consolidation_details(
    exercise_id: str | None = Query(None),
    year: int | None = Query(None),
    unit_id: str | None = Query(None),
    area_id: str | None = Query(None),
    cost_center_id: str | None = Query(None),
    category_id: str | None = Query(None),
    priority: str | None = Query(None),
    origin: str | None = Query(None),
    plan_status: str | None = Query(None),
    required_date_from: str | None = Query(None),
    required_date_to: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = PAGE_SIZE_QUERY("page_50_200"),
    sort_by: str = Query("updated_at"),
    sort_dir: str = Query("desc"),
):
    return _run(lambda: api_delpi_success(
        build_capex_consolidation_use_cases().list_details(
            build_actor(),
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_dir=sort_dir,
            **_consolidation_filter_kwargs(
                exercise_id=exercise_id,
                year=year,
                unit_id=unit_id,
                area_id=area_id,
                cost_center_id=cost_center_id,
                category_id=category_id,
                priority=priority,
                origin=origin,
                plan_status=plan_status,
                required_date_from=required_date_from,
                required_date_to=required_date_to,
            ),
        ),
        operation_id="list_planejamento_orcamentario_capex_consolidation_details",
        message="Detalhamento gerencial CAPEX.",
    ))


@router.get(
    "/capex/consolidation/export.xlsx",
    operation_id="export_planejamento_orcamentario_capex_consolidation_xlsx",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_CAPEX_EXPORT_PERMISSIONS)
def export_capex_consolidation_xlsx(
    exercise_id: str | None = Query(None),
    year: int | None = Query(None),
    unit_id: str | None = Query(None),
    area_id: str | None = Query(None),
    cost_center_id: str | None = Query(None),
    category_id: str | None = Query(None),
    priority: str | None = Query(None),
    origin: str | None = Query(None),
    plan_status: str | None = Query(None),
    required_date_from: str | None = Query(None),
    required_date_to: str | None = Query(None),
):
    def _do():
        result = build_capex_consolidation_use_cases().export_xlsx(
            build_actor(),
            **_consolidation_filter_kwargs(
                exercise_id=exercise_id,
                year=year,
                unit_id=unit_id,
                area_id=area_id,
                cost_center_id=cost_center_id,
                category_id=category_id,
                priority=priority,
                origin=origin,
                plan_status=plan_status,
                required_date_from=required_date_from,
                required_date_to=required_date_to,
            ),
        )
        return StreamingResponse(
            result["stream"],
            media_type=result["content_type"],
            headers={
                "Content-Disposition": f'attachment; filename="{result["filename"]}"',
                "X-Exported-Count": str(result["exported_count"]),
            },
        )

    return _run(_do)


# -------- Orçamento de Pessoal (Fase 3B.1 / 3B.1.1 — cargo livre) --------
@router.post(
    "/personnel/plans/resolve",
    operation_id="resolve_planejamento_orcamentario_personnel_plan",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_PERSONNEL_EDIT_PERMISSIONS)
def resolve_personnel_plan(body: PersonnelPlanResolveBody):
    return _run(lambda: api_delpi_success(
        build_personnel_plan_use_cases().resolve_plan(
            build_actor(),
            exercise_id=body.exercise_id,
            unit_id=body.unit_id,
            cost_center_id=body.cost_center_id,
        ),
        operation_id="resolve_planejamento_orcamentario_personnel_plan",
        message="Planejamento de Pessoal resolvido.",
    ))


@router.get(
    "/personnel/plans",
    operation_id="list_planejamento_orcamentario_personnel_plans",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_PERSONNEL_VIEW_PERMISSIONS)
def list_personnel_plans(
    exercise_id: str | None = None,
    unit_id: str | None = None,
    cost_center_id: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = PAGE_SIZE_QUERY("page_50_100"),
):
    return _run(lambda: api_delpi_success(
        build_personnel_plan_use_cases().list_plans(
            build_actor(),
            exercise_id=exercise_id,
            unit_id=unit_id,
            cost_center_id=cost_center_id,
            page=page,
            page_size=page_size,
        ),
        operation_id="list_planejamento_orcamentario_personnel_plans",
        message="Lista de planejamentos de Pessoal.",
    ))


@router.get(
    "/personnel/plans/{plan_id}",
    operation_id="get_planejamento_orcamentario_personnel_plan",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_PERSONNEL_VIEW_PERMISSIONS)
def get_personnel_plan(plan_id: str):
    return _run(lambda: api_delpi_success(
        build_personnel_plan_use_cases().get_plan(build_actor(), plan_id),
        operation_id="get_planejamento_orcamentario_personnel_plan",
        message="Detalhe do planejamento de Pessoal.",
    ))


@router.post(
    "/personnel/plans/{plan_id}/lines",
    operation_id="create_planejamento_orcamentario_personnel_plan_line",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_PERSONNEL_EDIT_PERMISSIONS)
def create_personnel_plan_line(plan_id: str, body: PersonnelLineCreateBody):
    return _run(lambda: api_delpi_success(
        build_personnel_plan_use_cases().create_line(
            build_actor(), plan_id, body.model_dump()
        ),
        operation_id="create_planejamento_orcamentario_personnel_plan_line",
        message="Linha de Pessoal criada.",
    ))


@router.put(
    "/personnel/lines/{line_id}",
    operation_id="update_planejamento_orcamentario_personnel_plan_line",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_PERSONNEL_EDIT_PERMISSIONS)
def update_personnel_plan_line(line_id: str, body: PersonnelLineUpdateBody):
    return _run(lambda: api_delpi_success(
        build_personnel_plan_use_cases().update_line(
            build_actor(), line_id, body.model_dump(exclude_unset=True)
        ),
        operation_id="update_planejamento_orcamentario_personnel_plan_line",
        message="Linha de Pessoal atualizada.",
    ))


@router.post(
    "/personnel/lines/{line_id}/archive",
    operation_id="archive_planejamento_orcamentario_personnel_plan_line",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_PERSONNEL_EDIT_PERMISSIONS)
def archive_personnel_plan_line(line_id: str):
    return _run(lambda: api_delpi_success(
        build_personnel_plan_use_cases().archive_line(build_actor(), line_id),
        operation_id="archive_planejamento_orcamentario_personnel_plan_line",
        message="Linha de Pessoal arquivada.",
    ))

@router.post(
    "/personnel/plans/{plan_id}/submit",
    operation_id="submit_planejamento_orcamentario_personnel_plan",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_PERSONNEL_SUBMIT_PERMISSIONS)
def submit_personnel_plan(plan_id: str, body: PersonnelPlanSubmitBody):
    return _run(lambda: api_delpi_success(
        build_personnel_plan_use_cases().submit_plan(
            build_actor(),
            plan_id,
            version=body.version,
            comment=body.comment,
        ),
        operation_id="submit_planejamento_orcamentario_personnel_plan",
        message="Planejamento de Pessoal submetido.",
    ))


@router.get(
    "/personnel/plans/{plan_id}/history",
    operation_id="list_planejamento_orcamentario_personnel_plan_history",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_PERSONNEL_VIEW_PERMISSIONS)
def list_personnel_plan_history(plan_id: str):
    return _run(lambda: api_delpi_success(
        build_personnel_plan_use_cases().list_history(build_actor(), plan_id),
        operation_id="list_planejamento_orcamentario_personnel_plan_history",
        message="Histórico do planejamento de Pessoal.",
    ))


@router.get(
    "/personnel/review-queue",
    operation_id="list_planejamento_orcamentario_personnel_review_queue",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_PERSONNEL_APPROVE_PERMISSIONS)
def list_personnel_review_queue(
    exercise_id: str | None = None,
    unit_id: str | None = None,
    area_id: str | None = None,
    cost_center_id: str | None = None,
    status: str | None = None,
    submitted_by: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = PAGE_SIZE_QUERY("page_50_100"),
):
    return _run(lambda: api_delpi_success(
        build_personnel_plan_use_cases().list_review_queue(
            build_actor(),
            exercise_id=exercise_id,
            unit_id=unit_id,
            area_id=area_id,
            cost_center_id=cost_center_id,
            status=status,
            submitted_by=submitted_by,
            page=page,
            page_size=page_size,
        ),
        operation_id="list_planejamento_orcamentario_personnel_review_queue",
        message="Fila de aprovação do Orçamento de Pessoal.",
    ))


@router.get(
    "/personnel/review/{plan_id}",
    operation_id="get_planejamento_orcamentario_personnel_review",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_PERSONNEL_APPROVE_PERMISSIONS)
def get_personnel_review(plan_id: str):
    return _run(lambda: api_delpi_success(
        build_personnel_plan_use_cases().get_review_detail(build_actor(), plan_id),
        operation_id="get_planejamento_orcamentario_personnel_review",
        message="Detalhe para revisão do Orçamento de Pessoal.",
    ))


@router.post(
    "/personnel/review/{plan_id}/request-changes",
    operation_id="request_changes_planejamento_orcamentario_personnel_plan",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_PERSONNEL_APPROVE_PERMISSIONS)
def request_changes_personnel_plan(plan_id: str, body: PersonnelPlanRequestChangesBody):
    return _run(lambda: api_delpi_success(
        build_personnel_plan_use_cases().request_changes(
            build_actor(),
            plan_id,
            version=body.version,
            comment=body.comment,
        ),
        operation_id="request_changes_planejamento_orcamentario_personnel_plan",
        message="Ajustes solicitados no planejamento de Pessoal.",
    ))


@router.post(
    "/personnel/review/{plan_id}/reject",
    operation_id="reject_planejamento_orcamentario_personnel_plan",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_PERSONNEL_APPROVE_PERMISSIONS)
def reject_personnel_plan(plan_id: str, body: PersonnelPlanRejectBody):
    return _run(lambda: api_delpi_success(
        build_personnel_plan_use_cases().reject_plan(
            build_actor(),
            plan_id,
            version=body.version,
            comment=body.comment,
        ),
        operation_id="reject_planejamento_orcamentario_personnel_plan",
        message="Planejamento de Pessoal reprovado.",
    ))


@router.post(
    "/personnel/review/{plan_id}/approve",
    operation_id="approve_planejamento_orcamentario_personnel_plan",
)
@require_any_permission(PLANEJAMENTO_ORCAMENTARIO_PERSONNEL_APPROVE_PERMISSIONS)
def approve_personnel_plan(plan_id: str, body: PersonnelPlanDecisionBody):
    return _run(lambda: api_delpi_success(
        build_personnel_plan_use_cases().approve_plan(
            build_actor(),
            plan_id,
            version=body.version,
            comment=body.comment,
        ),
        operation_id="approve_planejamento_orcamentario_personnel_plan",
        message="Planejamento de Pessoal aprovado.",
    ))

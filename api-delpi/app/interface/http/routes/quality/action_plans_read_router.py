from __future__ import annotations

from fastapi import APIRouter, Body, Query
from pydantic import BaseModel, Field

from delpi_auth.authorization import require_any_permission
from delpi_auth.request_context import get_current_user

from app.application.security.api_delpi_permissions import (
    QUALITY_ACTION_PLANS_READ_PERMISSIONS,
    QUALITY_ACTION_PLANS_WRITE_PERMISSIONS,
)
from app.application.use_cases.quality_action_plans.quality_action_plan_analysis_use_cases import (
    CreateActionItemRequest,
    EffectivenessReviewRequest,
    UpsertFiveWhysRequest,
    UpsertIshikawaRequest,
)
from app.application.use_cases.quality_action_plans.quality_action_plans_use_cases import (
    CreateQualityActionPlanRequest,
)
from app.composition.quality_action_plans_composer import (
    build_create_plan_actions_use_case,
    build_create_quality_action_plan_use_case,
    build_quality_action_plan_read_repository,
    build_record_effectiveness_review_use_case,
    build_update_plan_action_use_case,
    build_update_quality_action_plan_status_use_case,
    build_upsert_five_whys_use_case,
    build_upsert_ishikawa_use_case,
)
from app.core.responses import error_response, not_found_response
from app.interface.http.route_response_helpers import api_delpi_success
from app.infrastructure.persistence.plugins.plugin_base_repository import PluginsRepositoryError
from app.utils.logger import log_error

router = APIRouter(prefix="/action-plans", tags=["PAC Qualidade — planos de ação"])


class CreateActionPlanBody(BaseModel):
    title: str = Field(..., min_length=2, max_length=500)
    customer_name: str | None = Field(default=None, max_length=300)
    customer_contact: str | None = Field(default=None, max_length=300)
    source_type: str | None = Field(
        default=None,
        pattern="^(email|message|spreadsheet|pdf|image|manual_text|system_reference|other)$",
    )
    source_reference: str | None = Field(default=None, max_length=500)
    product_code: str | None = Field(default=None, max_length=50)
    product_description: str | None = Field(default=None, max_length=500)
    batch_number: str | None = Field(default=None, max_length=100)
    reported_problem: str | None = None
    detected_at: str | None = None
    reported_at: str | None = None
    severity: str = Field(default="medium", pattern="^(low|medium|high|critical)$")
    status: str = Field(default="triage", pattern="^(draft|triage)$")
    owner_user_id: str | None = Field(default=None, max_length=100)
    branch_code: str = Field(..., pattern="^(01|02)$")
    department: str | None = Field(default=None, max_length=200)
    problem_category: str | None = Field(default=None, max_length=200)
    symptom_tags: list[str] | None = None
    root_cause_category: str | None = Field(default=None, max_length=200)
    failure_mode: str | None = Field(default=None, max_length=300)
    recurrence_key: str | None = Field(default=None, max_length=500)


class UpdateActionPlanStatusBody(BaseModel):
    status: str = Field(
        ...,
        pattern=(
            "^(draft|triage|containment|root_cause_analysis|action_plan_defined|"
            "in_progress|waiting_validation|completed|cancelled)$"
        ),
    )
    comment: str | None = None


class IshikawaBody(BaseModel):
    machine: str | None = None
    method_process: str | None = None
    material: str | None = None
    manpower: str | None = None
    measurement: str | None = None
    environment: str | None = None
    notes: str | None = None


class FiveWhysBody(BaseModel):
    why_1: str | None = None
    why_2: str | None = None
    why_3: str | None = None
    why_4: str | None = None
    why_5: str | None = None
    root_cause: str | None = None
    confidence_level: str | None = Field(default=None, pattern="^(low|medium|high)$")


class ActionItemBody(BaseModel):
    action_type: str = Field(
        ...,
        pattern="^(containment|corrective|preventive|verification|standardization|training)$",
    )
    description: str = Field(..., min_length=3)
    responsible_user_id: str | None = None
    responsible_name: str | None = None
    department: str | None = None
    due_date: str | None = None
    status: str = Field(default="pending", pattern="^(pending|in_progress|blocked)$")
    evidence_required: bool = False


class CreateActionsBody(BaseModel):
    actions: list[ActionItemBody] = Field(..., min_length=1)


class UpdateActionBody(BaseModel):
    description: str | None = Field(default=None, min_length=3)
    responsible_user_id: str | None = None
    responsible_name: str | None = None
    department: str | None = None
    due_date: str | None = None
    status: str | None = Field(
        default=None,
        pattern="^(pending|in_progress|blocked|completed|cancelled|overdue)$",
    )
    evidence_required: bool | None = None


class EffectivenessReviewBody(BaseModel):
    effectiveness_status: str = Field(
        ...,
        pattern="^(pending|effective|partially_effective|ineffective|not_verified)$",
    )
    notes: str | None = None


def _current_user_id() -> str:
    user = get_current_user()
    if user is None:
        return "unknown"
    return str(getattr(user, "id", "unknown"))


@router.get("/dashboard")
@require_any_permission(QUALITY_ACTION_PLANS_READ_PERMISSIONS)
def get_action_plans_dashboard(
    branch_code: str | None = Query(default=None, pattern="^(01|02)$"),
):
    try:
        repo = build_quality_action_plan_read_repository()
        return api_delpi_success(
            repo.get_dashboard_summary(branch_code=branch_code),
            operation_id="get_quality_action_plans_dashboard",
            message="Dashboard PAC carregado.",
        )
    except PluginsRepositoryError as exc:
        log_error(f"Erro ao carregar dashboard PAC: {exc}")
        return error_response("Erro ao carregar dashboard de planos de ação.", status_code=500)


@router.get("/overdue")
@require_any_permission(QUALITY_ACTION_PLANS_READ_PERMISSIONS)
def list_overdue_action_plans(
    branch_code: str | None = Query(default=None, pattern="^(01|02)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
):
    try:
        repo = build_quality_action_plan_read_repository()
        return api_delpi_success(
            repo.list_overdue_plans(branch_code=branch_code, page=page, page_size=page_size),
            operation_id="list_quality_action_plans_overdue",
        )
    except PluginsRepositoryError as exc:
        log_error(f"Erro ao listar planos atrasados PAC: {exc}")
        return error_response("Erro ao listar planos atrasados.", status_code=500)


@router.post("")
@require_any_permission(QUALITY_ACTION_PLANS_WRITE_PERMISSIONS)
def create_action_plan(body: CreateActionPlanBody = Body(...)):
    try:
        plan = build_create_quality_action_plan_use_case().execute(
            CreateQualityActionPlanRequest(
                title=body.title,
                created_by_user_id=_current_user_id(),
                customer_name=body.customer_name,
                customer_contact=body.customer_contact,
                source_type=body.source_type,
                source_reference=body.source_reference,
                product_code=body.product_code,
                product_description=body.product_description,
                batch_number=body.batch_number,
                reported_problem=body.reported_problem,
                detected_at=body.detected_at,
                reported_at=body.reported_at,
                severity=body.severity,
                status=body.status,
                owner_user_id=body.owner_user_id,
                branch_code=body.branch_code,
                department=body.department,
                problem_category=body.problem_category,
                symptom_tags=body.symptom_tags,
                root_cause_category=body.root_cause_category,
                failure_mode=body.failure_mode,
                recurrence_key=body.recurrence_key,
            )
        )
        return api_delpi_success(
            plan,
            operation_id="create_quality_action_plan",
            message="Plano de ação criado com sucesso.",
        )
    except ValueError as exc:
        return error_response(str(exc), status_code=400)
    except PluginsRepositoryError as exc:
        log_error(f"Erro ao criar plano PAC: {exc}")
        return error_response(str(exc), status_code=500)


@router.get("")
@require_any_permission(QUALITY_ACTION_PLANS_READ_PERMISSIONS)
def list_action_plans(
    status: str | None = Query(default=None),
    severity: str | None = Query(default=None, pattern="^(low|medium|high|critical)$"),
    product_code: str | None = Query(default=None),
    customer_name: str | None = Query(default=None),
    owner_user_id: str | None = Query(default=None),
    branch_code: str | None = Query(default=None, pattern="^(01|02)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
):
    try:
        repo = build_quality_action_plan_read_repository()
        return api_delpi_success(
            repo.list_plans(
                status=status,
                severity=severity,
                product_code=product_code,
                customer_name=customer_name,
                owner_user_id=owner_user_id,
                branch_code=branch_code,
                page=page,
                page_size=page_size,
            ),
            operation_id="list_quality_action_plans",
        )
    except PluginsRepositoryError as exc:
        log_error(f"Erro ao listar planos PAC: {exc}")
        return error_response("Erro ao listar planos de ação.", status_code=500)


@router.get("/{plan_id}")
@require_any_permission(QUALITY_ACTION_PLANS_READ_PERMISSIONS)
def get_action_plan_detail(plan_id: str):
    try:
        repo = build_quality_action_plan_read_repository()
        detail = repo.get_plan_detail(plan_id)
        if not detail:
            return not_found_response("Plano de ação não encontrado.")
        return api_delpi_success(
            detail,
            operation_id="get_quality_action_plan_detail",
        )
    except PluginsRepositoryError as exc:
        log_error(f"Erro ao buscar plano PAC {plan_id}: {exc}")
        return error_response("Erro ao consultar plano de ação.", status_code=500)


@router.patch("/{plan_id}/status")
@require_any_permission(QUALITY_ACTION_PLANS_WRITE_PERMISSIONS)
def update_action_plan_status(plan_id: str, body: UpdateActionPlanStatusBody = Body(...)):
    try:
        plan = build_update_quality_action_plan_status_use_case().execute(
            plan_id,
            status=body.status,
            updated_by=_current_user_id(),
            comment=body.comment,
        )
        if not plan:
            return not_found_response("Plano de ação não encontrado.")
        return api_delpi_success(
            plan,
            operation_id="update_quality_action_plan_status",
            message="Status atualizado com sucesso.",
        )
    except ValueError as exc:
        return error_response(str(exc), status_code=400)
    except PluginsRepositoryError as exc:
        log_error(f"Erro ao atualizar status do plano PAC {plan_id}: {exc}")
        return error_response("Erro ao atualizar status do plano.", status_code=500)


@router.put("/{plan_id}/ishikawa")
@require_any_permission(QUALITY_ACTION_PLANS_WRITE_PERMISSIONS)
def upsert_ishikawa(plan_id: str, body: IshikawaBody = Body(...)):
    try:
        result = build_upsert_ishikawa_use_case().execute(
            plan_id,
            UpsertIshikawaRequest(**body.model_dump()),
            updated_by=_current_user_id(),
        )
        if not result:
            return not_found_response("Plano de ação não encontrado.")
        return api_delpi_success(
            result,
            operation_id="upsert_quality_action_plan_ishikawa",
            message="Análise Ishikawa registrada.",
        )
    except PluginsRepositoryError as exc:
        log_error(f"Erro ao salvar Ishikawa do plano {plan_id}: {exc}")
        return error_response("Erro ao registrar Ishikawa.", status_code=500)


@router.put("/{plan_id}/five-whys")
@require_any_permission(QUALITY_ACTION_PLANS_WRITE_PERMISSIONS)
def upsert_five_whys(plan_id: str, body: FiveWhysBody = Body(...)):
    try:
        result = build_upsert_five_whys_use_case().execute(
            plan_id,
            UpsertFiveWhysRequest(**body.model_dump()),
            updated_by=_current_user_id(),
        )
        if not result:
            return not_found_response("Plano de ação não encontrado.")
        return api_delpi_success(
            result,
            operation_id="upsert_quality_action_plan_five_whys",
            message="5 Porquês registrados.",
        )
    except ValueError as exc:
        return error_response(str(exc), status_code=400)
    except PluginsRepositoryError as exc:
        log_error(f"Erro ao salvar 5 Porquês do plano {plan_id}: {exc}")
        return error_response("Erro ao registrar 5 Porquês.", status_code=500)


@router.post("/{plan_id}/actions")
@require_any_permission(QUALITY_ACTION_PLANS_WRITE_PERMISSIONS)
def create_plan_actions(plan_id: str, body: CreateActionsBody = Body(...)):
    try:
        actions = [CreateActionItemRequest(**item.model_dump()) for item in body.actions]
        result = build_create_plan_actions_use_case().execute(
            plan_id,
            actions,
            created_by=_current_user_id(),
        )
        if result is None:
            return not_found_response("Plano de ação não encontrado.")
        return api_delpi_success(
            {"items": result},
            operation_id="create_quality_action_plan_actions",
            message="Ações registradas.",
        )
    except ValueError as exc:
        return error_response(str(exc), status_code=400)
    except PluginsRepositoryError as exc:
        log_error(f"Erro ao criar ações do plano {plan_id}: {exc}")
        return error_response("Erro ao registrar ações.", status_code=500)


@router.patch("/{plan_id}/actions/{action_id}")
@require_any_permission(QUALITY_ACTION_PLANS_WRITE_PERMISSIONS)
def update_plan_action(plan_id: str, action_id: str, body: UpdateActionBody = Body(...)):
    try:
        fields = body.model_dump(exclude_unset=True)
        result = build_update_plan_action_use_case().execute(
            plan_id,
            action_id,
            fields,
            updated_by=_current_user_id(),
        )
        if not result:
            return not_found_response("Ação não encontrada.")
        return api_delpi_success(
            result,
            operation_id="update_quality_action_plan_action",
            message="Ação atualizada.",
        )
    except ValueError as exc:
        return error_response(str(exc), status_code=400)
    except PluginsRepositoryError as exc:
        log_error(f"Erro ao atualizar ação {action_id}: {exc}")
        return error_response("Erro ao atualizar ação.", status_code=500)


@router.post("/{plan_id}/effectiveness-review")
@require_any_permission(QUALITY_ACTION_PLANS_WRITE_PERMISSIONS)
def record_effectiveness_review(plan_id: str, body: EffectivenessReviewBody = Body(...)):
    try:
        result = build_record_effectiveness_review_use_case().execute(
            plan_id,
            EffectivenessReviewRequest(
                effectiveness_status=body.effectiveness_status,
                notes=body.notes,
            ),
            updated_by=_current_user_id(),
        )
        if not result:
            return not_found_response("Plano de ação não encontrado.")
        return api_delpi_success(
            result,
            operation_id="record_quality_action_plan_effectiveness",
            message="Eficácia registrada.",
        )
    except ValueError as exc:
        return error_response(str(exc), status_code=400)
    except PluginsRepositoryError as exc:
        log_error(f"Erro ao registrar eficácia do plano {plan_id}: {exc}")
        return error_response("Erro ao registrar eficácia.", status_code=500)

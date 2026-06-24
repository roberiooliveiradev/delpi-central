from __future__ import annotations

from fastapi import APIRouter, Query

from delpi_auth.authorization import require_any_permission

from app.application.security.api_delpi_permissions import QUALITY_ACTION_PLANS_READ_PERMISSIONS
from app.composition.quality_action_plans_composer import build_quality_action_plan_read_repository
from app.core.responses import error_response, not_found_response
from app.interface.http.route_response_helpers import api_delpi_success
from app.infrastructure.persistence.plugins.plugin_base_repository import PluginsRepositoryError
from app.utils.logger import log_error

router = APIRouter(prefix="/action-plans", tags=["PAC Qualidade — leitura"])


@router.get("/dashboard")
@require_any_permission(QUALITY_ACTION_PLANS_READ_PERMISSIONS)
def get_action_plans_dashboard():
    try:
        repo = build_quality_action_plan_read_repository()
        return api_delpi_success(
            repo.get_dashboard_summary(),
            operation_id="get_quality_action_plans_dashboard",
            message="Dashboard PAC carregado.",
        )
    except PluginsRepositoryError as exc:
        log_error(f"Erro ao carregar dashboard PAC: {exc}")
        return error_response("Erro ao carregar dashboard de planos de ação.", status_code=500)


@router.get("/overdue")
@require_any_permission(QUALITY_ACTION_PLANS_READ_PERMISSIONS)
def list_overdue_action_plans(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
):
    try:
        repo = build_quality_action_plan_read_repository()
        return api_delpi_success(
            repo.list_overdue_plans(page=page, page_size=page_size),
            operation_id="list_quality_action_plans_overdue",
        )
    except PluginsRepositoryError as exc:
        log_error(f"Erro ao listar planos atrasados PAC: {exc}")
        return error_response("Erro ao listar planos atrasados.", status_code=500)


@router.get("")
@require_any_permission(QUALITY_ACTION_PLANS_READ_PERMISSIONS)
def list_action_plans(
    status: str | None = Query(default=None),
    severity: str | None = Query(default=None, pattern="^(low|medium|high|critical)$"),
    product_code: str | None = Query(default=None),
    customer_name: str | None = Query(default=None),
    owner_user_id: str | None = Query(default=None),
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

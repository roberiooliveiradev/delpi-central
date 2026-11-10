"""Rotas de planos de ação."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request

from it_portal_app.application.action_plan_service import ActionPlanService
from it_portal_app.application.ports import ActionPlanQuery
from it_portal_app.core.responses import ok
from it_portal_app.interface.http.authz import (
    ACTIONS_MANAGE,
    ACTIONS_VIEW,
    SERVERS_VIEW,
    actor_from,
    authorize,
)
from it_portal_app.interface.http.dependencies import (
    get_action_plan_service,
    get_today_provider,
)
from it_portal_app.interface.http.schemas import (
    ERROR_RESPONSES,
    ActionPlanInput,
    ActionPlanOut,
    ActionPlanStatusInput,
    ActionPlanUpdateInput,
    Envelope,
    PageOut,
)

router = APIRouter(tags=["Action Plans"], responses=ERROR_RESPONSES)

ActionSortKey = Literal["due_date", "priority", "status", "created_at", "updated_at", "title"]


@router.get(
    "/action-plans",
    operation_id="list_it_action_plans",
    response_model=Envelope[PageOut[ActionPlanOut]],
    summary="Lista planos de ação com filtros, ordenação e paginação",
)
def list_it_action_plans(
    request: Request,
    status: list[str] = Query(default=[], description="Repita para vários status"),
    server_id: UUID | None = Query(default=None),
    priority: str | None = Query(default=None),
    overdue_only: bool = Query(default=False),
    q: str | None = Query(default=None, max_length=120),
    sort: ActionSortKey = Query(default="due_date"),
    direction: Literal["asc", "desc"] = Query(default="asc"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    service: ActionPlanService = Depends(get_action_plan_service),
    today: Callable[[], date] = Depends(get_today_provider),
):
    authorize(request, SERVERS_VIEW, ACTIONS_VIEW)
    result = service.list_action_plans(
        ActionPlanQuery(
            today=today(),
            statuses=tuple(status),
            server_id=str(server_id) if server_id else None,
            priority=priority,
            overdue_only=overdue_only,
            q=q,
            sort=sort,
            direction=direction,
            page=page,
            page_size=page_size,
        )
    )
    return ok(result, operation_id="list_it_action_plans")


@router.post(
    "/servers/{server_id}/action-plans",
    operation_id="create_it_action_plan",
    response_model=Envelope[ActionPlanOut],
    status_code=201,
    summary="Cria um plano de ação para o servidor",
)
def create_it_action_plan(
    request: Request,
    server_id: UUID,
    payload: ActionPlanInput,
    service: ActionPlanService = Depends(get_action_plan_service),
):
    user = authorize(request, SERVERS_VIEW, ACTIONS_MANAGE)
    created = service.create_action_plan(
        str(server_id), payload.model_dump(), actor_from(user)
    )
    return ok(created, "Plano de ação criado.", 201, operation_id="create_it_action_plan")


@router.get(
    "/action-plans/{action_plan_id}",
    operation_id="get_it_action_plan",
    response_model=Envelope[ActionPlanOut],
    summary="Detalhe do plano de ação",
)
def get_it_action_plan(
    request: Request,
    action_plan_id: UUID,
    service: ActionPlanService = Depends(get_action_plan_service),
):
    authorize(request, SERVERS_VIEW, ACTIONS_VIEW)
    return ok(service.get_action_plan(str(action_plan_id)), operation_id="get_it_action_plan")


@router.put(
    "/action-plans/{action_plan_id}",
    operation_id="update_it_action_plan",
    response_model=Envelope[ActionPlanOut],
    summary="Edita o plano de ação (concorrência otimista por revision)",
)
def update_it_action_plan(
    request: Request,
    action_plan_id: UUID,
    payload: ActionPlanUpdateInput,
    service: ActionPlanService = Depends(get_action_plan_service),
):
    user = authorize(request, SERVERS_VIEW, ACTIONS_MANAGE)
    updated = service.update_action_plan(
        str(action_plan_id),
        payload.model_dump(exclude={"revision"}),
        payload.revision,
        actor_from(user),
    )
    return ok(updated, "Plano de ação atualizado.", operation_id="update_it_action_plan")


@router.post(
    "/action-plans/{action_plan_id}/status",
    operation_id="change_it_action_plan_status",
    response_model=Envelope[ActionPlanOut],
    summary="Altera o status do plano de ação",
)
def change_it_action_plan_status(
    request: Request,
    action_plan_id: UUID,
    payload: ActionPlanStatusInput,
    service: ActionPlanService = Depends(get_action_plan_service),
):
    user = authorize(request, SERVERS_VIEW, ACTIONS_MANAGE)
    updated = service.change_status(
        str(action_plan_id), payload.status, payload.revision, actor_from(user)
    )
    return ok(updated, "Status atualizado.", operation_id="change_it_action_plan_status")

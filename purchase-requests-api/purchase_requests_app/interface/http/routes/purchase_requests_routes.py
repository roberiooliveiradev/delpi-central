from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from delpi_auth.request_context import get_current_user

from purchase_requests_app.application.security.purchase_requests_permissions import (
    has_admin,
)
from purchase_requests_app.application.use_cases.get_purchase_request_use_case import (
    GetPurchaseRequestUseCase,
)
from purchase_requests_app.application.use_cases.list_admin_protheus_users_use_case import (
    ListAdminProtheusUsersUseCase,
)
from purchase_requests_app.application.use_cases.list_purchase_request_requesters_use_case import (
    ListPurchaseRequestRequestersUseCase,
)
from purchase_requests_app.application.use_cases.list_purchase_requests_use_case import (
    ListPurchaseRequestsUseCase,
)
from purchase_requests_app.core.responses import fail, ok
from purchase_requests_app.infrastructure.persistence.repositories.user_protheus_mapping_repository import (
    UserProtheusMappingRepository,
)
from purchase_requests_app.domain.services.notification_event_catalog import (
    list_notification_events,
)
from purchase_requests_app.infrastructure.persistence.repositories.notification_subscription_repository import (
    NotificationSubscriptionRepository,
)
from purchase_requests_app.infrastructure.persistence.repositories.visibility_scope_repository import (
    VisibilityScopeRepository,
)

router = APIRouter(prefix="/purchase-requests", tags=["Purchase Requests"])


def _current_user():
    user = get_current_user()
    if user is None:
        raise HTTPException(status_code=401, detail="Não autenticado.")
    return user


@router.get("")
def list_purchase_requests(
    branch: str = Query(...),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    request_number: str | None = Query(None),
    requester_user_id: list[str] | None = Query(None),
    cost_center: list[str] | None = Query(None),
    product_code: str | None = Query(None),
    supplier_code: str | None = Query(None),
    order_number: str | None = Query(None),
    overall_stage: list[str] | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    user=Depends(_current_user),
):
    try:
        result = ListPurchaseRequestsUseCase().execute(
            user=user,
            branch=branch,
            date_from=date_from,
            date_to=date_to,
            request_number=request_number,
            requester_user_ids=requester_user_id,
            cost_centers=cost_center,
            product_code=product_code,
            supplier_code=supplier_code,
            order_number=order_number,
            overall_stages=overall_stage,
            page=page,
            page_size=page_size,
        )
        return ok(result, message="Solicitações de compra listadas com sucesso.")
    except PermissionError as exc:
        return fail(str(exc), 403)
    except Exception:
        return fail("Erro interno ao listar solicitações de compra.", 500)


@router.get("/requesters")
def list_purchase_request_requesters(
    branch: str = Query(...),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    request_number: str | None = Query(None),
    cost_center: list[str] | None = Query(None),
    product_code: str | None = Query(None),
    supplier_code: str | None = Query(None),
    order_number: str | None = Query(None),
    user=Depends(_current_user),
):
    try:
        result = ListPurchaseRequestRequestersUseCase().execute(
            user=user,
            branch=branch,
            date_from=date_from,
            date_to=date_to,
            request_number=request_number,
            cost_centers=cost_center,
            product_code=product_code,
            supplier_code=supplier_code,
            order_number=order_number,
        )
        return ok(result, message="Solicitantes listados com sucesso.")
    except PermissionError as exc:
        return fail(str(exc), 403)
    except Exception:
        return fail("Erro interno ao listar solicitantes.", 500)


@router.get("/{branch}/{request_number}")
def get_purchase_request(
    branch: str,
    request_number: str,
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    cost_center: list[str] | None = Query(None),
    user=Depends(_current_user),
):
    try:
        result = GetPurchaseRequestUseCase().execute(
            user=user,
            branch=branch,
            request_number=request_number,
            date_from=date_from,
            date_to=date_to,
            cost_centers=cost_center,
        )
        return ok(result, message="Detalhe da solicitação carregado com sucesso.")
    except PermissionError as exc:
        return fail(str(exc), 403)
    except LookupError:
        return fail("Solicitação não encontrada.", 404)
    except Exception:
        return fail("Erro interno ao carregar solicitação de compra.", 500)


class VisibilityScopeCreateBody(BaseModel):
    name: str = Field(min_length=1)
    description: str | None = None


class VisibilityScopeUpdateBody(BaseModel):
    name: str | None = None
    description: str | None = None
    active: bool | None = None


class ReplaceUsersBody(BaseModel):
    user_ids: list[str]


class CostCenterItem(BaseModel):
    branch: str
    cost_center_code: str


class ReplaceCostCentersBody(BaseModel):
    cost_centers: list[CostCenterItem]


class UserMappingBody(BaseModel):
    protheus_user_id: str | None = None
    protheus_user_code: str | None = None
    mapping_status: str = "mapped"
    mapping_source: str | None = "manual"
    verified: bool = False


class NotificationSubscriptionItem(BaseModel):
    event_key: str = Field(min_length=1)
    enabled: bool = True


class ReplaceNotificationSubscriptionsBody(BaseModel):
    subscriptions: list[NotificationSubscriptionItem] = Field(default_factory=list)


admin_router = APIRouter(prefix="/purchase-requests/admin", tags=["Purchase Requests Admin"])


def _require_admin(user=Depends(_current_user)):
    if not has_admin(user):
        raise HTTPException(status_code=403, detail="Sem permissão administrativa.")
    return user


@admin_router.get("/visibility-scopes")
def list_visibility_scopes(user=Depends(_require_admin)):
    repo = VisibilityScopeRepository()
    return ok(repo.list_scopes())


@admin_router.post("/visibility-scopes")
def create_visibility_scope(body: VisibilityScopeCreateBody, user=Depends(_require_admin)):
    repo = VisibilityScopeRepository()
    actor = str(getattr(user, "id", "") or getattr(user, "sub", ""))
    scope = repo.create_scope(
        name=body.name,
        description=body.description,
        actor_user_id=actor,
    )
    return ok(scope, message="Escopo criado com sucesso.", status_code=201)


@admin_router.get("/visibility-scopes/{scope_id}")
def get_visibility_scope(scope_id: str, user=Depends(_require_admin)):
    repo = VisibilityScopeRepository()
    scope = repo.get_scope(scope_id)
    if not scope:
        return fail("Escopo não encontrado.", 404)
    return ok(scope)


@admin_router.put("/visibility-scopes/{scope_id}")
def update_visibility_scope(
    scope_id: str,
    body: VisibilityScopeUpdateBody,
    user=Depends(_require_admin),
):
    repo = VisibilityScopeRepository()
    actor = str(getattr(user, "id", "") or getattr(user, "sub", ""))
    scope = repo.update_scope(
        scope_id,
        name=body.name,
        description=body.description,
        active=body.active,
        actor_user_id=actor,
    )
    if not scope:
        return fail("Escopo não encontrado.", 404)
    return ok(scope, message="Escopo atualizado com sucesso.")


@admin_router.put("/visibility-scopes/{scope_id}/users")
def replace_visibility_scope_users(
    scope_id: str,
    body: ReplaceUsersBody,
    user=Depends(_require_admin),
):
    repo = VisibilityScopeRepository()
    scope = repo.replace_users(scope_id, body.user_ids)
    if not scope:
        return fail("Escopo não encontrado.", 404)
    return ok(scope, message="Usuários do escopo atualizados.")


@admin_router.put("/visibility-scopes/{scope_id}/cost-centers")
def replace_visibility_scope_cost_centers(
    scope_id: str,
    body: ReplaceCostCentersBody,
    user=Depends(_require_admin),
):
    repo = VisibilityScopeRepository()
    scope = repo.replace_cost_centers(
        scope_id,
        [item.model_dump() for item in body.cost_centers],
    )
    if not scope:
        return fail("Escopo não encontrado.", 404)
    return ok(scope, message="Centros de custo do escopo atualizados.")


@admin_router.get("/user-mappings")
def list_user_mappings(user=Depends(_require_admin)):
    repo = UserProtheusMappingRepository()
    return ok(repo.list_mappings())


@admin_router.put("/user-mappings/{user_id}")
def upsert_user_mapping(
    user_id: str,
    body: UserMappingBody,
    user=Depends(_require_admin),
):
    repo = UserProtheusMappingRepository()
    mapping = repo.upsert_mapping(
        user_id=user_id,
        protheus_user_id=body.protheus_user_id,
        protheus_user_code=body.protheus_user_code,
        mapping_status=body.mapping_status,
        mapping_source=body.mapping_source,
        verified=body.verified,
    )
    return ok(mapping, message="Mapping atualizado com sucesso.")


@admin_router.get("/protheus-users")
def list_admin_protheus_users(
    branch: str = Query(...),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    user=Depends(_require_admin),
):
    try:
        result = ListAdminProtheusUsersUseCase().execute(
            user=user,
            branch=branch,
            date_from=date_from,
            date_to=date_to,
        )
        return ok(result, message="Usuários Protheus listados com sucesso.")
    except PermissionError as exc:
        return fail(str(exc), 403)
    except Exception:
        return fail("Erro interno ao listar usuários Protheus.", 500)


@admin_router.get("/notification-events")
def list_notification_events_route(user=Depends(_require_admin)):
    return ok({"items": list_notification_events()})


@admin_router.get("/notification-subscriptions")
def list_notification_subscriptions(user=Depends(_require_admin)):
    repo = NotificationSubscriptionRepository()
    return ok({"items": repo.list_all()})


@admin_router.get("/notification-subscriptions/{user_id}")
def list_notification_subscriptions_for_user(user_id: str, user=Depends(_require_admin)):
    repo = NotificationSubscriptionRepository()
    return ok({"items": repo.list_for_user(user_id)})


@admin_router.put("/notification-subscriptions/{user_id}")
def replace_notification_subscriptions(
    user_id: str,
    body: ReplaceNotificationSubscriptionsBody,
    user=Depends(_require_admin),
):
    repo = NotificationSubscriptionRepository()
    try:
        items = repo.replace_for_user(
            user_id,
            [item.model_dump() for item in body.subscriptions],
        )
    except ValueError as exc:
        return fail(str(exc), 422)
    return ok({"items": items}, message="Notificações atualizadas com sucesso.")

"""BFF open-orders / ops — escopo commercial antes do proxy TOTVS."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Query, Request

from commercial_app.application.security.auth_dependencies import require_any_permission
from commercial_app.application.security.commercial_permissions import (
    COMMERCIAL_MANAGE_PERMISSIONS,
    COMMERCIAL_READ_PERMISSIONS,
    can_manage_portfolios,
    can_use_team_scope,
)
from commercial_app.application.services.filter_open_orders_by_scope_service import (
    FilterOpenOrdersByScopeService,
)
from commercial_app.composition.commercial_composer import (
    build_delpi_commercial_gateway,
    build_resolve_commercial_customer_scope_service,
)
from commercial_app.core.auth_actor import (
    actor_sub_from_request,
    current_user_from_request,
)
from commercial_app.core.responses import fail, ok

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/open-orders", tags=["Open orders"])


def _open_orders_scope(request: Request, *, portfolio_id: str | None):
    user = current_user_from_request(request)
    unrestricted = can_manage_portfolios(user) or can_use_team_scope(user)
    user_id = actor_sub_from_request(request) or ""
    return build_resolve_commercial_customer_scope_service().execute(
        user_id=user_id,
        unrestricted=unrestricted,
        portfolio_id=portfolio_id,
    ).for_open_orders()


@router.get("/", operation_id="list_commercial_open_orders")
@require_any_permission(*COMMERCIAL_READ_PERMISSIONS, *COMMERCIAL_MANAGE_PERMISSIONS)
def list_commercial_open_orders(
    request: Request,
    seller_id: str | None = Query(
        default=None,
        description="PK da carteira. Team/manage: qualquer; membro: só carteira própria. Alias histórico seller_id.",
    ),
    portfolio_id: str | None = Query(
        default=None,
        description="PK da carteira (preferencial). Se ambos, portfolio_id vence.",
    ),
):
    try:
        pid = (portfolio_id or seller_id or "").strip() or None
        scope = _open_orders_scope(request, portfolio_id=pid)
        # api-delpi: sem seller_id — commercial filtra no BFF (opção a do plano).
        payload = build_delpi_commercial_gateway().list_open_orders()
        raw = payload.get("data", payload) if isinstance(payload, dict) else {}
        data = FilterOpenOrdersByScopeService().apply(
            raw if isinstance(raw, dict) else {},
            scope,
        )
        return ok(data, message="Pedidos de venda em aberto carregados.")
    except PermissionError as exc:
        return fail(str(exc), 403, operation_id="list_commercial_open_orders")
    except LookupError as exc:
        return fail(str(exc), 404, operation_id="list_commercial_open_orders")
    except ValueError as exc:
        return fail(str(exc), 400, operation_id="list_commercial_open_orders")
    except RuntimeError as exc:
        return fail(str(exc), 502, operation_id="list_commercial_open_orders")
    except Exception:
        logger.exception("list_commercial_open_orders_failed")
        return fail(
            "Erro interno ao carregar pedidos em aberto.",
            500,
            operation_id="list_commercial_open_orders",
        )


@router.get("/ops-abertas", operation_id="list_commercial_open_ops")
@require_any_permission(*COMMERCIAL_READ_PERMISSIONS, *COMMERCIAL_MANAGE_PERMISSIONS)
def list_commercial_open_ops(_request: Request):
    try:
        payload = build_delpi_commercial_gateway().list_ops_abertas()
        data = payload.get("data", payload) if isinstance(payload, dict) else payload
        return ok(data, message="OPs abertas carregadas.")
    except RuntimeError as exc:
        return fail(str(exc), 502, operation_id="list_commercial_open_ops")
    except Exception:
        logger.exception("list_commercial_open_ops_failed")
        return fail(
            "Erro interno ao carregar OPs abertas.",
            500,
            operation_id="list_commercial_open_ops",
        )

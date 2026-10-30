"""CAIO MCP tool bridge — adapters over the official Commercial use cases.

Identidade: o contexto autenticado pelo transporte MCP (delpi_auth
middleware + audience/scope) é o mesmo objeto canônico do request; o
token humano é propagado aos use cases exatamente como nas rotas REST
— sem service token, sem elevação.
AuthZ de negócio: ``commercial.access``/``commercial.manage`` +
``principal_type=="user"`` aplicados aqui, idênticos às rotas — MCP
não é autoridade; escopo de carteira segue o resolver oficial.
"""

from __future__ import annotations

import logging
from typing import Any

from mcp.types import CallToolResult

from delpi_auth.authz_core import has_any_permission
from delpi_mcp.errors import mcp_tool_result
from delpi_mcp.identity import (
    build_mcp_request as _shared_build_request,
)
from delpi_mcp.identity import (
    require_mcp_context,
)
from starlette.requests import Request

from commercial_app.application.security.commercial_permissions import (
    COMMERCIAL_ACCESS,
    COMMERCIAL_MANAGE,
    can_manage_portfolios,
    can_use_team_scope,
    has_access,
    has_billing_notify,
    has_manage,
)
from commercial_app.application.services.enrich_open_orders_kanban_service import (
    EnrichOpenOrdersKanbanService,
)
from commercial_app.application.services.filter_open_orders_by_scope_service import (
    FilterOpenOrdersByScopeService,
)
from commercial_app.application.services.resolve_commercial_customer_scope_service import (
    CommercialCustomerScope,
)
from commercial_app.application.use_cases.get_open_portfolio_horizon import (
    GetOpenPortfolioHorizonUseCase,
)
from commercial_app.application.use_cases.get_open_portfolio_summary import (
    GetOpenPortfolioSummaryUseCase,
)
from commercial_app.composition.commercial_composer import (
    build_delpi_commercial_gateway,
    build_list_customers_in_scope_use_case,
    build_manage_seller_portfolio_use_case,
    build_resolve_commercial_customer_scope_service,
)
from commercial_app.core.auth_actor import (
    actor_sub_from_request,
    current_user_from_request,
)
from commercial_app.interface.http.routes.totvs_bff_helpers import (
    merge_totvs_params,
    parse_portfolio_id_csv,
    resolve_analytics_portfolio_scope,
    unwrap_gateway_data,
)

logger = logging.getLogger(__name__)

COMMERCIAL_ACCESS_PERMISSIONS: tuple[str, ...] = (
    COMMERCIAL_ACCESS,
    COMMERCIAL_MANAGE,
)

_PROPOSAL_SORT_KEYS = {
    "ov", "interna", "cliente", "oportunidade", "versao", "data", "itens",
}


def _error_result(
    message: str,
    *,
    status_code: int = 400,
    error_code: str = "validation",
    data: dict | None = None,
) -> CallToolResult:
    payload = {
        "success": False,
        "message": message,
        "status_code": status_code,
        "error_code": error_code,
        "data": data or {},
    }
    return mcp_tool_result(payload, is_error=True)


def handle_tool_error(exc: Exception) -> CallToolResult:
    """Map adapter failures to honest typed results — never silent."""
    if isinstance(exc, PermissionError):
        msg = str(exc) or "Unauthorized"
        if msg == "Unauthorized":
            return _error_result(
                "Authentication required.",
                status_code=401,
                error_code="unauthenticated",
            )
        return _error_result(
            "Forbidden",
            status_code=403,
            error_code="forbidden",
            data={"error_kind": "authz"},
        )
    if isinstance(exc, LookupError):
        return _error_result(
            str(exc),
            status_code=404,
            error_code="not_found",
            data={"error_kind": "not_found"},
        )
    if isinstance(exc, TimeoutError):
        return _error_result(
            "Upstream timeout.",
            status_code=504,
            error_code="timeout",
        )
    if isinstance(exc, ValueError):
        return _error_result(
            str(exc),
            status_code=400,
            error_code="validation",
            data={"error_kind": "validation"},
        )
    if isinstance(exc, RuntimeError):
        return _error_result(
            str(exc) or "Upstream service error.",
            status_code=502,
            error_code="upstream_error",
        )
    logger.exception("caio_mcp_tool_error")
    return _error_result(
        "Upstream service error.",
        status_code=502,
        error_code="upstream_error",
    )


def build_mcp_request() -> Request:
    """Rebuild the adapter Request from the delpi_auth-established context."""
    context = require_mcp_context()
    return _shared_build_request(
        context=context,
        server=("commercial-api", 443),
        client=("127.0.0.1", 0),
    )


def _require_commercial_human():
    """Same gate as the REST routes: human principal + effective permission.

    Raises PermissionError — mapped by ``handle_tool_error`` (401/403).
    """
    context = require_mcp_context()
    if not context.user or not context.authorization:
        raise PermissionError("Unauthorized")
    user = context.user
    if getattr(user, "principal_type", None) != "user":
        raise PermissionError("MCP tools require a human principal.")
    if not getattr(user, "is_superadmin", False) and not has_any_permission(
        user, COMMERCIAL_ACCESS_PERMISSIONS
    ):
        raise PermissionError("Forbidden")
    return context


def _ok(data: Any, message: str = "ok") -> CallToolResult:
    return mcp_tool_result(
        {"success": True, "message": message, "data": data}, is_error=False
    )


# --- read: portfolio.me -----------------------------------------------------


def tool_portfolio_me() -> CallToolResult:
    """Caller commercial context — official ``GET /seller-portfolios/me``."""
    try:
        _require_commercial_human()
        request = build_mcp_request()
        user_id = actor_sub_from_request(request)
        if not user_id:
            raise PermissionError("Unauthorized")
        use_case = build_manage_seller_portfolio_use_case()
        portfolios = use_case.get_me_portfolios(user_id)
        serialized = use_case.serialize_portfolios(portfolios)
        user = current_user_from_request(request)
        return _ok(
            {
                "user_id": user_id,
                "portfolio": serialized[0] if serialized else None,
                "portfolios": serialized,
                "is_admin": can_manage_portfolios(user),
                "capabilities": {
                    "access": has_access(user),
                    "manage": has_manage(user),
                    "billing_notify": has_billing_notify(user),
                },
            },
            "Carteira do usuário carregada.",
        )
    except Exception as exc:
        return handle_tool_error(exc)


# --- read: customer.list ----------------------------------------------------


def tool_customer_list(
    *,
    portfolio_id: str | None = None,
    seller_id: str | None = None,
) -> CallToolResult:
    """Authorized customers in the caller's scope — ``GET /customers/in-scope``."""
    try:
        _require_commercial_human()
        request = build_mcp_request()
        user = current_user_from_request(request)
        unrestricted = can_manage_portfolios(user) or can_use_team_scope(user)
        user_id = actor_sub_from_request(request) or ""
        portfolio_ids = parse_portfolio_id_csv(portfolio_id, seller_id)
        scope = build_resolve_commercial_customer_scope_service().execute(
            user_id=user_id,
            unrestricted=unrestricted,
            portfolio_ids=portfolio_ids or None,
        )
        data = build_list_customers_in_scope_use_case().execute(scope)
        return _ok(data, "Clientes da carteira carregados.")
    except Exception as exc:
        return handle_tool_error(exc)


# --- read: open_order -------------------------------------------------------


def _open_orders_scope(request: Request, *, portfolio_id: str | None):
    user = current_user_from_request(request)
    unrestricted = can_manage_portfolios(user) or can_use_team_scope(user)
    user_id = actor_sub_from_request(request) or ""
    return build_resolve_commercial_customer_scope_service().execute(
        user_id=user_id,
        unrestricted=unrestricted,
        portfolio_id=portfolio_id,
    ).for_open_orders()


def tool_open_order_list(
    *,
    portfolio_id: str | None = None,
    seller_id: str | None = None,
    customer_centers: str | None = None,
) -> CallToolResult:
    """Open sales orders — official ``GET /open-orders/`` semantics."""
    try:
        _require_commercial_human()
        request = build_mcp_request()
        pid = (portfolio_id or seller_id or "").strip() or None
        scope = _open_orders_scope(request, portfolio_id=pid)
        payload = build_delpi_commercial_gateway().list_open_orders(
            params={"customer_centers": customer_centers}
            if customer_centers
            else None
        )
        raw = payload.get("data", payload) if isinstance(payload, dict) else {}
        data = FilterOpenOrdersByScopeService().apply(
            raw if isinstance(raw, dict) else {},
            scope,
        )
        if isinstance(data, dict):
            items_raw = data.get("items")
            items = (
                [item for item in items_raw if isinstance(item, dict)]
                if isinstance(items_raw, list)
                else []
            )
            data = {
                **data,
                **EnrichOpenOrdersKanbanService().build_payload_fields(items),
            }
        return _ok(data, "Pedidos de venda em aberto carregados.")
    except Exception as exc:
        return handle_tool_error(exc)


def tool_open_order_recently_closed(
    *,
    days: int = 30,
    portfolio_id: str | None = None,
    seller_id: str | None = None,
    customer_centers: str | None = None,
) -> CallToolResult:
    """Recently closed orders — official ``GET /open-orders/recently-closed``."""
    try:
        _require_commercial_human()
        days_i = int(days or 30)
        if not 1 <= days_i <= 90:
            raise ValueError("days deve estar entre 1 e 90.")
        request = build_mcp_request()
        pid = (portfolio_id or seller_id or "").strip() or None
        scope = _open_orders_scope(request, portfolio_id=pid)
        payload = build_delpi_commercial_gateway().list_recently_closed_orders(
            days=days_i,
            params={"customer_centers": customer_centers}
            if customer_centers
            else None,
        )
        raw = payload.get("data", payload) if isinstance(payload, dict) else {}
        data = FilterOpenOrdersByScopeService().apply(
            raw if isinstance(raw, dict) else {},
            scope,
        )
        if isinstance(data, dict) and isinstance(data.get("summary"), dict):
            data = {
                **data,
                "summary": {**data["summary"], "days": days_i},
            }
        return _ok(data, "Pedidos encerrados recentemente carregados.")
    except Exception as exc:
        return handle_tool_error(exc)


# --- read: proposal.list ----------------------------------------------------


def tool_proposal_list(
    *,
    search: str | None = None,
    sort_by: str | None = None,
    sort_dir: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> CallToolResult:
    """Commercial proposal documents — official ``GET /proposal-documents/``."""
    try:
        _require_commercial_human()
        if sort_by is not None and sort_by not in _PROPOSAL_SORT_KEYS:
            raise ValueError(
                f"sort_by inválido — use {sorted(_PROPOSAL_SORT_KEYS)}."
            )
        if sort_dir is not None and sort_dir not in ("asc", "desc"):
            raise ValueError("sort_dir inválido — use asc|desc.")
        params: dict[str, Any] = {"limit": 100, "page": max(int(page or 1), 1)}
        size = min(max(int(page_size or 20), 1), 200)
        params["page_size"] = size
        if search and str(search).strip():
            params["search"] = str(search).strip()
        if sort_by:
            params["sort_by"] = sort_by
        if sort_dir:
            params["sort_dir"] = sort_dir
        payload = build_delpi_commercial_gateway().get_commercial_proposal_document(
            "", params=params
        )
        data = payload.get("data", payload) if isinstance(payload, dict) else {}
        return _ok(data, "Propostas comerciais carregadas.")
    except Exception as exc:
        return handle_tool_error(exc)


# --- analyze ----------------------------------------------------------------


def _analytics_scope(
    request: Request,
    *,
    seller_id: str | None,
    portfolio_id: str | None,
    scope_mode: str | None,
) -> CommercialCustomerScope:
    """Canonical analytics scope — the MCP request has no query params,
    so ``scope_mode`` is always passed explicitly."""
    return resolve_analytics_portfolio_scope(
        request,
        seller_id=seller_id,
        portfolio_id=portfolio_id,
        scope_mode=scope_mode,
    )


def analyze_open_portfolio_summary(
    *,
    seller_id: str | None = None,
    portfolio_id: str | None = None,
    scope_mode: str | None = None,
    customer_codes: str | None = None,
    question: str | None = None,
) -> CallToolResult:
    """KPI-CARTEIRA — official ``GetOpenPortfolioSummaryUseCase``."""
    try:
        _require_commercial_human()
        request = build_mcp_request()
        scope = _analytics_scope(
            request,
            seller_id=seller_id,
            portfolio_id=portfolio_id,
            scope_mode=scope_mode,
        )
        payload = build_delpi_commercial_gateway().list_open_orders()
        raw = unwrap_gateway_data(payload)
        data = GetOpenPortfolioSummaryUseCase().execute(
            raw if isinstance(raw, dict) else {},
            scope,
            selected_customer_codes=customer_codes,
        )
        return _ok(
            {
                "analysis_type": "portfolio.open_summary",
                "question": question,
                "data_class": "OBSERVED",
                "scope_mode": scope_mode or "global",
                "summary": data,
                "provenance": (
                    "commercial-api official open-orders → owner use case"
                ),
            },
            "Resumo da carteira em aberto carregado.",
        )
    except Exception as exc:
        return handle_tool_error(exc)


def analyze_open_portfolio_horizon(
    *,
    seller_id: str | None = None,
    portfolio_id: str | None = None,
    scope_mode: str | None = None,
    customer_codes: str | None = None,
    question: str | None = None,
) -> CallToolResult:
    """KPI-CARTEIRA-HORIZON — official ``GetOpenPortfolioHorizonUseCase``."""
    try:
        _require_commercial_human()
        request = build_mcp_request()
        scope = _analytics_scope(
            request,
            seller_id=seller_id,
            portfolio_id=portfolio_id,
            scope_mode=scope_mode,
        )
        payload = build_delpi_commercial_gateway().list_open_orders()
        raw = unwrap_gateway_data(payload)
        data = GetOpenPortfolioHorizonUseCase().execute(
            raw if isinstance(raw, dict) else {},
            scope,
            selected_customer_codes=customer_codes,
        )
        return _ok(
            {
                "analysis_type": "portfolio.open_horizon",
                "question": question,
                "data_class": "OBSERVED",
                "scope_mode": scope_mode or "global",
                "horizon": data,
                "provenance": (
                    "commercial-api official open-orders → owner use case"
                ),
            },
            "Horizonte da carteira em aberto carregado.",
        )
    except Exception as exc:
        return handle_tool_error(exc)


def analyze_rol_summary(
    *,
    seller_id: str | None = None,
    portfolio_id: str | None = None,
    scope_mode: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    branch: str | None = None,
    customer_segment: str | None = None,
    customer_centers: str | None = None,
    customer_codes: str | None = None,
    question: str | None = None,
) -> CallToolResult:
    """ROL summary — official ``GET /analytics/rol/summary`` semantics."""
    try:
        _require_commercial_human()
        request = build_mcp_request()
        scope = _analytics_scope(
            request,
            seller_id=seller_id,
            portfolio_id=portfolio_id,
            scope_mode=scope_mode,
        )
        params: dict[str, Any] = {
            "start_date": start_date,
            "end_date": end_date,
            "branch": branch,
            "customer_segment": customer_segment,
        }
        centers = (customer_centers or "").strip()
        if centers:
            params["customer_centers"] = centers
        totvs_params = merge_totvs_params(
            scope,
            params,
            selected_customer_codes=customer_codes,
        )
        payload = build_delpi_commercial_gateway().get_commercial_analytics(
            "/rol/summary", params=totvs_params
        )
        data = unwrap_gateway_data(payload)
        return _ok(
            {
                "analysis_type": "rol.summary",
                "question": question,
                "data_class": "OBSERVED",
                "scope_mode": scope_mode or "global",
                "summary": data,
                "filters_applied": {
                    k: v for k, v in params.items() if v is not None
                },
                "provenance": (
                    "TOTVS via api-delpi commercial analytics → "
                    "commercial-api scope"
                ),
            },
            "Resumo ROL carregado.",
        )
    except Exception as exc:
        return handle_tool_error(exc)

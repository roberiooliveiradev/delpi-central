"""CAIO 2.0 — parity handlers over the official Commercial contracts.

Every handler re-uses the same use case/gateway/scope resolver the
REST route uses — MCP is an adapter, never a second implementation.
Reads/analyses return ``CallToolResult``; writes/deletes return plain
payloads raised through the same domain errors (``PermissionError``,
``LookupError``, ``ValueError``, ``RuntimeError``) so the semantic
bridge maps them identically to the routes.
"""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import quote
from datetime import datetime
from uuid import UUID

from mcp.types import CallToolResult
from starlette.requests import Request

from commercial_app.application.security.commercial_permissions import (
    can_manage_portfolios,
    can_use_team_scope,
    can_view_portfolio_billing_share,
    can_view_worklist_team,
    has_manage,
)
from commercial_app.application.use_cases.create_task_from_interaction_message import (
    CreateTaskFromInteractionMessageInput,
)
from commercial_app.application.use_cases.get_portfolio_billing_ranking import (
    GetPortfolioBillingRankingUseCase,
)
from commercial_app.application.use_cases.get_portfolio_billing_share import (
    GetPortfolioBillingShareUseCase,
)
from commercial_app.application.use_cases.manage_account_contacts import (
    CreateAccountContactInput,
)
from commercial_app.application.use_cases.manage_commercial_groups import (
    CreateCommercialGroupRequest,
    RenameCommercialGroupRequest,
)
from commercial_app.application.use_cases.manage_interaction_messages import (
    PostInteractionMessageInput,
)
from commercial_app.application.use_cases.manage_interaction_rooms import (
    ResolveInteractionRoomInput,
)
from commercial_app.application.use_cases.manage_seller_portfolio import (
    CreatePortfolioRequest,
    coverage_audit_to_dict,
    customer_shared_coverage_to_dict,
    load_summary_to_dict,
    parse_customer_assignments,
)
from commercial_app.application.use_cases.manage_worklist import (
    CreateActivityInput,
    CreateTaskInput,
    UpdateTaskInput,
)
from commercial_app.application.services.analytics_customer_codes_service import (
    AnalyticsCustomerCodesService,
)
from commercial_app.application.services.commercial_realtime_notify import (
    notify_interaction_mention,
    notify_interaction_room_activity,
    notify_worklist_changed,
)
from commercial_app.composition.commercial_composer import (
    build_attachment_repository,
    build_create_task_from_interaction_message_use_case,
    build_delpi_commercial_gateway,
    build_enqueue_task_portal_notifications_service,
    build_list_interaction_inbox_use_case,
    build_list_interaction_room_shared_items_use_case,
    build_manage_account_contacts_use_case,
    build_manage_attachments_use_case,
    build_manage_commercial_groups_use_case,
    build_manage_interaction_messages_use_case,
    build_manage_interaction_rooms_use_case,
    build_manage_seller_portfolio_use_case,
    build_manage_team_roster_use_case,
    build_manage_user_profile_use_case,
    build_manage_worklist_use_case,
    build_preview_interaction_entity_use_case,
    build_resolve_commercial_customer_scope_service,
    build_suggest_interaction_mentions_use_case,
    build_task_repository,
)
from commercial_app.core.auth_actor import (
    actor_display_name_from_request,
    actor_sub_from_request,
    current_user_from_request,
)
from commercial_app.domain.entities.seller_portfolio import SellerCustomerAssignment
from commercial_app.domain.entities.task import TaskCustomerRef
from commercial_app.infrastructure.persistence.repositories.postgres_home_favorites_repository import (
    MAX_HOME_FAVORITES,
    PostgresHomeFavoritesRepository,
    normalize_favorite_items,
)
from commercial_app.infrastructure.persistence.repositories.postgres_sla_policy_repository import (
    PostgresSlaPolicyRepository,
)
from commercial_app.interface.http.client_id import client_id_from_request
from commercial_app.interface.http.routes.customer_routes import (
    _account_detail_scope_check,
    _pairs_for_account_or_portfolio_list,
)
from commercial_app.interface.http.routes.interaction_room_routes import (
    _mentions_from_body,
)
from commercial_app.interface.http.routes.seller_portfolio_routes import (
    _verified_customer_center,
)
from commercial_app.interface.http.routes.totvs_bff_helpers import (
    merge_totvs_params,
    unwrap_gateway_data,
)
from commercial_app.interface.mcp.tool_bridge import (
    _analytics_scope,
    _ok,
    _require_commercial_human,
    build_mcp_request,
    handle_tool_error,
)

logger = logging.getLogger(__name__)


def _actor(request: Request) -> tuple[Any, str]:
    user = current_user_from_request(request)
    user_id = actor_sub_from_request(request) or ""
    return user, user_id


def _require_manage(user: Any) -> None:
    if not can_manage_portfolios(user):
        raise PermissionError("Forbidden")


def _is_manager(request: Request) -> bool:
    return can_manage_portfolios(current_user_from_request(request))


def _customer_scope(request: Request):
    """Same scope as ``customer_routes._customer_scope_for_request``."""
    user = current_user_from_request(request)
    unrestricted = can_manage_portfolios(user) or can_use_team_scope(user)
    user_id = actor_sub_from_request(request) or ""
    return build_resolve_commercial_customer_scope_service().execute(
        user_id=user_id,
        unrestricted=unrestricted,
    )


def _assignments(raw: Any):
    if not isinstance(raw, list):
        raise ValueError("customers deve ser uma lista.")
    return parse_customer_assignments(list(raw))


def _uuid(value: Any, name: str) -> UUID:
    try:
        return UUID(str(value or "").strip())
    except (ValueError, TypeError, AttributeError) as exc:
        raise ValueError(f"{name} inválido.") from exc


def _iso_datetime(value: Any, name: str) -> Any:
    """Coerce ISO-8601 date/datetime strings into ``datetime``.

    REST routes get this coercion for free via Pydantic; the semantic
    surface receives raw JSON, so strings must be parsed at the adapter
    boundary — otherwise they crash inside the owner use case and
    surface as a misleading 502 instead of a 400/valid call."""
    if value is None or isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError(
                f"{name} inválido. Use ISO 8601 "
                "(ex.: 2026-10-30T14:00:00)."
            ) from exc
    raise ValueError(f"{name} inválido.")


def _task_customers(raw: Any) -> list[TaskCustomerRef] | None:
    if raw is None:
        return None
    if not isinstance(raw, list):
        raise ValueError("customers deve ser uma lista.")
    return [
        TaskCustomerRef(
            customer_code=str(item.get("code") or "").strip(),
            customer_store=str(item.get("store") or "").strip(),
            customer_name=str(item.get("name") or "").strip() or None,
        )
        for item in raw
        if isinstance(item, dict)
        and str(item.get("code") or "").strip()
        and str(item.get("store") or "").strip()
    ]


def _notify_task(
    request: Request,
    *,
    reason: str,
    task: Any,
    existing: Any = None,
) -> None:
    source = existing if existing is not None else task
    assignees = [
        str(item) for item in (source.resolved_assignee_user_ids() or [])
    ]
    try:
        notify_worklist_changed(
            reason=reason,
            task_id=str(task.id),
            assignee_user_ids=assignees,
            actor_user_id=actor_sub_from_request(request),
            actor_display_name=actor_display_name_from_request(request),
            task_title=getattr(task, "title", None),
            actor_client_id=client_id_from_request(request),
        )
    except Exception:
        logger.exception("caio_mcp_task_notify_failed")


def _portal_task_notify(callback) -> None:
    try:
        callback()
    except Exception:
        logger.exception("caio_mcp_task_portal_notify_failed")


# --- read: portfolio detail / list / audit / coverage / load -----------------


def _portfolio_access(request: Request, portfolio: Any) -> None:
    """Route-equivalent ``_can_access_portfolio``."""
    user = current_user_from_request(request)
    if can_manage_portfolios(user):
        return
    user_id = actor_sub_from_request(request) or ""
    member_ids = {m.user_id for m in getattr(portfolio, "members", [])}
    allowed = user_id in member_ids or user_id in {
        getattr(portfolio, "owner_user_id", None),
        getattr(portfolio, "user_id", None),
    }
    if not allowed:
        raise PermissionError("Forbidden")


def tool_portfolio_get(*, portfolio_id: str) -> CallToolResult:
    try:
        _require_commercial_human()
        request = build_mcp_request()
        use_case = build_manage_seller_portfolio_use_case()
        portfolio = use_case.get_portfolio(portfolio_id)
        if portfolio is None:
            raise LookupError("Carteira não encontrada.")
        _portfolio_access(request, portfolio)
        return _ok(
            use_case.serialize_portfolio(portfolio),
            "Carteira carregada.",
        )
    except Exception as exc:
        return handle_tool_error(exc)


def tool_portfolio_list(
    *,
    active_only: bool | None = None,
    include_customers: bool | None = None,
) -> CallToolResult:
    try:
        _require_commercial_human()
        request = build_mcp_request()
        user, _ = _actor(request)
        _require_manage(user)
        force_active = bool(active_only) or (
            can_use_team_scope(user) and not can_manage_portfolios(user)
        )
        use_case = build_manage_seller_portfolio_use_case()
        portfolios = use_case.list_portfolios(
            active_only=force_active,
            include_customers=include_customers is not False,
        )
        return _ok(
            {"items": use_case.serialize_portfolios(portfolios)},
            "Carteiras carregadas.",
        )
    except Exception as exc:
        return handle_tool_error(exc)


def tool_portfolio_audit(
    *,
    portfolio_id: str,
    page: int = 1,
    page_size: int = 20,
) -> CallToolResult:
    try:
        _require_commercial_human()
        request = build_mcp_request()
        use_case = build_manage_seller_portfolio_use_case()
        portfolio = use_case.get_portfolio(portfolio_id)
        if portfolio is None:
            raise LookupError("Carteira não encontrada.")
        _portfolio_access(request, portfolio)
        payload = use_case.list_portfolio_audit(
            portfolio_id,
            page=max(int(page or 1), 1),
            page_size=min(max(int(page_size or 20), 1), 100),
        )
        return _ok(payload, "Auditoria da carteira carregada.")
    except Exception as exc:
        return handle_tool_error(exc)


def tool_portfolio_coverage_audit() -> CallToolResult:
    try:
        _require_commercial_human()
        request = build_mcp_request()
        user, _ = _actor(request)
        _require_manage(user)
        audit = build_manage_seller_portfolio_use_case().audit_customer_coverage()
        return _ok(
            coverage_audit_to_dict(audit),
            "Auditoria de cobertura carregada.",
        )
    except Exception as exc:
        return handle_tool_error(exc)


def tool_portfolio_load_summary(
    *, active_only: bool | None = None
) -> CallToolResult:
    try:
        _require_commercial_human()
        request = build_mcp_request()
        user, _ = _actor(request)
        _require_manage(user)
        summary = build_manage_seller_portfolio_use_case().summarize_portfolio_load(
            active_only=bool(active_only)
        )
        return _ok(
            load_summary_to_dict(summary),
            "Resumo de carga das carteiras carregado.",
        )
    except Exception as exc:
        return handle_tool_error(exc)


def tool_portfolio_customer_coverage(
    *,
    customers: Any,
    portfolio_ids: Any = None,
) -> CallToolResult:
    try:
        _require_commercial_human()
        request = build_mcp_request()
        keys = _assignments(customers)
        user = current_user_from_request(request)
        team_scope = can_use_team_scope(user) or can_manage_portfolios(user)
        items = build_manage_seller_portfolio_use_case().lookup_customer_shared_coverage(
            customers=keys,
            portfolio_ids=list(portfolio_ids or ()),
            actor_user_id=actor_sub_from_request(request) or "",
            team_scope=team_scope,
        )
        return _ok(
            {"items": [customer_shared_coverage_to_dict(i) for i in items]},
            "Cobertura compartilhada carregada.",
        )
    except Exception as exc:
        return handle_tool_error(exc)


# --- execute/delete: portfolio writes -----------------------------------------


def execute_portfolio_create(*, display_name: str, user_id: str | None = None,
                             customers: Any = None, user_ids: Any = None,
                             owner_user_id: str | None = None) -> dict:
    request = build_mcp_request()
    user, actor = _actor(request)
    _require_manage(user)
    uc = build_manage_seller_portfolio_use_case()
    portfolio = uc.create_portfolio(
        CreatePortfolioRequest(
            user_id=user_id or "",
            display_name=display_name,
            created_by_user_id=actor or None,
            customers=tuple(_assignments(customers or [])),
            user_ids=tuple(user_ids or ()),
            owner_user_id=owner_user_id,
        )
    )
    return uc.serialize_portfolio(portfolio)


def execute_portfolio_update(*, portfolio_id: str,
                             display_name: str | None = None,
                             active: bool | None = None) -> dict:
    request = build_mcp_request()
    user, actor = _actor(request)
    _require_manage(user)
    uc = build_manage_seller_portfolio_use_case()
    portfolio = uc.update_portfolio(
        portfolio_id=portfolio_id,
        display_name=display_name,
        active=active,
        actor_user_id=actor or None,
    )
    return uc.serialize_portfolio(portfolio)


def execute_portfolio_customers_replace(*, portfolio_id: str,
                                        customers: Any) -> dict:
    request = build_mcp_request()
    user, actor = _actor(request)
    _require_manage(user)
    uc = build_manage_seller_portfolio_use_case()
    portfolio = uc.replace_customers(
        portfolio_id=portfolio_id,
        customers=_assignments(customers or []),
        actor_user_id=actor or None,
    )
    return uc.serialize_portfolio(portfolio)


def execute_portfolio_customer_add(*, portfolio_id: str, customer_code: str,
                                   customer_store: str,
                                   customer_name: str | None = None,
                                   customer_center: str | None = None) -> dict:
    request = build_mcp_request()
    user, actor = _actor(request)
    _require_manage(user)
    uc = build_manage_seller_portfolio_use_case()
    result = uc.add_customer(
        portfolio_id=portfolio_id,
        customer=SellerCustomerAssignment(
            customer_code=customer_code.strip(),
            customer_store=customer_store.strip(),
            customer_name=(customer_name or "").strip() or None,
            customer_center=_verified_customer_center(
                customer_code, customer_store, customer_center
            ),
        ),
        actor_user_id=actor or None,
    )
    return uc.serialize_add_customer_result(result)


def execute_portfolio_customer_remove(*, portfolio_id: str,
                                      customer_code: str, customer_store: str,
                                      customer_center: Any = None) -> dict:
    request = build_mcp_request()
    user, actor = _actor(request)
    _require_manage(user)
    uc = build_manage_seller_portfolio_use_case()
    portfolio = uc.remove_customer(
        portfolio_id=portfolio_id,
        customer_code=customer_code,
        customer_store=customer_store,
        actor_user_id=actor or None,
        match_center=customer_center is not None,
        customer_center=customer_center,
    )
    return uc.serialize_portfolio(portfolio)


def execute_portfolio_members_replace(*, portfolio_id: str,
                                      members: Any) -> dict:
    request = build_mcp_request()
    user, actor = _actor(request)
    _require_manage(user)
    uc = build_manage_seller_portfolio_use_case()
    normalized = [
        {"user_id": m.get("user_id"), "role": m.get("role") or "member"}
        for m in (members or [])
        if isinstance(m, dict)
    ]
    portfolio = uc.replace_members(
        portfolio_id=portfolio_id,
        members=normalized,
        actor_user_id=actor or None,
    )
    return uc.serialize_portfolio(portfolio)


def execute_portfolio_member_add(*, portfolio_id: str, user_id: str,
                                 role: str = "member") -> dict:
    request = build_mcp_request()
    user, actor = _actor(request)
    _require_manage(user)
    uc = build_manage_seller_portfolio_use_case()
    portfolio = uc.add_member(
        portfolio_id=portfolio_id,
        user_id=user_id,
        role=role or "member",
        actor_user_id=actor or None,
    )
    return uc.serialize_portfolio(portfolio)


def execute_portfolio_member_remove(*, portfolio_id: str,
                                    user_id: str) -> dict:
    request = build_mcp_request()
    user, actor = _actor(request)
    _require_manage(user)
    uc = build_manage_seller_portfolio_use_case()
    portfolio = uc.remove_member(
        portfolio_id=portfolio_id,
        user_id=user_id,
        actor_user_id=actor or None,
    )
    return uc.serialize_portfolio(portfolio)


def execute_portfolio_owner_set(*, portfolio_id: str, user_id: str) -> dict:
    request = build_mcp_request()
    user, actor = _actor(request)
    _require_manage(user)
    uc = build_manage_seller_portfolio_use_case()
    portfolio = uc.set_owner(
        portfolio_id=portfolio_id,
        owner_user_id=user_id,
        actor_user_id=actor or None,
    )
    return uc.serialize_portfolio(portfolio)


def execute_portfolio_transfer(*, source_portfolio_id: str,
                               target_portfolio_id: str, customers: Any,
                               reason_note: str) -> dict:
    request = build_mcp_request()
    user, actor = _actor(request)
    _require_manage(user)
    uc = build_manage_seller_portfolio_use_case()
    source, target = uc.transfer_customers(
        source_portfolio_id=source_portfolio_id,
        target_portfolio_id=target_portfolio_id,
        customers=_assignments(customers or []),
        reason_note=reason_note,
        actor_user_id=actor or None,
    )
    return {
        "source": uc.serialize_portfolio(source),
        "target": uc.serialize_portfolio(target),
    }


def execute_portfolio_transfer_bulk(*, source_portfolio_id: str,
                                    target_portfolio_id: str, customers: Any,
                                    reason_note: str) -> dict:
    request = build_mcp_request()
    user, actor = _actor(request)
    _require_manage(user)
    uc = build_manage_seller_portfolio_use_case()
    result = uc.transfer_customers_bulk(
        source_portfolio_id=source_portfolio_id,
        target_portfolio_id=target_portfolio_id,
        customers=_assignments(customers or []),
        reason_note=reason_note,
        actor_user_id=actor or None,
    )
    return uc.serialize_bulk_transfer_result(result)


def delete_portfolio_deactivate(*, portfolio_id: str) -> dict:
    request = build_mcp_request()
    user, actor = _actor(request)
    _require_manage(user)
    uc = build_manage_seller_portfolio_use_case()
    portfolio = uc.deactivate_portfolio(
        portfolio_id, actor_user_id=actor or None
    )
    return uc.serialize_portfolio(portfolio)


def delete_portfolio_purge(*, portfolio_id: str) -> dict:
    request = build_mcp_request()
    user, actor = _actor(request)
    _require_manage(user)
    uc = build_manage_seller_portfolio_use_case()
    portfolio = uc.purge_portfolio(
        portfolio_id, actor_user_id=actor or None
    )
    return uc.serialize_portfolio(portfolio)


def portfolio_delete_impact(*, capability: str, portfolio_id: str) -> dict:
    """Prepare-phase impact for portfolio.deactivate|purge."""
    uc = build_manage_seller_portfolio_use_case()
    portfolio = uc.get_portfolio(portfolio_id)
    if portfolio is None:
        raise LookupError("Carteira não encontrada.")
    return {
        "portfolio_id": portfolio_id,
        "display_name": getattr(portfolio, "display_name", None),
        "active": getattr(portfolio, "active", None),
        "customer_count": len(getattr(portfolio, "customers", []) or []),
        "member_count": len(getattr(portfolio, "members", []) or []),
        "effect": (
            "Desativação reversível da carteira."
            if capability == "portfolio.deactivate"
            else "Exclusão permanente da carteira inativa."
        ),
    }


# --- read: customer operations -------------------------------------------------


def tool_customer_search(*, q: str | None = None,
                         include_blocked: bool | None = None,
                         page: int = 1, page_size: int = 20) -> CallToolResult:
    try:
        _require_commercial_human()
        payload = build_delpi_commercial_gateway().search_active_customers(
            params={
                "q": q,
                "page": max(int(page or 1), 1),
                "page_size": min(max(int(page_size or 20), 1), 100),
                "include_blocked": str(
                    include_blocked is not False
                ).lower(),
            },
        )
        data = payload.get("data", payload) if isinstance(payload, dict) else {}
        return _ok(data, "Clientes encontrados.")
    except Exception as exc:
        return handle_tool_error(exc)


def tool_customer_enrichment(*, customers: Any,
                             window_days: int | None = None,
                             nature: str | None = None) -> CallToolResult:
    try:
        _require_commercial_human()
        request = build_mcp_request()
        scope = _customer_scope(request)
        assignments = _assignments(customers or [])
        allowed_pairs = _pairs_for_account_or_portfolio_list(
            scope,
            [(a.customer_code, a.customer_store) for a in assignments],
        )
        if not allowed_pairs:
            return _ok(
                {"items": [], "customer_count": 0},
                "Nenhum cliente autorizado no escopo.",
            )
        payload: dict[str, Any] = {
            "customers": [
                {"customer_code": c, "customer_store": s}
                for c, s in allowed_pairs
            ]
        }
        if window_days:
            payload["window_days"] = int(window_days)
        if nature:
            payload["nature"] = nature
        result = build_delpi_commercial_gateway().enrich_portfolio_customers(
            payload=payload
        )
        data = result.get("data", result) if isinstance(result, dict) else {}
        return _ok(data, "Clientes enriquecidos.")
    except Exception as exc:
        return handle_tool_error(exc)


def tool_customer_billing_series(*, customers: Any,
                                 **params: Any) -> CallToolResult:
    try:
        _require_commercial_human()
        request = build_mcp_request()
        scope = _customer_scope(request)
        assignments = _assignments(customers or [])
        allowed_pairs = _pairs_for_account_or_portfolio_list(
            scope,
            [(a.customer_code, a.customer_store) for a in assignments],
        )
        payload: dict[str, Any] = {
            "customers": [
                {"customer_code": c, "customer_store": s}
                for c, s in allowed_pairs
            ],
            "months": min(max(int(params.get("months") or 12), 1), 24),
        }
        for key in (
            "start_date", "end_date", "granularity", "nature", "metric",
            "product_codes", "product_groups", "market", "customer_centers",
        ):
            if params.get(key) is not None:
                payload[key] = params[key]
        if not allowed_pairs:
            return _ok(
                {
                    "months": payload["months"],
                    "customer_count": 0,
                    "points": [],
                    "billingNature": payload.get("nature") or "gross",
                },
                "Nenhum cliente autorizado no escopo.",
            )
        result = build_delpi_commercial_gateway().list_customer_billing_series(
            payload=payload
        )
        data = result.get("data", result) if isinstance(result, dict) else {}
        return _ok(data, "Série de faturamento carregada.")
    except Exception as exc:
        return handle_tool_error(exc)


def tool_customer_center_assignments() -> CallToolResult:
    try:
        _require_commercial_human()
        request = build_mcp_request()
        scope = _customer_scope(request)
        params: dict[str, Any] = {}
        if scope.allowed_customers is not None:
            codes = sorted(
                {code for code, _store in scope.allowed_customers if code}
            )
            params["customer_codes"] = ",".join(codes)
        payload = build_delpi_commercial_gateway().get_commercial_analytics(
            "/customer-center-assignments", params=params
        )
        data = payload.get("data", payload) if isinstance(payload, dict) else {}
        return _ok(data, "Centros do cliente carregados.")
    except Exception as exc:
        return handle_tool_error(exc)


def tool_customer_outbound_invoices(
    *,
    customer_code: str,
    customer_store: str,
    start_date: str | None = None,
    end_date: str | None = None,
    page: int = 1,
    page_size: int = 20,
    situation: str | None = None,
    search: str | None = None,
    customer_centers: str | None = None,
    branch: str | None = None,
) -> CallToolResult:
    try:
        _require_commercial_human()
        result = build_delpi_commercial_gateway().list_customer_outbound_invoices(
            customer_code=customer_code,
            customer_store=customer_store,
            params={
                "start_date": start_date,
                "end_date": end_date,
                "page": max(int(page or 1), 1),
                "page_size": min(max(int(page_size or 20), 1), 100),
                "situation": situation or "all",
                "search": search,
                "branch": branch,
                **(
                    {"customer_centers": customer_centers}
                    if customer_centers
                    else {}
                ),
            },
        )
        data = result.get("data", result) if isinstance(result, dict) else {}
        return _ok(data, "Notas de saída carregadas.")
    except Exception as exc:
        return handle_tool_error(exc)


def tool_customer_outbound_invoice(
    *,
    customer_code: str,
    customer_store: str,
    branch: str,
    invoice_number: str,
    invoice_series: str,
) -> CallToolResult:
    try:
        _require_commercial_human()
        result = build_delpi_commercial_gateway().get_outbound_invoice(
            branch=branch,
            invoice_number=invoice_number,
            invoice_series=invoice_series,
        )
        data = result.get("data", result) if isinstance(result, dict) else {}
        return _ok(data, "Nota fiscal carregada.")
    except Exception as exc:
        return handle_tool_error(exc)


def tool_customer_open_orders(
    *,
    customer_code: str,
    customer_store: str,
    customer_centers: str | None = None,
    branch: str | None = None,
) -> CallToolResult:
    try:
        _require_commercial_human()
        params: dict[str, Any] = {}
        if customer_centers:
            params["customer_centers"] = customer_centers
        if branch:
            params["branch"] = branch
        result = build_delpi_commercial_gateway().list_open_orders_by_customer(
            customer_code=customer_code,
            customer_store=customer_store,
            params=params or None,
        )
        data = result.get("data", result) if isinstance(result, dict) else {}
        return _ok(data, "Pedidos em aberto do cliente carregados.")
    except Exception as exc:
        return handle_tool_error(exc)


def tool_customer_contacts(
    *, customer_code: str, customer_store: str
) -> CallToolResult:
    try:
        _require_commercial_human()
        request = build_mcp_request()
        items = build_manage_account_contacts_use_case().list(
            customer_code=customer_code,
            customer_store=customer_store,
            scope_check=_account_detail_scope_check(request),
        )
        totvs_contact = (
            build_delpi_commercial_gateway().fetch_totvs_customer_contact(
                customer_code=customer_code,
                customer_store=customer_store,
            )
        )
        return _ok(
            {
                "items": [item.to_dict() for item in items],
                "totvs_contact": totvs_contact,
            },
            "Contatos do cliente carregados.",
        )
    except Exception as exc:
        return handle_tool_error(exc)


def tool_customer_account_audit(
    *,
    customer_code: str,
    customer_store: str,
    page: int = 1,
    page_size: int = 20,
    limit: int | None = None,
) -> CallToolResult:
    try:
        _require_commercial_human()
        request = build_mcp_request()
        payload = build_manage_account_contacts_use_case().list_account_audit(
            customer_code=customer_code,
            customer_store=customer_store,
            scope_check=_account_detail_scope_check(request),
            page=max(int(page or 1), 1),
            page_size=min(max(int(limit or page_size or 20), 1), 100),
        )
        return _ok(payload, "Auditoria da conta carregada.")
    except Exception as exc:
        return handle_tool_error(exc)


# --- read: misc single-purpose ------------------------------------------------


def tool_customer_center_list(
    *,
    seller_id: str | None = None,
    portfolio_id: str | None = None,
    scope_mode: str | None = None,
) -> CallToolResult:
    try:
        _require_commercial_human()
        request = build_mcp_request()
        scope = _analytics_scope(
            request,
            seller_id=seller_id,
            portfolio_id=portfolio_id,
            scope_mode=scope_mode,
        )
        params: dict[str, Any] = {}
        codes = AnalyticsCustomerCodesService.codes_param(scope)
        if codes is not None:
            params["customer_codes"] = codes
        payload = build_delpi_commercial_gateway().get_commercial_analytics(
            "/customer-centers", params=params
        )
        return _ok(
            unwrap_gateway_data(payload),
            "Centros do cliente carregados.",
        )
    except Exception as exc:
        return handle_tool_error(exc)


def tool_open_ops() -> CallToolResult:
    try:
        _require_commercial_human()
        payload = build_delpi_commercial_gateway().list_ops_abertas()
        data = payload.get("data", payload) if isinstance(payload, dict) else payload
        return _ok(data, "OPs abertas carregadas.")
    except Exception as exc:
        return handle_tool_error(exc)


def tool_proposal_get(*, proposta_interna: str) -> CallToolResult:
    try:
        _require_commercial_human()
        encoded = quote(str(proposta_interna).strip(), safe="")
        payload = build_delpi_commercial_gateway().get_commercial_proposal_document(
            f"/{encoded}"
        )
        data = payload.get("data", payload) if isinstance(payload, dict) else {}
        if isinstance(data, dict):
            data.setdefault(
                "document_url",
                f"/proposal-documents/{encoded}/pdf",
            )
        return _ok(data, "Proposta carregada.")
    except Exception as exc:
        return handle_tool_error(exc)


def tool_proposal_analytics_list(
    *,
    seller_id: str | None = None,
    portfolio_id: str | None = None,
    scope_mode: str | None = None,
    account_customer_code: str | None = None,
    customer_codes: str | None = None,
    page: int = 1,
    page_size: int = 20,
    **params: Any,
) -> CallToolResult:
    try:
        _require_commercial_human()
        request = build_mcp_request()
        scope = _analytics_scope(
            request,
            seller_id=seller_id,
            portfolio_id=portfolio_id,
            scope_mode=scope_mode,
        )
        base: dict[str, Any] = {
            key: params.get(key)
            for key in (
                "start_date", "end_date", "branch", "customer_segment",
                "granularity", "status", "search", "product_code",
                "product_group", "sort_by", "sort_dir",
            )
        }
        base["page"] = max(int(page or 1), 1)
        base["page_size"] = min(max(int(page_size or 20), 1), 100)
        totvs = merge_totvs_params(
            scope,
            base,
            account_customer_code=account_customer_code,
            selected_customer_codes=customer_codes,
        )
        payload = build_delpi_commercial_gateway().get_commercial_analytics(
            "/proposals", params=totvs
        )
        return _ok(
            unwrap_gateway_data(payload),
            "Propostas carregadas.",
        )
    except Exception as exc:
        return handle_tool_error(exc)


def tool_proposal_analytics_get(
    *,
    proposal_number: str,
    branch: str,
    revision: str | None = None,
    seller_id: str | None = None,
    portfolio_id: str | None = None,
    scope_mode: str | None = None,
) -> CallToolResult:
    try:
        _require_commercial_human()
        request = build_mcp_request()
        scope = _analytics_scope(
            request,
            seller_id=seller_id,
            portfolio_id=portfolio_id,
            scope_mode=scope_mode,
        )
        totvs = merge_totvs_params(
            scope, {"branch": branch, "revision": revision}
        )
        encoded = quote(str(proposal_number).strip(), safe="")
        payload = build_delpi_commercial_gateway().get_commercial_analytics(
            f"/proposals/{encoded}", params=totvs
        )
        return _ok(
            unwrap_gateway_data(payload),
            "Proposta carregada.",
        )
    except Exception as exc:
        return handle_tool_error(exc)


def tool_proposal_history_events(
    *,
    proposal_number: str,
    branch: str,
    revision: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    seller_id: str | None = None,
    portfolio_id: str | None = None,
    scope_mode: str | None = None,
) -> CallToolResult:
    try:
        _require_commercial_human()
        request = build_mcp_request()
        scope = _analytics_scope(
            request,
            seller_id=seller_id,
            portfolio_id=portfolio_id,
            scope_mode=scope_mode,
        )
        totvs = merge_totvs_params(
            scope,
            {
                "branch": branch,
                "revision": revision,
                "start_date": start_date,
                "end_date": end_date,
            },
        )
        encoded = quote(str(proposal_number).strip(), safe="")
        payload = build_delpi_commercial_gateway().get_commercial_analytics(
            f"/proposals/{encoded}/history/events", params=totvs
        )
        return _ok(
            unwrap_gateway_data(payload),
            "Histórico da proposta carregado.",
        )
    except Exception as exc:
        return handle_tool_error(exc)


# --- read: worklist / tasks / activities ----------------------------------------


def tool_worklist_mine(
    *,
    scope: str | None = None,
    assignee_user_id: str | None = None,
) -> CallToolResult:
    try:
        _require_commercial_human()
        request = build_mcp_request()
        _, user_id = _actor(request)
        if not user_id:
            raise PermissionError("Unauthorized")
        user = current_user_from_request(request)
        normalized = (scope or "mine").strip().lower()
        data = build_manage_worklist_use_case().get_worklist(
            user_id=user_id,
            scope="team" if normalized == "team" else "mine",
            assignee_user_id=assignee_user_id,
            actor_is_portfolio_manager=(
                can_view_worklist_team(user) or can_manage_portfolios(user)
            ),
        )
        return _ok(data, "Worklist carregada.")
    except Exception as exc:
        return handle_tool_error(exc)


def tool_worklist_done(
    *,
    scope: str | None = None,
    assignee_user_id: str | None = None,
    limit: int = 50,
) -> CallToolResult:
    try:
        _require_commercial_human()
        request = build_mcp_request()
        _, user_id = _actor(request)
        if not user_id:
            raise PermissionError("Unauthorized")
        user = current_user_from_request(request)
        normalized = (scope or "mine").strip().lower()
        data = build_manage_worklist_use_case().get_completed_worklist(
            user_id=user_id,
            scope="team" if normalized == "team" else "mine",
            assignee_user_id=assignee_user_id,
            actor_is_portfolio_manager=(
                can_view_worklist_team(user) or can_manage_portfolios(user)
            ),
            limit=min(max(int(limit or 50), 1), 100),
        )
        return _ok(data, "Tarefas concluídas carregadas.")
    except Exception as exc:
        return handle_tool_error(exc)


def tool_task_list(*, status: str | None = "open") -> CallToolResult:
    try:
        _require_commercial_human()
        request = build_mcp_request()
        _, user_id = _actor(request)
        if not user_id:
            raise PermissionError("Unauthorized")
        items = build_manage_worklist_use_case().list_tasks(
            user_id=user_id, status=status
        )
        return _ok(
            {"items": [item.to_dict() for item in items]},
            "Tarefas carregadas.",
        )
    except Exception as exc:
        return handle_tool_error(exc)


def tool_activity_list(
    *,
    customer_code: str,
    customer_store: str,
    limit: int = 50,
) -> CallToolResult:
    try:
        _require_commercial_human()
        items = build_manage_worklist_use_case().list_customer_activities(
            customer_code=customer_code.strip(),
            customer_store=customer_store.strip(),
            limit=min(max(int(limit or 50), 1), 100),
        )
        return _ok(
            {"items": [item.to_dict() for item in items]},
            "Atividades carregadas.",
        )
    except Exception as exc:
        return handle_tool_error(exc)


# --- execute/delete: worklist ---------------------------------------------------


def execute_task_create(
    *,
    title: str,
    description: str | None = None,
    task_type: str = "follow_up",
    priority: str = "normal",
    due_at: Any = None,
    customer_code: str | None = None,
    customer_store: str | None = None,
    customers: Any = None,
    assignee_user_id: str | None = None,
    assignee_user_ids: Any = None,
    assignee_group_ids: Any = None,
    related_entity_type: str | None = None,
    related_entity_id: str | None = None,
    source_interaction_message_id: Any = None,
) -> dict:
    request = build_mcp_request()
    _, user_id = _actor(request)
    if not user_id:
        raise PermissionError("Unauthorized")
    source_mid = None
    if source_interaction_message_id:
        source_mid = _uuid(
            source_interaction_message_id, "source_interaction_message_id"
        )
    task = build_manage_worklist_use_case().create_task(
        user_id=user_id,
        data=CreateTaskInput(
            title=title,
            description=description,
            task_type=task_type,
            priority=priority,
            due_at=_iso_datetime(due_at, "due_at"),
            customer_code=customer_code,
            customer_store=customer_store,
            assignee_user_id=assignee_user_id,
            assignee_user_ids=list(assignee_user_ids) if assignee_user_ids else None,
            assignee_group_ids=list(assignee_group_ids) if assignee_group_ids else None,
            customers=_task_customers(customers),
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            source_interaction_message_id=source_mid,
        ),
        actor_is_portfolio_manager=_is_manager(request),
    )
    _notify_task(request, reason="task.created", task=task)
    _portal_task_notify(
        lambda: build_enqueue_task_portal_notifications_service().on_task_created(
            task=task, actor_user_id=user_id
        )
    )
    return task.to_dict()


def execute_task_update(*, task_id: str, **fields: Any) -> dict:
    request = build_mcp_request()
    _, user_id = _actor(request)
    if not user_id:
        raise PermissionError("Unauthorized")
    tid = _uuid(task_id, "task_id")
    existing = build_task_repository().get_by_id(tid)
    task = build_manage_worklist_use_case().update_task(
        user_id=user_id,
        task_id=tid,
        data=UpdateTaskInput(
            title=fields.get("title"),
            description=fields.get("description"),
            task_type=fields.get("task_type") or "follow_up",
            priority=fields.get("priority") or "normal",
            due_at=_iso_datetime(fields.get("due_at"), "due_at"),
            customer_code=fields.get("customer_code"),
            customer_store=fields.get("customer_store"),
            assignee_user_id=fields.get("assignee_user_id"),
            assignee_user_ids=(
                list(fields["assignee_user_ids"])
                if fields.get("assignee_user_ids")
                else None
            ),
            assignee_group_ids=(
                list(fields["assignee_group_ids"])
                if fields.get("assignee_group_ids")
                else None
            ),
            customers=_task_customers(fields.get("customers")),
        ),
        actor_is_portfolio_manager=_is_manager(request),
    )
    _notify_task(
        request, reason="task.updated", task=task, existing=existing
    )
    if existing is not None:
        prev_users = list(existing.resolved_assignee_user_ids())
        prev_groups = list(existing.resolved_assignee_group_ids())
        curr_users = list(task.resolved_assignee_user_ids())
        curr_groups = list(task.resolved_assignee_group_ids())
        if set(prev_users) != set(curr_users) or set(prev_groups) != set(curr_groups):
            _portal_task_notify(
                lambda: build_enqueue_task_portal_notifications_service().on_task_assignees_changed(
                    task=task,
                    actor_user_id=user_id,
                    previous_user_ids=prev_users,
                    previous_group_ids=prev_groups,
                )
            )
    return task.to_dict()


def execute_task_complete(*, task_id: str) -> dict:
    request = build_mcp_request()
    _, user_id = _actor(request)
    if not user_id:
        raise PermissionError("Unauthorized")
    task = build_manage_worklist_use_case().complete_task(
        user_id=user_id,
        task_id=_uuid(task_id, "task_id"),
        actor_is_portfolio_manager=_is_manager(request),
    )
    _notify_task(request, reason="task.completed", task=task)
    _portal_task_notify(
        lambda: build_enqueue_task_portal_notifications_service().on_task_completed(
            task=task, actor_user_id=user_id
        )
    )
    return task.to_dict()


def execute_task_defer(*, task_id: str, due_at: Any) -> dict:
    request = build_mcp_request()
    _, user_id = _actor(request)
    if not user_id:
        raise PermissionError("Unauthorized")
    task = build_manage_worklist_use_case().defer_task(
        user_id=user_id,
        task_id=_uuid(task_id, "task_id"),
        due_at=_iso_datetime(due_at, "due_at"),
        actor_is_portfolio_manager=_is_manager(request),
    )
    _notify_task(request, reason="task.deferred", task=task)
    return task.to_dict()


def execute_task_reassign(*, task_id: str, **fields: Any) -> dict:
    request = build_mcp_request()
    _, user_id = _actor(request)
    if not user_id:
        raise PermissionError("Unauthorized")
    tid = _uuid(task_id, "task_id")
    existing = build_task_repository().get_by_id(tid)
    task = build_manage_worklist_use_case().reassign_task(
        user_id=user_id,
        task_id=tid,
        new_assignee_user_id=fields.get("assignee_user_id"),
        assignee_user_ids=(
            list(fields["assignee_user_ids"])
            if fields.get("assignee_user_ids")
            else None
        ),
        assignee_group_ids=(
            list(fields["assignee_group_ids"])
            if fields.get("assignee_group_ids")
            else None
        ),
        actor_is_portfolio_manager=_is_manager(request),
    )
    _notify_task(
        request, reason="task.reassigned", task=task, existing=existing
    )
    prev_users = list(existing.resolved_assignee_user_ids()) if existing else []
    prev_groups = list(existing.resolved_assignee_group_ids()) if existing else []
    _portal_task_notify(
        lambda: build_enqueue_task_portal_notifications_service().on_task_assignees_changed(
            task=task,
            actor_user_id=user_id,
            previous_user_ids=prev_users,
            previous_group_ids=prev_groups,
        )
    )
    return task.to_dict()


def execute_task_from_message(
    *,
    room_id: str,
    message_id: str,
    description: str | None = None,
    assignee_user_id: str | None = None,
    assignee_user_ids: Any = None,
    priority: str = "normal",
    task_type: str = "follow_up",
    **_ignored: Any,
) -> dict:
    request = build_mcp_request()
    _, actor = _actor(request)
    if not actor:
        raise PermissionError("Unauthorized")
    result = build_create_task_from_interaction_message_use_case().execute(
        CreateTaskFromInteractionMessageInput(
            room_id=_uuid(room_id, "room_id"),
            message_id=_uuid(message_id, "message_id"),
            actor_user_id=actor,
            description=description,
            assignee_user_id=assignee_user_id,
            assignee_user_ids=(
                tuple(assignee_user_ids) if assignee_user_ids else None
            ),
            priority=priority,
            task_type=task_type,
        ),
        actor_is_portfolio_manager=_is_manager(request),
    )
    try:
        notify_interaction_room_activity(
            reason="created",
            room_id=str(result.task_ref_message.room_id),
            message=result.task_ref_message,
            actor_user_id=actor,
            actor_display_name=actor_display_name_from_request(request),
            actor_client_id=client_id_from_request(request),
        )
    except Exception:
        logger.exception("caio_mcp_task_from_message_notify_failed")
    return result.to_dict() if hasattr(result, "to_dict") else {
        "room_id": room_id,
        "message_id": message_id,
    }


def execute_activity_create(
    *,
    activity_type: str,
    subject: str,
    body: str | None = None,
    occurred_at: Any = None,
    customer_code: str | None = None,
    customer_store: str | None = None,
    task_id: Any = None,
) -> dict:
    request = build_mcp_request()
    _, user_id = _actor(request)
    if not user_id:
        raise PermissionError("Unauthorized")
    activity = build_manage_worklist_use_case().create_activity(
        user_id=user_id,
        data=CreateActivityInput(
            activity_type=activity_type,
            subject=subject,
            body=body,
            occurred_at=_iso_datetime(occurred_at, "occurred_at"),
            customer_code=customer_code,
            customer_store=customer_store,
            task_id=_uuid(task_id, "task_id") if task_id else None,
        ),
    )
    return activity.to_dict()


def delete_task(*, task_id: str) -> dict:
    request = build_mcp_request()
    _, user_id = _actor(request)
    if not user_id:
        raise PermissionError("Unauthorized")
    task = build_manage_worklist_use_case().delete_task(
        user_id=user_id,
        task_id=_uuid(task_id, "task_id"),
        actor_is_portfolio_manager=_is_manager(request),
    )
    _notify_task(request, reason="task.deleted", task=task)
    return task.to_dict()


def task_delete_impact(*, task_id: str) -> dict:
    task = build_task_repository().get_by_id(_uuid(task_id, "task_id"))
    if task is None:
        raise LookupError("Tarefa não encontrada.")
    data = task.to_dict() if hasattr(task, "to_dict") else {}
    return {
        "task_id": task_id,
        "title": data.get("title"),
        "status": data.get("status"),
        "effect": "Exclusão da tarefa.",
    }


# --- read/execute/delete: groups ------------------------------------------------


def tool_group_list(*, active_only: bool | None = None) -> CallToolResult:
    try:
        _require_commercial_human()
        request = build_mcp_request()
        user, _ = _actor(request)
        _require_manage(user)
        use_case = build_manage_commercial_groups_use_case()
        groups = use_case.list_groups(active_only=bool(active_only))
        return _ok(
            {"items": use_case.serialize_groups(groups)},
            "Grupos carregados.",
        )
    except Exception as exc:
        return handle_tool_error(exc)


def tool_group_get(*, group_id: str) -> CallToolResult:
    try:
        _require_commercial_human()
        request = build_mcp_request()
        user, _ = _actor(request)
        _require_manage(user)
        use_case = build_manage_commercial_groups_use_case()
        group = use_case.get_group(group_id)
        return _ok(use_case.serialize_group(group), "Grupo carregado.")
    except Exception as exc:
        return handle_tool_error(exc)


def execute_group_create(
    *,
    name: str,
    kind: str | None = None,
    sort_order: int | None = None,
    user_ids: Any = None,
) -> dict:
    request = build_mcp_request()
    user, actor = _actor(request)
    _require_manage(user)
    use_case = build_manage_commercial_groups_use_case()
    group = use_case.create_group(
        CreateCommercialGroupRequest(
            name=name,
            kind=kind or "custom",
            sort_order=sort_order if sort_order is not None else 0,
            created_by_user_id=actor or None,
        )
    )
    if user_ids:
        # Mirrors the REST sequence: create the group, then replace
        # members — the owner create contract takes no member list.
        group = use_case.replace_members(
            group_id=group.id,
            user_ids=list(user_ids),
            actor_user_id=actor or None,
        )
    return use_case.serialize_group(group)


def execute_group_rename(*, group_id: str, name: str) -> dict:
    request = build_mcp_request()
    user, actor = _actor(request)
    _require_manage(user)
    use_case = build_manage_commercial_groups_use_case()
    group = use_case.rename_group(
        RenameCommercialGroupRequest(
            group_id=group_id,
            name=name,
            actor_user_id=actor or None,
        )
    )
    return use_case.serialize_group(group)


def execute_group_members_replace(
    *, group_id: str, user_ids: Any
) -> dict:
    request = build_mcp_request()
    user, actor = _actor(request)
    _require_manage(user)
    use_case = build_manage_commercial_groups_use_case()
    group = use_case.replace_members(
        group_id=group_id,
        user_ids=list(user_ids or ()),
        actor_user_id=actor or None,
    )
    return use_case.serialize_group(group)


def execute_group_member_add(*, group_id: str, user_id: str) -> dict:
    request = build_mcp_request()
    user, actor = _actor(request)
    _require_manage(user)
    use_case = build_manage_commercial_groups_use_case()
    group = use_case.add_member(
        group_id=group_id,
        user_id=user_id,
        actor_user_id=actor or None,
    )
    return use_case.serialize_group(group)


def execute_group_member_remove(*, group_id: str, user_id: str) -> dict:
    request = build_mcp_request()
    user, actor = _actor(request)
    _require_manage(user)
    use_case = build_manage_commercial_groups_use_case()
    group = use_case.remove_member(
        group_id=group_id,
        user_id=user_id,
        actor_user_id=actor or None,
    )
    return use_case.serialize_group(group)


def delete_group(*, group_id: str) -> dict:
    request = build_mcp_request()
    user, actor = _actor(request)
    _require_manage(user)
    build_manage_commercial_groups_use_case().delete_group(
        group_id=group_id,
        actor_user_id=actor or None,
    )
    return {"group_id": group_id, "deleted": True}


def group_delete_impact(*, group_id: str) -> dict:
    use_case = build_manage_commercial_groups_use_case()
    group = use_case.get_group(group_id)
    data = use_case.serialize_group(group)
    return {
        "group_id": group_id,
        "name": data.get("name"),
        "member_count": len(
            data.get("members") or data.get("user_ids") or []
        ),
        "effect": "Exclusão do grupo comercial.",
    }


# --- read/execute/delete: SLA policies -------------------------------------------


def tool_sla_policy_list(
    *, include_inactive: bool | None = None
) -> CallToolResult:
    try:
        _require_commercial_human()
        request = build_mcp_request()
        user = current_user_from_request(request)
        if include_inactive and not has_manage(user):
            raise PermissionError("Forbidden")
        items = PostgresSlaPolicyRepository().list_policies(
            include_inactive=bool(include_inactive)
        )
        return _ok(
            {
                "items": items,
                "configured": any(item.get("active") for item in items),
                "includeInactive": bool(include_inactive),
            },
            "Políticas de SLA.",
        )
    except Exception as exc:
        return handle_tool_error(exc)


def execute_sla_policy_create(
    *,
    code: str,
    name: str,
    appliesTo: str | None = None,
    durationHours: Any = None,
    calendarCode: str | None = None,
    active: bool | None = None,
) -> dict:
    request = build_mcp_request()
    user, _ = _actor(request)
    _require_manage(user)
    return PostgresSlaPolicyRepository().create(
        code=code,
        name=name,
        applies_to=appliesTo,
        duration_hours=durationHours,
        calendar_code=calendarCode,
        active=active if active is not None else True,
    )


def execute_sla_policy_update(*, policy_id: str, **fields: Any) -> dict:
    request = build_mcp_request()
    user, _ = _actor(request)
    _require_manage(user)
    updated = PostgresSlaPolicyRepository().update(
        policy_id,
        code=fields.get("code"),
        name=fields.get("name"),
        applies_to=fields.get("appliesTo"),
        duration_hours=fields.get("durationHours"),
        calendar_code=(
            fields["calendarCode"] if "calendarCode" in fields else ...
        ),
        active=fields.get("active"),
    )
    if updated is None:
        raise LookupError("Política de SLA não encontrada.")
    return updated


def delete_sla_policy_deactivate(*, policy_id: str) -> dict:
    request = build_mcp_request()
    user, _ = _actor(request)
    _require_manage(user)
    deactivated = PostgresSlaPolicyRepository().deactivate(policy_id)
    if deactivated is None:
        raise LookupError("Política de SLA não encontrada.")
    return deactivated


def sla_policy_delete_impact(*, policy_id: str) -> dict:
    items = PostgresSlaPolicyRepository().list_policies(include_inactive=True)
    match = next(
        (item for item in items if str(item.get("id") or "") == str(policy_id)),
        None,
    )
    if match is None:
        raise LookupError("Política de SLA não encontrada.")
    return {
        "policy_id": policy_id,
        "name": match.get("name"),
        "active": match.get("active"),
        "effect": "Desativação da política de SLA.",
    }


# --- read/execute: home favorites ------------------------------------------------


def tool_home_favorite_list() -> CallToolResult:
    try:
        _require_commercial_human()
        request = build_mcp_request()
        _, user_id = _actor(request)
        if not user_id:
            raise PermissionError("Unauthorized")
        items = PostgresHomeFavoritesRepository().get_items(user_id=user_id)
        return _ok({"items": items}, "Favoritos carregados.")
    except Exception as exc:
        return handle_tool_error(exc)


def execute_home_favorite_put(*, items: Any = None) -> dict:
    request = build_mcp_request()
    _, user_id = _actor(request)
    if not user_id:
        raise PermissionError("Unauthorized")
    raw = list(items or [])
    if len(raw) > MAX_HOME_FAVORITES:
        raise ValueError(
            f"Máximo de {MAX_HOME_FAVORITES} favoritos."
        )
    payload = [
        {k: v for k, v in item.items() if v is not None}
        for item in raw
        if isinstance(item, dict)
    ]
    normalize_favorite_items(payload)
    return {
        "items": PostgresHomeFavoritesRepository().put_items(
            user_id=user_id, items=payload
        )
    }


# --- read: team roster -------------------------------------------------------------


def tool_team_roster() -> CallToolResult:
    try:
        _require_commercial_human()
        request = build_mcp_request()
        user, _ = _actor(request)
        _require_manage(user)
        items = build_manage_team_roster_use_case().list_roster()
        serialized = [
            item.to_dict() if hasattr(item, "to_dict") else item
            for item in items
        ]
        return _ok({"items": serialized}, "Equipe carregada.")
    except Exception as exc:
        return handle_tool_error(exc)


# --- read/delete: attachments -------------------------------------------------------


def tool_attachment_list(
    *, owner_type: str, owner_id: str
) -> CallToolResult:
    try:
        _require_commercial_human()
        request = build_mcp_request()
        _, user_id = _actor(request)
        items = build_manage_attachments_use_case().list(
            owner_type=owner_type,
            owner_id=owner_id,
            actor_user_id=user_id,
            actor_is_portfolio_manager=_is_manager(request),
        )
        return _ok(
            {
                "items": [
                    {
                        **item.to_dict(),
                        "download_url": (
                            f"/attachments/{item.id}/content"
                        ),
                    }
                    for item in items
                ],
                "note": (
                    "download_url points to the canonical Portal "
                    "Comercial route — the binary stream is served "
                    "only there."
                ),
            },
            "Anexos carregados.",
        )
    except Exception as exc:
        return handle_tool_error(exc)


def delete_attachment(*, attachment_id: str) -> dict:
    request = build_mcp_request()
    _, user_id = _actor(request)
    if not user_id:
        raise PermissionError("Unauthorized")
    return build_manage_attachments_use_case().delete(
        attachment_id=_uuid(attachment_id, "attachment_id"),
        actor_user_id=user_id,
        actor_is_portfolio_manager=_is_manager(request),
    )


def attachment_delete_impact(*, attachment_id: str) -> dict:
    record = build_attachment_repository().get_by_id(
        _uuid(attachment_id, "attachment_id")
    )
    if record is None:
        raise LookupError("Anexo não encontrado.")
    return {
        "attachment_id": attachment_id,
        "file_name": getattr(record, "file_name", None),
        "owner_type": getattr(record, "owner_type", None),
        "effect": "Exclusão do anexo.",
    }


# --- read/execute/delete: interaction rooms -----------------------------------------


def tool_interaction_room_list(
    *,
    filter_key: str | None = None,
    query: str | None = None,
    limit: int = 50,
    cursor: str | None = None,
) -> CallToolResult:
    try:
        _require_commercial_human()
        request = build_mcp_request()
        _, actor = _actor(request)
        if not actor:
            raise PermissionError("Unauthorized")
        items = build_list_interaction_inbox_use_case().execute(
            actor_user_id=actor,
            filter_key=filter_key,
            query=query,
            limit=min(max(int(limit or 50), 1), 100),
        )
        return _ok(
            {
                "items": [
                    item.to_dict() if hasattr(item, "to_dict") else item
                    for item in items
                ]
            },
            "Salas carregadas.",
        )
    except Exception as exc:
        return handle_tool_error(exc)


def tool_interaction_room_get(*, room_id: str) -> CallToolResult:
    try:
        _require_commercial_human()
        request = build_mcp_request()
        _, actor = _actor(request)
        room = build_manage_interaction_rooms_use_case().get(
            room_id=_uuid(room_id, "room_id"),
            actor_user_id=actor,
        )
        return _ok(room.to_dict(), "Sala carregada.")
    except Exception as exc:
        return handle_tool_error(exc)


def tool_interaction_room_members(*, room_id: str) -> CallToolResult:
    try:
        _require_commercial_human()
        request = build_mcp_request()
        _, actor = _actor(request)
        members = build_manage_interaction_rooms_use_case().list_members(
            room_id=_uuid(room_id, "room_id"),
            actor_user_id=actor,
        )
        return _ok(
            {
                "items": [
                    m.to_dict() if hasattr(m, "to_dict") else m
                    for m in members
                ]
            },
            "Membros carregados.",
        )
    except Exception as exc:
        return handle_tool_error(exc)


def tool_interaction_room_messages(
    *,
    room_id: str,
    limit: int = 50,
    before_created_at: Any = None,
    before_id: Any = None,
    q: str | None = None,
) -> CallToolResult:
    try:
        _require_commercial_human()
        request = build_mcp_request()
        _, actor = _actor(request)
        messages = build_manage_interaction_messages_use_case().list_messages(
            room_id=_uuid(room_id, "room_id"),
            actor_user_id=actor,
            limit=min(max(int(limit or 50), 1), 200),
            before_created_at=before_created_at,
            before_id=before_id,
            query=q,
        )
        return _ok(
            {"items": [item.to_dict() for item in messages]},
            "Mensagens carregadas.",
        )
    except Exception as exc:
        return handle_tool_error(exc)


def tool_interaction_room_shared_items(
    *, room_id: str, kind: str | None = None
) -> CallToolResult:
    try:
        _require_commercial_human()
        request = build_mcp_request()
        _, actor = _actor(request)
        items = build_list_interaction_room_shared_items_use_case().execute(
            room_id=_uuid(room_id, "room_id"),
            actor_user_id=actor,
            kind=kind if isinstance(kind, str) else "all",
        )
        return _ok({"items": items}, "Itens compartilhados carregados.")
    except Exception as exc:
        return handle_tool_error(exc)


def tool_interaction_room_pins(*, room_id: str) -> CallToolResult:
    try:
        _require_commercial_human()
        request = build_mcp_request()
        _, actor = _actor(request)
        pins = build_manage_interaction_messages_use_case().list_pins(
            room_id=_uuid(room_id, "room_id"),
            actor_user_id=actor,
        )
        return _ok(
            {
                "items": [
                    item.to_dict() if hasattr(item, "to_dict") else item
                    for item in pins
                ]
            },
            "Fixadas carregadas.",
        )
    except Exception as exc:
        return handle_tool_error(exc)


def tool_interaction_mention_suggest(
    *,
    q: str | None = None,
    kinds: str | None = None,
    limit: int = 20,
) -> CallToolResult:
    try:
        _require_commercial_human()
        request = build_mcp_request()
        user, actor = _actor(request)
        kind_list = [
            item.strip()
            for item in (kinds or "user").split(",")
            if item.strip()
        ]
        items = build_suggest_interaction_mentions_use_case().suggest(
            query=q if isinstance(q, str) else "",
            kinds=kind_list,
            limit=min(max(int(limit or 20), 1), 20),
            actor_user_id=actor,
            unrestricted=(
                can_manage_portfolios(user) or can_use_team_scope(user)
            ),
        )
        return _ok({"items": items}, "Sugestões carregadas.")
    except Exception as exc:
        return handle_tool_error(exc)


def tool_interaction_entity_preview(
    *, kind: str, ref: Any
) -> CallToolResult:
    import json as _json

    try:
        _require_commercial_human()
        request = build_mcp_request()
        _, actor = _actor(request)
        if isinstance(ref, dict):
            parsed = ref
        else:
            try:
                parsed = _json.loads(str(ref or "{}"))
            except Exception as exc:
                raise ValueError("ref deve ser um objeto JSON.") from exc
        if not isinstance(parsed, dict):
            raise ValueError("ref deve ser um objeto JSON.")
        card = build_preview_interaction_entity_use_case().preview(
            kind=kind,
            ref=parsed,
            actor_user_id=actor,
        )
        return _ok(
            card.to_dict() if hasattr(card, "to_dict") else card,
            "Pré-visualização carregada.",
        )
    except Exception as exc:
        return handle_tool_error(exc)


def execute_room_resolve(
    *,
    kind: str,
    entity_type: str | None = None,
    entity_key: str | None = None,
    group_id: Any = None,
    title: str | None = None,
) -> dict:
    request = build_mcp_request()
    _, actor = _actor(request)
    if not actor:
        raise PermissionError("Unauthorized")
    room = build_manage_interaction_rooms_use_case().resolve(
        ResolveInteractionRoomInput(
            kind=kind,
            actor_user_id=actor,
            entity_type=entity_type,
            entity_key=entity_key,
            group_id=_uuid(group_id, "group_id") if group_id else None,
            title=title,
        )
    )
    return room.to_dict()


def execute_room_rename(*, room_id: str, title: str) -> dict:
    request = build_mcp_request()
    _, actor = _actor(request)
    if not actor:
        raise PermissionError("Unauthorized")
    room = build_manage_interaction_rooms_use_case().rename(
        room_id=_uuid(room_id, "room_id"),
        actor_user_id=actor,
        title=title,
    )
    return room.to_dict()


def execute_room_member_add(*, room_id: str, user_id: str) -> dict:
    request = build_mcp_request()
    _, actor = _actor(request)
    if not actor:
        raise PermissionError("Unauthorized")
    member = build_manage_interaction_rooms_use_case().add_member(
        room_id=_uuid(room_id, "room_id"),
        actor_user_id=actor,
        user_id=user_id,
    )
    return member.to_dict() if hasattr(member, "to_dict") else member


def execute_room_member_remove(*, room_id: str, user_id: str) -> dict:
    request = build_mcp_request()
    _, actor = _actor(request)
    if not actor:
        raise PermissionError("Unauthorized")
    build_manage_interaction_rooms_use_case().remove_member(
        room_id=_uuid(room_id, "room_id"),
        actor_user_id=actor,
        user_id=user_id,
    )
    return {"room_id": room_id, "user_id": user_id, "removed": True}


def execute_room_mark_read(*, room_id: str) -> dict:
    request = build_mcp_request()
    _, actor = _actor(request)
    if not actor:
        raise PermissionError("Unauthorized")
    member = build_manage_interaction_rooms_use_case().mark_read(
        room_id=_uuid(room_id, "room_id"),
        actor_user_id=actor,
    )
    return member.to_dict() if hasattr(member, "to_dict") else member


def delete_room(*, room_id: str) -> dict:
    request = build_mcp_request()
    user, actor = _actor(request)
    _require_manage(user)
    room = build_manage_interaction_rooms_use_case().soft_delete(
        room_id=_uuid(room_id, "room_id"),
        actor_user_id=actor,
    )
    return room.to_dict()


def room_delete_impact(*, room_id: str) -> dict:
    request = build_mcp_request()
    _, actor = _actor(request)
    room = build_manage_interaction_rooms_use_case().get(
        room_id=_uuid(room_id, "room_id"),
        actor_user_id=actor,
    )
    return {
        "room_id": room_id,
        "title": getattr(room, "title", None),
        "kind": getattr(room, "kind", None),
        "effect": "Exclusão (soft) da sala de interação.",
    }


# --- execute/delete: interaction messages -----------------------------------------


def _room_notify(request: Request, *, reason: str, message: Any) -> None:
    try:
        actor = actor_sub_from_request(request)
        notify_interaction_room_activity(
            reason=reason,
            room_id=str(message.room_id),
            message=message,
            actor_user_id=actor,
            actor_display_name=actor_display_name_from_request(request),
            actor_client_id=client_id_from_request(request),
        )
        notify_interaction_mention(
            message=message,
            actor_user_id=actor,
            actor_display_name=actor_display_name_from_request(request),
            actor_client_id=client_id_from_request(request),
        )
    except Exception:
        logger.exception("caio_mcp_message_notify_failed")


def execute_message_post(
    *,
    room_id: str,
    body_text: str,
    message_kind: str = "text",
    parent_id: Any = None,
    mentions: Any = None,
) -> dict:
    request = build_mcp_request()
    _, actor = _actor(request)
    if not actor:
        raise PermissionError("Unauthorized")
    message = build_manage_interaction_messages_use_case().post(
        PostInteractionMessageInput(
            room_id=_uuid(room_id, "room_id"),
            actor_user_id=actor,
            body_text=body_text,
            message_kind=message_kind,
            parent_id=_uuid(parent_id, "parent_id") if parent_id else None,
            mentions=_mentions_from_body(
                mentions if isinstance(mentions, list) else None
            ),
        )
    )
    _room_notify(request, reason="created", message=message)
    return message.to_dict()


def execute_message_update(
    *,
    room_id: str,
    message_id: str,
    body_text: str | None = None,
    mentions: Any = None,
) -> dict:
    request = build_mcp_request()
    _, actor = _actor(request)
    if not actor:
        raise PermissionError("Unauthorized")
    message = build_manage_interaction_messages_use_case().update(
        room_id=_uuid(room_id, "room_id"),
        message_id=_uuid(message_id, "message_id"),
        actor_user_id=actor,
        body_text=body_text,
        mentions=_mentions_from_body(
            mentions if isinstance(mentions, list) else None
        ),
        replace_mentions=mentions is not None,
    )
    _room_notify(request, reason="updated", message=message)
    return message.to_dict()


def execute_message_reaction(
    *,
    room_id: str,
    message_id: str,
    code: str,
    clear: bool = False,
) -> dict:
    request = build_mcp_request()
    _, actor = _actor(request)
    if not actor:
        raise PermissionError("Unauthorized")
    uc = build_manage_interaction_messages_use_case()
    rid = _uuid(room_id, "room_id")
    mid = _uuid(message_id, "message_id")
    if clear:
        reaction = uc.clear_reaction(
            room_id=rid, message_id=mid, actor_user_id=actor, code=code
        )
    else:
        reaction = uc.set_reaction(
            room_id=rid, message_id=mid, actor_user_id=actor, code=code
        )
    return reaction.to_dict() if hasattr(reaction, "to_dict") else {
        "room_id": room_id,
        "message_id": message_id,
        "code": code,
        "cleared": clear,
    }


def execute_message_pin(
    *, room_id: str, message_id: str, unpin: bool = False
) -> dict:
    request = build_mcp_request()
    _, actor = _actor(request)
    if not actor:
        raise PermissionError("Unauthorized")
    uc = build_manage_interaction_messages_use_case()
    rid = _uuid(room_id, "room_id")
    mid = _uuid(message_id, "message_id")
    if unpin:
        result = uc.unpin(room_id=rid, message_id=mid, actor_user_id=actor)
    else:
        result = uc.pin(room_id=rid, message_id=mid, actor_user_id=actor)
    return result.to_dict() if hasattr(result, "to_dict") else {
        "room_id": room_id,
        "message_id": message_id,
        "unpinned": unpin,
    }


def delete_message(*, room_id: str, message_id: str) -> dict:
    request = build_mcp_request()
    _, actor = _actor(request)
    if not actor:
        raise PermissionError("Unauthorized")
    message = build_manage_interaction_messages_use_case().delete(
        room_id=_uuid(room_id, "room_id"),
        message_id=_uuid(message_id, "message_id"),
        actor_user_id=actor,
    )
    try:
        notify_interaction_room_activity(
            reason="deleted",
            room_id=str(message.room_id),
            message=message,
            actor_user_id=actor,
            actor_display_name=actor_display_name_from_request(request),
            actor_client_id=client_id_from_request(request),
        )
    except Exception:
        logger.exception("caio_mcp_message_delete_notify_failed")
    return message.to_dict()


def message_delete_impact(*, room_id: str, message_id: str) -> dict:
    return {
        "room_id": room_id,
        "message_id": message_id,
        "effect": "Exclusão (soft) da mensagem da sala.",
    }


# --- read/execute/delete: contacts ---------------------------------------------------


def execute_contact_create(
    *,
    customer_code: str,
    customer_store: str,
    full_name: str,
    role_title: str | None = None,
    channel: str | None = None,
    email: str | None = None,
    phone_e164: str | None = None,
    is_whatsapp: bool | None = None,
    is_primary: bool | None = None,
    source: str | None = None,
) -> dict:
    request = build_mcp_request()
    _, actor = _actor(request)
    contact = build_manage_account_contacts_use_case().create(
        customer_code=customer_code,
        customer_store=customer_store,
        actor_user_id=actor or "",
        data=CreateAccountContactInput(
            full_name=full_name,
            role_title=role_title,
            channel=channel,
            email=email,
            phone_e164=phone_e164,
            is_whatsapp=is_whatsapp,
            is_primary=is_primary,
            source=source,
        ),
        scope_check=_account_detail_scope_check(request),
    )
    return contact.to_dict()


def execute_contact_update(
    *,
    contact_id: str,
    customer_code: str,
    customer_store: str,
    **changes: Any,
) -> dict:
    request = build_mcp_request()
    _, actor = _actor(request)
    allowed = {
        "full_name", "role_title", "channel", "email", "phone_e164",
        "is_whatsapp", "is_primary",
    }
    contact = build_manage_account_contacts_use_case().update(
        customer_code=customer_code,
        customer_store=customer_store,
        contact_id=_uuid(contact_id, "contact_id"),
        changes={
            key: value
            for key, value in changes.items()
            if key in allowed and value is not None
        },
        scope_check=_account_detail_scope_check(request),
        actor_user_id=actor or "",
    )
    return contact.to_dict()


def delete_contact(
    *, contact_id: str, customer_code: str, customer_store: str
) -> dict:
    request = build_mcp_request()
    _, actor = _actor(request)
    contact = build_manage_account_contacts_use_case().soft_delete(
        customer_code=customer_code,
        customer_store=customer_store,
        contact_id=_uuid(contact_id, "contact_id"),
        scope_check=_account_detail_scope_check(request),
        actor_user_id=actor or "",
    )
    return contact.to_dict()


# --- read: production BFF --------------------------------------------------------------


def tool_production_order(
    *, production_order: str, branch: str | None = None
) -> CallToolResult:
    try:
        _require_commercial_human()
        encoded = quote(production_order.strip(), safe="")
        payload = build_delpi_commercial_gateway().get_production(
            f"/orders/by-op/{encoded}",
            params={"branch": branch},
        )
        return _ok(unwrap_gateway_data(payload), "OP carregada.")
    except Exception as exc:
        return handle_tool_error(exc)


def tool_production_appointments(
    *,
    op: str,
    branch: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> CallToolResult:
    try:
        _require_commercial_human()
        payload = build_delpi_commercial_gateway().get_production(
            "/appointments/by-op",
            params={
                "op": op,
                "branch": branch,
                "page": max(int(page or 1), 1),
                "page_size": min(max(int(page_size or 50), 1), 100),
            },
        )
        return _ok(unwrap_gateway_data(payload), "Apontamentos carregados.")
    except Exception as exc:
        return handle_tool_error(exc)


def tool_product_factory_status(
    *, product_code: str, branch: str | None = None
) -> CallToolResult:
    try:
        _require_commercial_human()
        encoded = quote(product_code.strip(), safe="")
        payload = build_delpi_commercial_gateway().get_product(
            f"/{encoded}/factory-status",
            params={"branch": branch},
        )
        return _ok(
            unwrap_gateway_data(payload),
            "Status de fábrica carregado.",
        )
    except Exception as exc:
        return handle_tool_error(exc)


def tool_product_structure(
    *, product_code: str, branch: str | None = None
) -> CallToolResult:
    try:
        _require_commercial_human()
        encoded = quote(product_code.strip(), safe="")
        payload = build_delpi_commercial_gateway().get_product(
            f"/{encoded}/structure",
            params={"branch": branch},
        )
        return _ok(
            unwrap_gateway_data(payload),
            "Estrutura do produto carregada.",
        )
    except Exception as exc:
        return handle_tool_error(exc)


# --- read: product catalog (engineering-owned SB1 via products BFF) ------------


def tool_product_search(
    *,
    code: str | None = None,
    description: str | None = None,
    group_code: str | None = None,
    subgroup: str | None = None,
    product_type: str | None = None,
    customer_reference: str | None = None,
    view: str | None = None,
    sort: str | None = None,
    direction: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> CallToolResult:
    try:
        _require_commercial_human()
        payload = build_delpi_commercial_gateway().get_product(
            "/search",
            params={
                "code": code,
                "description": description,
                "group_code": group_code,
                "subgroup": subgroup,
                "product_type": product_type,
                "customer_reference": customer_reference,
                "view": view,
                "sort": sort,
                "direction": direction,
                "page": max(int(page or 1), 1),
                "page_size": min(max(int(page_size or 50), 1), 100),
            },
        )
        return _ok(
            unwrap_gateway_data(payload), "Produtos carregados."
        )
    except Exception as exc:
        return handle_tool_error(exc)


def tool_product_summary(*, product_code: str) -> CallToolResult:
    try:
        _require_commercial_human()
        encoded = quote(product_code.strip(), safe="")
        payload = build_delpi_commercial_gateway().get_product(
            f"/{encoded}/summary"
        )
        return _ok(
            unwrap_gateway_data(payload),
            "Resumo cadastral do produto carregado.",
        )
    except Exception as exc:
        return handle_tool_error(exc)


def tool_product_customers(
    *, product_code: str, page: int = 1, page_size: int = 50
) -> CallToolResult:
    try:
        _require_commercial_human()
        encoded = quote(product_code.strip(), safe="")
        payload = build_delpi_commercial_gateway().get_product(
            f"/{encoded}/customers",
            params={
                "page": max(int(page or 1), 1),
                "page_size": min(max(int(page_size or 50), 1), 100),
            },
        )
        return _ok(
            unwrap_gateway_data(payload),
            "Clientes do produto carregados.",
        )
    except Exception as exc:
        return handle_tool_error(exc)


def tool_product_filter_options() -> CallToolResult:
    try:
        _require_commercial_human()
        payload = build_delpi_commercial_gateway().get_product(
            "/filter-options"
        )
        return _ok(
            unwrap_gateway_data(payload),
            "Opções de filtro de produtos carregadas.",
        )
    except Exception as exc:
        return handle_tool_error(exc)


# --- read/execute: user profile ------------------------------------------------------------


def tool_user_profile_get(*, user_id: str) -> CallToolResult:
    try:
        _require_commercial_human()
        data = build_manage_user_profile_use_case().get_profile(user_id=user_id)
        return _ok(data, "Perfil carregado.")
    except Exception as exc:
        return handle_tool_error(exc)


def execute_user_profile_update(
    *,
    user_id: str | None = None,
    job_title: str | None = None,
    phone_e164: str | None = None,
    mobile_e164: str | None = None,
    whatsapp_e164: str | None = None,
) -> dict:
    request = build_mcp_request()
    _, actor = _actor(request)
    if not actor:
        raise PermissionError("Unauthorized")
    target = (user_id or "").strip() or actor
    if target != actor and not _is_manager(request):
        raise PermissionError("Forbidden")
    return build_manage_user_profile_use_case().update_profile(
        actor_user_id=actor,
        user_id=target,
        job_title=job_title,
        phone_e164=phone_e164,
        mobile_e164=mobile_e164,
        whatsapp_e164=whatsapp_e164,
        authorization=request.headers.get("Authorization"),
    )


def delete_user_profile_photo(*, user_id: str) -> dict:
    request = build_mcp_request()
    _, actor = _actor(request)
    if not actor:
        raise PermissionError("Unauthorized")
    return build_manage_user_profile_use_case().delete_photo(
        actor_user_id=actor,
        user_id=(user_id or "").strip() or actor,
        authorization=request.headers.get("Authorization"),
    )


def user_profile_photo_delete_impact(*, user_id: str) -> dict:
    return {
        "user_id": user_id,
        "effect": "Exclusão da foto de perfil do usuário.",
    }


# --- analyze: proxies over the official analytics owner ------------------------------


def analyze_proxy(
    *,
    path: str,
    analysis_label: str,
    seller_id: str | None = None,
    portfolio_id: str | None = None,
    scope_mode: str | None = None,
    account_customer_code: str | None = None,
    customer_codes: str | None = None,
    question: str | None = None,
    **params: Any,
) -> CallToolResult:
    """One adapter for the GET-analytics family — same scope merge and
    gateway call as ``analytics_routes._proxy``."""
    try:
        _require_commercial_human()
        request = build_mcp_request()
        scope = _analytics_scope(
            request,
            seller_id=seller_id,
            portfolio_id=portfolio_id,
            scope_mode=scope_mode,
        )
        totvs = merge_totvs_params(
            scope,
            params,
            account_customer_code=account_customer_code,
            selected_customer_codes=customer_codes,
        )
        payload = build_delpi_commercial_gateway().get_commercial_analytics(
            path, params=totvs
        )
        return _ok(
            {
                "analysis_type": analysis_label,
                "question": question,
                "data_class": "OBSERVED",
                "scope_mode": scope_mode or "global",
                "data": unwrap_gateway_data(payload),
                "provenance": (
                    "TOTVS via api-delpi commercial analytics → "
                    "commercial-api scope"
                ),
            },
            "Análise carregada.",
        )
    except Exception as exc:
        return handle_tool_error(exc)


def analyze_billing_share(
    *,
    seller_id: str | None = None,
    portfolio_id: str | None = None,
    scope_mode: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    branch: str | None = None,
    customer_segment: str | None = None,
    customer_codes: str | None = None,
    customer_centers: str | None = None,
    nature: str | None = None,
    question: str | None = None,
) -> CallToolResult:
    try:
        _require_commercial_human()
        request = build_mcp_request()
        user = current_user_from_request(request)
        if not can_view_portfolio_billing_share(user):
            raise PermissionError("Forbidden")
        scope = _analytics_scope(
            request,
            seller_id=seller_id,
            portfolio_id=portfolio_id,
            scope_mode=scope_mode,
        )
        data = GetPortfolioBillingShareUseCase().execute(
            build_delpi_commercial_gateway(),
            scope,
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            customer_segment=customer_segment,
            nature=nature,
            selected_customer_codes=customer_codes,
            customer_centers=customer_centers,
        )
        return _ok(
            {
                "analysis_type": "portfolio.billing_share",
                "question": question,
                "data_class": "OBSERVED",
                "scope_mode": scope_mode or "global",
                "data": data,
                "provenance": "GetPortfolioBillingShareUseCase (owner).",
            },
            "Share de faturamento carregado.",
        )
    except Exception as exc:
        return handle_tool_error(exc)


def analyze_billing_ranking(
    *,
    seller_id: str | None = None,
    portfolio_id: str | None = None,
    scope_mode: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    branch: str | None = None,
    customer_segment: str | None = None,
    customer_codes: str | None = None,
    customer_centers: str | None = None,
    nature: str | None = None,
    group_by: str = "customer",
    limit: int = 50,
    order: str = "growth",
    question: str | None = None,
) -> CallToolResult:
    try:
        _require_commercial_human()
        request = build_mcp_request()
        if not start_date or not end_date:
            raise ValueError("start_date e end_date são obrigatórios.")
        scope = _analytics_scope(
            request,
            seller_id=seller_id,
            portfolio_id=portfolio_id,
            scope_mode=scope_mode,
        )
        data = GetPortfolioBillingRankingUseCase().execute(
            build_delpi_commercial_gateway(),
            scope,
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            customer_segment=customer_segment,
            limit=min(max(int(limit or 50), 1), 500),
            group_by="seller" if group_by == "seller" else "customer",
            order="decline" if order == "decline" else "growth",
            nature=nature,
            selected_customer_codes=customer_codes,
            customer_centers=customer_centers,
        )
        return _ok(
            {
                "analysis_type": "portfolio.billing_ranking",
                "question": question,
                "data_class": "OBSERVED",
                "scope_mode": scope_mode or "global",
                "data": data,
                "provenance": "GetPortfolioBillingRankingUseCase (owner).",
            },
            "Ranking de faturamento carregado.",
        )
    except Exception as exc:
        return handle_tool_error(exc)


def analyze_department(
    *,
    analysis_label: str,
    department_id: str = "commercial",
    competence: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    branch: str | None = None,
    question: str | None = None,
    idd: bool = True,
) -> CallToolResult:
    try:
        _require_commercial_human()
        params: dict[str, Any] = {"department_id": department_id}
        if competence:
            params["competence"] = competence
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if branch:
            params["branch"] = branch
        gateway = build_delpi_commercial_gateway()
        payload = (
            gateway.get_dashboard_department_idd(params=params)
            if idd
            else gateway.get_dashboard_department_indicators(params=params)
        )
        return _ok(
            {
                "analysis_type": analysis_label,
                "question": question,
                "data_class": "OBSERVED",
                "data": unwrap_gateway_data(payload),
                "provenance": "Dashboard department indicators (owner).",
            },
            "Indicadores carregados.",
        )
    except Exception as exc:
        return handle_tool_error(exc)


def analyze_otd_line_detail(
    *,
    seller_id: str | None = None,
    portfolio_id: str | None = None,
    scope_mode: str | None = None,
    branch: str,
    order_number: str,
    line_item: str,
    customer_centers: str | None = None,
    question: str | None = None,
) -> CallToolResult:
    try:
        _require_commercial_human()
        request = build_mcp_request()
        scope = _analytics_scope(
            request,
            seller_id=seller_id,
            portfolio_id=portfolio_id,
            scope_mode=scope_mode,
        )
        params: dict[str, Any] = {}
        if customer_centers:
            params["customer_centers"] = customer_centers
        totvs = merge_totvs_params(scope, params)
        b = quote(branch.strip(), safe="")
        o = quote(order_number.strip(), safe="")
        line = quote(line_item.strip(), safe="")
        payload = build_delpi_commercial_gateway().get_commercial_analytics(
            f"/sales-order-otd/lines/{b}/{o}/{line}", params=totvs
        )
        return _ok(
            {
                "analysis_type": "sales_order_otd.line_detail",
                "question": question,
                "data_class": "OBSERVED",
                "scope_mode": scope_mode or "global",
                "data": unwrap_gateway_data(payload),
                "provenance": (
                    "TOTVS via api-delpi OTD → commercial-api scope"
                ),
            },
            "Detalhe OTD carregado.",
        )
    except Exception as exc:
        return handle_tool_error(exc)


# Analytics proxy map — analysis_type → (path, allowed upstream
# params, required upstream params). Mirrors analytics_routes: scope
# merged server-side, never widened. ``required`` mirrors the owner
# contract (api-delpi required query params / DTO validation) so a
# missing input fails locally with 400 — never an upstream 502.
ANALYZE_PROXY_MAP: dict[
    str, tuple[str, tuple[str, ...], tuple[str, ...]]
] = {
    "rol.series": (
        "/rol/series",
        (
            "start_date", "end_date", "branch", "customer_segment",
            "granularity", "customer_centers",
        ),
        ("granularity",),
    ),
    "rol.by_product": (
        "/rol/by-product",
        (
            "start_date", "end_date", "branch", "customer_segment",
            "product_codes", "product_groups", "market", "group_by",
            "limit", "customer_centers",
        ),
        ("start_date", "end_date"),
    ),
    "rol.by_customer": (
        "/rol/by-customer",
        (
            "start_date", "end_date", "branch", "customer_segment",
            "product_codes", "product_groups", "market", "limit",
            "include_others", "customer_centers",
        ),
        ("start_date", "end_date"),
    ),
    "billing.by_customer_month": (
        "/billing/by-customer-month",
        (
            "start_date", "end_date", "branch", "customer_segment",
            "nature", "limit", "customer_centers",
        ),
        (),
    ),
    "closing_rate.summary": (
        "/closing-rate",
        (
            "start_date", "end_date", "branch", "customer_segment",
        ),
        (),
    ),
    "closing_rate.series": (
        "/closing-rate/series",
        (
            "start_date", "end_date", "branch", "customer_segment",
            "granularity",
        ),
        ("granularity",),
    ),
    "sales_order_otd.summary": (
        "/sales-order-otd",
        (
            "start_date", "end_date", "branch", "customer_segment",
            "customer_centers",
        ),
        (),
    ),
    "sales_order_otd.panel": (
        "/sales-order-otd/panel",
        (
            "start_date", "end_date", "branch", "customer_segment",
            "customer_centers",
        ),
        (),
    ),
    "sales_order_otd.series": (
        "/sales-order-otd/series",
        (
            "start_date", "end_date", "branch", "customer_segment",
            "granularity", "customer_centers",
        ),
        ("granularity",),
    ),
    "new_business.rol_pct": (
        "/new-business-rol-pct",
        (
            "start_date", "end_date", "branch", "customer_segment",
        ),
        (),
    ),
    "new_business.rol_target_pct": (
        "/new-business-rol-target-pct",
        (
            "start_date", "end_date", "branch", "customer_segment",
        ),
        (),
    ),
    "weg.rol_target_pct": (
        "/weg-rol-target-pct",
        (
            "start_date", "end_date", "branch", "customer_segment",
        ),
        (),
    ),
    "opportunity.collaborator_summary": (
        "/proposals/collaborator-summary",
        (
            "start_date", "end_date", "branch", "customer_segment",
        ),
        (),
    ),
}

"""Helpers BFF TOTVS — escopo commercial → customer_codes para api-delpi."""

from __future__ import annotations

from starlette.requests import Request

from commercial_app.application.security.commercial_permissions import (
    can_manage_portfolios,
    can_use_team_scope,
)
from commercial_app.application.services.analytics_customer_codes_service import (
    AnalyticsCustomerCodesService,
)
from commercial_app.application.services.resolve_commercial_customer_scope_service import (
    CommercialCustomerScope,
)
from commercial_app.core.auth_actor import (
    actor_sub_from_request,
    current_user_from_request,
)


def parse_portfolio_id_csv(*values: str | None) -> list[str]:
    """Parse one or more CSV strings of portfolio UUIDs (seller_id / portfolio_id)."""
    seen: set[str] = set()
    out: list[str] = []
    for raw in values:
        if not raw:
            continue
        for part in str(raw).split(","):
            pid = part.strip()
            if not pid or pid in seen:
                continue
            seen.add(pid)
            out.append(pid)
    return out


def resolve_portfolio_scope(
    request: Request,
    *,
    seller_id: str | None = None,
    portfolio_id: str | None = None,
) -> CommercialCustomerScope:
    # Lazy: evita import de gateway/delpi_auth em testes unitários de merge.
    from commercial_app.composition.commercial_composer import (
        build_resolve_commercial_customer_scope_service,
    )

    user = current_user_from_request(request)
    unrestricted = can_manage_portfolios(user) or can_use_team_scope(user)
    user_id = actor_sub_from_request(request) or ""
    portfolio_ids = parse_portfolio_id_csv(portfolio_id, seller_id)
    return build_resolve_commercial_customer_scope_service().execute(
        user_id=user_id,
        unrestricted=unrestricted,
        portfolio_ids=portfolio_ids or None,
    )


def resolve_analytics_portfolio_scope(
    request: Request,
    *,
    seller_id: str | None = None,
    portfolio_id: str | None = None,
) -> CommercialCustomerScope:
    """
    Analytics / Visão geral:
    - sem seller_id/portfolio_id → «Não filtrar» (TOTVS global, sem membership);
    - com ids → escopo das carteiras selecionadas (union / membership).
    """
    portfolio_ids = parse_portfolio_id_csv(portfolio_id, seller_id)
    if not portfolio_ids:
        return CommercialCustomerScope(
            unrestricted=True,
            allowed_customers=None,
        )
    return resolve_portfolio_scope(
        request,
        seller_id=seller_id,
        portfolio_id=portfolio_id,
    )


def selected_customer_codes_from_request(request: Request) -> str | None:
    raw = (request.query_params.get("customer_codes") or "").strip()
    return raw or None


def merge_totvs_params(
    scope: CommercialCustomerScope,
    base: dict[str, object | None],
    *,
    account_customer_code: str | None = None,
    selected_customer_codes: str | None = None,
) -> dict[str, object]:
    """Insere customer_codes a partir do escopo; remove seller_id/portfolio_id.

    Conta 360: com ``account_customer_code`` explícito, restringe só a esse código
    (não à membership da carteira) — mesma semântica do enrichment 1 par.

    ``selected_customer_codes`` (CSV do MFE): interseção com membership; em
    recorte irrestrito, aplica os códigos selecionados. Nunca amplia o escopo.
    ``customer_codes`` no ``base`` é descartado (não confiar no browser).
    """
    params: dict[str, object] = {
        key: value
        for key, value in base.items()
        if value is not None
        and value != ""
        and key
        not in {
            "seller_id",
            "portfolio_id",
            "account_customer_code",
            "customer_codes",
        }
    }
    account_code = (account_customer_code or "").strip()
    if account_code:
        params["customer_codes"] = account_code
        return params
    codes = AnalyticsCustomerCodesService.codes_param_for_selection(
        scope, selected_customer_codes
    )
    if codes is not None:
        params["customer_codes"] = codes
    return params


def unwrap_gateway_data(payload: object) -> object:
    if isinstance(payload, dict) and "data" in payload:
        return payload.get("data")
    return payload

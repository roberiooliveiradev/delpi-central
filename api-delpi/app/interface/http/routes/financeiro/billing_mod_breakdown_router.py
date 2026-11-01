"""R09 billing × MOD breakdown (doc 141 — DR-1/DR-2 APPROVED).

Guard: S2S-only — the shared ``stock-inventory.read`` scope on the
technical client ``controllership-finance-api`` plus the delegated human
Bearer (ADR-010). Branch is a data filter, not an access boundary (PO
decision, doc 49 §8). The read is an operational view:
``official_parity`` stays ``pending`` until the Controladoria sign-off
(DR-3) — cost fields return typed absence, never inferred values.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter

from app.application.dto.financeiro_billing_mod_breakdown.billing_mod_breakdown_request import (
    BillingModBreakdownRequest,
)
from app.application.security.stock_inventory_scope import (
    StockInventoryScopeUnavailableError,
)
from app.composition.financeiro_billing_mod_breakdown_composer import (
    build_billing_mod_breakdown_use_case,
)
from app.core.responses import error_response
from app.interface.http.openapi_agent_metadata_builder import (
    OpenApiAgentMetadataBuilder,
)
from app.interface.http.route_response_helpers import api_delpi_success
from app.interface.http.routes.financeiro.stock_inventory_route_helpers import (
    BRANCH_QUERY,
    PERIOD_QUERY,
    delegated_user_subject,
)
from app.interface.http.s2s_service_access import require_s2s_service
from app.utils.logger import log_error

router = APIRouter(
    prefix="/financeiro",
    tags=["Financeiro — Billing MOD Breakdown"],
)

# Same dataset scope as the stock-inventory/billing family (doc 49 §8).
BILLING_MOD_S2S_REQUIRED_SCOPES = ("stock-inventory.read",)
BILLING_MOD_S2S_ALLOWED_CLIENTS = ("controllership-finance-api",)


def _billing_mod_s2s_guard(fn):
    return require_s2s_service(
        required_scopes=BILLING_MOD_S2S_REQUIRED_SCOPES,
        allowed_clients=BILLING_MOD_S2S_ALLOWED_CLIENTS,
    )(fn)


@router.get(
    "/billing-mod-breakdown",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_financeiro_billing_mod_breakdown",
        path="/financeiro/billing-mod-breakdown",
    ),
)
@_billing_mod_s2s_guard
def get_financeiro_billing_mod_breakdown_route(
    period: str = PERIOD_QUERY(),
    branch: Optional[str] = BRANCH_QUERY(),
):
    try:
        request = BillingModBreakdownRequest.from_query(
            period=period, branch=branch
        )
    except ValueError as exc:
        log_error(f"Erro de validação em billing-mod-breakdown: {exc}")
        return error_response(str(exc), status_code=400)

    try:
        data = build_billing_mod_breakdown_use_case().execute(
            request, user_subject=delegated_user_subject()
        )
    except StockInventoryScopeUnavailableError as exc:
        log_error(f"Escopo financeiro não resolvido no R09: {exc}")
        return error_response(
            "Escopo de dados financeiros não autorizado.",
            status_code=403,
            code="scope_unavailable",
            recoverable=False,
        )
    except Exception as exc:
        log_error(f"Erro ao carregar R09 billing-mod-breakdown: {exc}")
        return error_response(
            "Erro interno ao carregar faturamento × MOD.",
            status_code=500,
        )

    return api_delpi_success(
        data=data,
        message="Billing × MOD breakdown loaded successfully.",
        operation_id="get_financeiro_billing_mod_breakdown",
    )

"""R12/R15 closing-state markers read (SB9010/SX6/TTAT, doc 129).

Guard: S2S-only — ``stock-inventory.read`` scope on the dedicated client
``controllership-finance-api`` plus the delegated human Bearer (ADR-010).
Read-only markers; the governed state projection lives in the BFF.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter

from app.application.dto.financeiro_closing_state.closing_state_request import (
    ClosingStateRequest,
)
from app.application.security.stock_inventory_scope import (
    StockInventoryScopeUnavailableError,
)
from app.composition.financeiro_closing_state_composer import (
    build_closing_state_use_case,
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
    prefix="/financeiro/closing-state",
    tags=["Financeiro — Closing State"],
)

CLOSING_STATE_S2S_REQUIRED_SCOPES = ("stock-inventory.read",)
CLOSING_STATE_S2S_ALLOWED_CLIENTS = ("controllership-finance-api",)


def _closing_state_s2s_guard(fn):
    return require_s2s_service(
        required_scopes=CLOSING_STATE_S2S_REQUIRED_SCOPES,
        allowed_clients=CLOSING_STATE_S2S_ALLOWED_CLIENTS,
    )(fn)


@router.get(
    "",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_financeiro_closing_state",
        path="/financeiro/closing-state",
    ),
)
@_closing_state_s2s_guard
def get_financeiro_closing_state_route(
    period: str = PERIOD_QUERY(),
    branch: Optional[str] = BRANCH_QUERY(),
):
    try:
        request = ClosingStateRequest.from_query(
            period=period, branch=branch
        )
    except ValueError as exc:
        log_error(f"Erro de validação em closing state: {exc}")
        return error_response(str(exc), status_code=400)

    try:
        data = build_closing_state_use_case().execute(
            request, user_subject=delegated_user_subject()
        )
    except StockInventoryScopeUnavailableError as exc:
        log_error(f"Escopo financeiro não resolvido em closing state: {exc}")
        return error_response(
            "Escopo de dados financeiros não autorizado.",
            status_code=403,
            code="scope_unavailable",
            recoverable=False,
        )
    except Exception as exc:
        log_error(f"Erro ao carregar closing state: {exc}")
        return error_response(
            "Erro interno ao carregar o estado de fechamento.",
            status_code=500,
        )

    return api_delpi_success(
        data=data,
        message="Closing-state markers loaded successfully.",
        operation_id="get_financeiro_closing_state",
    )

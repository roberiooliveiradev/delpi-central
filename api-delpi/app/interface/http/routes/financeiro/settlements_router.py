from __future__ import annotations

from typing import Optional

from fastapi import APIRouter

from app.application.dto.financeiro_settlements.constantes import (
    DEFAULT_PAGE,
    DEFAULT_PAGE_SIZE,
    DEFAULT_SORT_BY,
    DEFAULT_SORT_DIR,
    SETTLEMENT_SIDE_PAYABLE,
    SETTLEMENT_SIDE_RECEIVABLE,
)
from app.composition.financeiro_settlements_composer import (
    build_get_settlements_summary_use_case,
    build_get_settlements_use_case,
)
from app.core.responses import error_response
from app.interface.http.openapi_agent_metadata_builder import (
    OpenApiAgentMetadataBuilder,
)
from app.interface.http.routes.financeiro.settlements_route_helpers import (
    MOVEMENT_TYPE_QUERY,
    NATURE_CODE_QUERY,
    PAGE_QUERY,
    PERIOD_END_QUERY,
    PERIOD_START_QUERY,
    SETTLEMENTS_PAGE_SIZE_QUERY,
    SETTLEMENTS_SORT_DIR_QUERY,
    SORT_BY_QUERY,
    build_settlements_request,
    delegated_user_subject,
    execute_settlements_route,
)
from app.interface.http.s2s_service_access import require_s2s_service
from app.utils.logger import log_error

router = APIRouter(
    prefix="/financeiro/settlements",
    tags=["Financeiro — Financial Settlements"],
)

# Individual S2S contract (ADR-010): only the Controladoria & Finanças BFF
# client-credentials principal may call these routes, and only with the
# settlements scope. A dedicated user Bearer is still mandatory — the shared
# internal token never authorizes this surface.
SETTLEMENTS_S2S_REQUIRED_SCOPES = ("settlements.read",)
SETTLEMENTS_S2S_ALLOWED_CLIENTS = ("controllership-finance-api",)


def _settlements_s2s_guard(fn):
    return require_s2s_service(
        required_scopes=SETTLEMENTS_S2S_REQUIRED_SCOPES,
        allowed_clients=SETTLEMENTS_S2S_ALLOWED_CLIENTS,
    )(fn)


@router.get(
    "/payables",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_financeiro_settlements_payables",
        path="/financeiro/settlements/payables",
    ),
)
@_settlements_s2s_guard
def get_financeiro_settlements_payables_route(
    start_date: Optional[str] = PERIOD_START_QUERY(),
    end_date: Optional[str] = PERIOD_END_QUERY(),
    nature_code: Optional[str] = NATURE_CODE_QUERY(),
    movement_type: Optional[str] = MOVEMENT_TYPE_QUERY(),
    sort_by: str = SORT_BY_QUERY(),
    sort_dir: str = SETTLEMENTS_SORT_DIR_QUERY(),
    page: int = PAGE_QUERY(),
    page_size: int = SETTLEMENTS_PAGE_SIZE_QUERY(),
):
    try:
        request = build_settlements_request(
            start_date=start_date,
            end_date=end_date,
            nature_code=nature_code,
            movement_type=movement_type,
            sort_by=sort_by,
            sort_dir=sort_dir,
            page=page,
            page_size=page_size,
        )
    except ValueError as exc:
        log_error(f"Erro de validação em settlements payables: {exc}")
        return error_response(str(exc), status_code=400)

    return execute_settlements_route(
        use_case_builder=build_get_settlements_use_case,
        request=request,
        side=SETTLEMENT_SIDE_PAYABLE,
        operation_id="get_financeiro_settlements_payables",
        success_message="Payable settlement events loaded successfully.",
        error_context="carregar baixas a pagar",
        user_subject=delegated_user_subject(),
    )


@router.get(
    "/receivables",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_financeiro_settlements_receivables",
        path="/financeiro/settlements/receivables",
    ),
)
@_settlements_s2s_guard
def get_financeiro_settlements_receivables_route(
    start_date: Optional[str] = PERIOD_START_QUERY(),
    end_date: Optional[str] = PERIOD_END_QUERY(),
    nature_code: Optional[str] = NATURE_CODE_QUERY(),
    movement_type: Optional[str] = MOVEMENT_TYPE_QUERY(),
    sort_by: str = SORT_BY_QUERY(),
    sort_dir: str = SETTLEMENTS_SORT_DIR_QUERY(),
    page: int = PAGE_QUERY(),
    page_size: int = SETTLEMENTS_PAGE_SIZE_QUERY(),
):
    try:
        request = build_settlements_request(
            start_date=start_date,
            end_date=end_date,
            nature_code=nature_code,
            movement_type=movement_type,
            sort_by=sort_by,
            sort_dir=sort_dir,
            page=page,
            page_size=page_size,
        )
    except ValueError as exc:
        log_error(f"Erro de validação em settlements receivables: {exc}")
        return error_response(str(exc), status_code=400)

    return execute_settlements_route(
        use_case_builder=build_get_settlements_use_case,
        request=request,
        side=SETTLEMENT_SIDE_RECEIVABLE,
        operation_id="get_financeiro_settlements_receivables",
        success_message="Receivable settlement events loaded successfully.",
        error_context="carregar baixas a receber",
        user_subject=delegated_user_subject(),
    )


@router.get(
    "/summary",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_financeiro_settlements_summary",
        path="/financeiro/settlements/summary",
    ),
)
@_settlements_s2s_guard
def get_financeiro_settlements_summary_route(
    start_date: Optional[str] = PERIOD_START_QUERY(),
    end_date: Optional[str] = PERIOD_END_QUERY(),
    nature_code: Optional[str] = NATURE_CODE_QUERY(),
    movement_type: Optional[str] = MOVEMENT_TYPE_QUERY(),
):
    try:
        request = build_settlements_request(
            start_date=start_date,
            end_date=end_date,
            nature_code=nature_code,
            movement_type=movement_type,
        )
    except ValueError as exc:
        log_error(f"Erro de validação em settlements summary: {exc}")
        return error_response(str(exc), status_code=400)

    return execute_settlements_route(
        use_case_builder=build_get_settlements_summary_use_case,
        request=request,
        operation_id="get_financeiro_settlements_summary",
        success_message="Financial settlements summary loaded successfully.",
        error_context="carregar resumo de baixas",
        user_subject=delegated_user_subject(),
    )

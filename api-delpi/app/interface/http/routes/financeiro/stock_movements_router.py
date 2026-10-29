"""R05 operational stock-movements summary query (MATR320 rule, doc 85 §5).

Guard: S2S-only — same contract family as the sibling stock-inventory
route: the ``stock-inventory.read`` scope on the technical client
``controllership-finance-api`` plus the delegated human Bearer
(ADR-010). Branch is a data filter, not an access boundary (doc 49 §8).
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query

from app.application.dto.financeiro_stock_movements.stock_movements_request import (
    StockMovementsQueryRequest,
)
from app.application.security.stock_inventory_scope import (
    StockInventoryScopeUnavailableError,
)
from app.application.use_cases.financeiro_reports_export.report_export_common import (
    EXPORT_FORMATS,
    ReportExportTruncatedError,
    ReportNotExportableError,
)
from app.composition.financeiro_stock_movements_composer import (
    build_export_stock_movements_use_case,
    build_stock_movements_use_case,
)
from app.core.responses import error_response
from app.interface.http.openapi_agent_metadata_builder import (
    OpenApiAgentMetadataBuilder,
)
from app.interface.http.route_response_helpers import api_delpi_success
from app.interface.http.routes.financeiro.stock_inventory_route_helpers import (
    BRANCH_QUERY,
    PERIOD_QUERY,
    REPORT_SCOPE_QUERY,
    delegated_user_subject,
    export_binary_response,
)
from app.interface.http.s2s_service_access import require_s2s_service
from app.utils.logger import log_error

router = APIRouter(
    prefix="/financeiro/stock-movements",
    tags=["Financeiro — Stock Movements"],
)

STOCK_MOVEMENTS_S2S_REQUIRED_SCOPES = ("stock-inventory.read",)
STOCK_MOVEMENTS_S2S_ALLOWED_CLIENTS = ("controllership-finance-api",)


def _stock_movements_s2s_guard(fn):
    return require_s2s_service(
        required_scopes=STOCK_MOVEMENTS_S2S_REQUIRED_SCOPES,
        allowed_clients=STOCK_MOVEMENTS_S2S_ALLOWED_CLIENTS,
    )(fn)


def _build_request(
    *, period: str, branch: Optional[str], report_scope: Optional[str]
) -> StockMovementsQueryRequest:
    return StockMovementsQueryRequest.from_query(
        period=period, branch=branch, report_scope=report_scope
    )


@router.get(
    "",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_financeiro_stock_movements",
        path="/financeiro/stock-movements",
    ),
)
@_stock_movements_s2s_guard
def get_financeiro_stock_movements_route(
    period: str = PERIOD_QUERY(),
    branch: Optional[str] = BRANCH_QUERY(),
    report_scope: Optional[str] = REPORT_SCOPE_QUERY(),
):
    try:
        request = _build_request(
            period=period, branch=branch, report_scope=report_scope
        )
    except ValueError as exc:
        log_error(f"Erro de validação em stock movements: {exc}")
        return error_response(str(exc), status_code=400)

    try:
        result = build_stock_movements_use_case().execute(
            request, user_subject=delegated_user_subject()
        )
        return api_delpi_success(
            result.to_dict(),
            operation_id="get_financeiro_stock_movements",
            message="Stock movements summary loaded successfully.",
        )
    except StockInventoryScopeUnavailableError as exc:
        log_error(
            f"Escopo financeiro não resolvido ao carregar R05: {exc}"
        )
        return error_response(
            "Escopo de dados financeiros não autorizado.",
            status_code=403,
            code="scope_unavailable",
            recoverable=False,
        )
    except ValueError as exc:
        log_error(f"Erro de validação ao carregar R05: {exc}")
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro ao carregar R05: {exc}")
        return error_response(
            "Erro interno ao carregar o resumo de entradas e saídas.",
            status_code=500,
        )


@router.get(
    "/export",
    **OpenApiAgentMetadataBuilder.from_contract(
        "export_financeiro_stock_movements",
        path="/financeiro/stock-movements/export",
    ),
)
@_stock_movements_s2s_guard
def export_financeiro_stock_movements_route(
    period: str = PERIOD_QUERY(),
    branch: Optional[str] = BRANCH_QUERY(),
    report_scope: Optional[str] = REPORT_SCOPE_QUERY(),
    export_format: str = Query(
        "csv",
        alias="format",
        pattern="^(csv|pdf)$",
        description="Export format — csv or pdf.",
    ),
):
    """Export of the SAME R05 engine payload (CSV or PDF): metadata
    identity, SHA-256 content hash and parity watermark — never an
    official seal."""
    try:
        request = _build_request(
            period=period, branch=branch, report_scope=report_scope
        )
    except ValueError as exc:
        log_error(f"Erro de validação em stock movements export: {exc}")
        return error_response(str(exc), status_code=400)

    if export_format not in EXPORT_FORMATS:
        return error_response("format inválido.", status_code=400)

    try:
        result = build_export_stock_movements_use_case().execute(
            request,
            export_format=export_format,
            user_subject=delegated_user_subject(),
        )
    except StockInventoryScopeUnavailableError as exc:
        log_error(f"Escopo financeiro não resolvido ao exportar R05: {exc}")
        return error_response(
            "Escopo de dados financeiros não autorizado.",
            status_code=403,
            code="scope_unavailable",
            recoverable=False,
        )
    except ReportNotExportableError as exc:
        return error_response(
            "Relatório indisponível para exportação no estado atual.",
            status_code=409,
            code="not_exportable",
            recoverable=False,
        )
    except ReportExportTruncatedError as exc:
        log_error(f"Export R05 truncada: {exc}")
        return error_response(
            "Exportação incompleta — volume acima do limite suportado.",
            status_code=503,
        )
    except ValueError as exc:
        log_error(f"Erro de validação ao exportar R05: {exc}")
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro ao exportar R05: {exc}")
        return error_response(
            "Erro interno ao exportar o resumo de entradas e saídas.",
            status_code=500,
        )

    return export_binary_response(result)

"""R08 operational work-in-process query (MATR989 rule, doc 80 §41).

Same S2S contract family as the sibling stock-inventory route —
``stock-inventory.read`` scope on ``controllership-finance-api`` plus
the delegated human Bearer (ADR-010). One engine: the response is the
standalone surface of the same MATR989 composition the P7 engine
certifies.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query

from app.application.security.stock_inventory_scope import (
    StockInventoryScopeUnavailableError,
)
from app.application.use_cases.financeiro_reports_export.report_export_common import (
    EXPORT_FORMATS,
    ReportExportTruncatedError,
    ReportNotExportableError,
)
from app.composition.financeiro_work_in_process_composer import (
    build_export_work_in_process_use_case,
    build_work_in_process_use_case,
)
from app.core.responses import error_response
from app.interface.http.openapi_agent_metadata_builder import (
    OpenApiAgentMetadataBuilder,
)
from app.interface.http.route_response_helpers import api_delpi_success
from app.interface.http.routes.financeiro.stock_inventory_route_helpers import (
    BRANCH_QUERY,
    PAGE_QUERY,
    PERIOD_QUERY,
    REPORT_SCOPE_QUERY,
    STOCK_INVENTORY_PAGE_SIZE_QUERY,
    WAREHOUSE_QUERY,
    build_stock_inventory_request,
    delegated_user_subject,
    export_binary_response,
)
from app.interface.http.s2s_service_access import require_s2s_service
from app.utils.logger import log_error

router = APIRouter(
    prefix="/financeiro/work-in-process",
    tags=["Financeiro — Work In Process"],
)

WORK_IN_PROCESS_S2S_REQUIRED_SCOPES = ("stock-inventory.read",)
WORK_IN_PROCESS_S2S_ALLOWED_CLIENTS = ("controllership-finance-api",)


def _work_in_process_s2s_guard(fn):
    return require_s2s_service(
        required_scopes=WORK_IN_PROCESS_S2S_REQUIRED_SCOPES,
        allowed_clients=WORK_IN_PROCESS_S2S_ALLOWED_CLIENTS,
    )(fn)


@router.get(
    "",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_financeiro_work_in_process",
        path="/financeiro/work-in-process",
    ),
)
@_work_in_process_s2s_guard
def get_financeiro_work_in_process_route(
    period: str = PERIOD_QUERY(),
    branch: Optional[str] = BRANCH_QUERY(),
    report_scope: Optional[str] = REPORT_SCOPE_QUERY(),
    warehouse: Optional[str] = WAREHOUSE_QUERY(),
    page: int = PAGE_QUERY(),
    page_size: int = STOCK_INVENTORY_PAGE_SIZE_QUERY(),
):
    try:
        request = build_stock_inventory_request(
            period=period,
            branch=branch,
            report_scope=report_scope,
            warehouse=warehouse,
            page=page,
            page_size=page_size,
        )
    except ValueError as exc:
        log_error(f"Erro de validação em work in process: {exc}")
        return error_response(str(exc), status_code=400)

    try:
        result = build_work_in_process_use_case().execute(
            request, user_subject=delegated_user_subject()
        )
        return api_delpi_success(
            result.to_dict(),
            operation_id="get_financeiro_work_in_process",
            message="Work-in-process report loaded successfully.",
        )
    except StockInventoryScopeUnavailableError as exc:
        log_error(
            f"Escopo financeiro não resolvido ao carregar R08: {exc}"
        )
        return error_response(
            "Escopo de dados financeiros não autorizado.",
            status_code=403,
            code="scope_unavailable",
            recoverable=False,
        )
    except ValueError as exc:
        log_error(f"Erro de validação ao carregar R08: {exc}")
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro ao carregar R08: {exc}")
        return error_response(
            "Erro interno ao carregar o material em processo.",
            status_code=500,
        )


@router.get(
    "/export",
    **OpenApiAgentMetadataBuilder.from_contract(
        "export_financeiro_work_in_process",
        path="/financeiro/work-in-process/export",
    ),
)
@_work_in_process_s2s_guard
def export_financeiro_work_in_process_route(
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
    """Export of the SAME MATR989 payload (CSV or PDF): metadata
    identity, SHA-256 content hash and parity watermark — never an
    official seal."""
    try:
        request = build_stock_inventory_request(
            period=period,
            branch=branch,
            report_scope=report_scope,
            warehouse=None,
            page=1,
            page_size=50,
        )
    except ValueError as exc:
        log_error(f"Erro de validação em work-in-process export: {exc}")
        return error_response(str(exc), status_code=400)

    if export_format not in EXPORT_FORMATS:
        return error_response("format inválido.", status_code=400)

    try:
        result = build_export_work_in_process_use_case().execute(
            request,
            export_format=export_format,
            user_subject=delegated_user_subject(),
        )
    except StockInventoryScopeUnavailableError as exc:
        log_error(f"Escopo financeiro não resolvido ao exportar R08: {exc}")
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
        log_error(f"Export R08 truncada: {exc}")
        return error_response(
            "Exportação incompleta — volume acima do limite suportado.",
            status_code=503,
        )
    except ValueError as exc:
        log_error(f"Erro de validação ao exportar R08: {exc}")
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro ao exportar R08: {exc}")
        return error_response(
            "Erro interno ao exportar o material em processo.",
            status_code=500,
        )

    return export_binary_response(result)

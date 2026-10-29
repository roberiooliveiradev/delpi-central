"""R03/P7 operational stock-inventory snapshot query (SB9/SB1, doc 49).

Guard: S2S-only — the dedicated ``stock-inventory.read`` scope on the
technical client ``controllership-finance-api`` plus the delegated human
Bearer (ADR-010). Branch is a data filter, not an access boundary (PO
decision, doc 49 §8).
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from app.application.use_cases.financeiro_stock_inventory.export_stock_inventory_use_case import (
    EXPORT_PAGE_SIZE,
    StockInventoryExportTruncatedError,
    StockInventoryNotExportableError,
)
from app.application.security.stock_inventory_scope import (
    StockInventoryScopeUnavailableError,
)
from app.composition.financeiro_stock_inventory_composer import (
    build_export_stock_inventory_use_case,
    build_stock_inventory_use_case,
)
from app.core.responses import error_response
from app.interface.http.openapi_agent_metadata_builder import (
    OpenApiAgentMetadataBuilder,
)
from app.interface.http.routes.financeiro.stock_inventory_route_helpers import (
    BRANCH_QUERY,
    PAGE_QUERY,
    PERIOD_QUERY,
    REPORT_SCOPE_QUERY,
    STOCK_INVENTORY_PAGE_SIZE_QUERY,
    WAREHOUSE_QUERY,
    build_stock_inventory_request,
    delegated_user_subject,
    execute_stock_inventory_route,
)
from app.interface.http.s2s_service_access import require_s2s_service
from app.utils.logger import log_error

router = APIRouter(
    prefix="/financeiro/stock-inventory",
    tags=["Financeiro — Stock Inventory"],
)

# Individual S2S contract (ADR-010): only the Controladoria & Finanças BFF
# client-credentials principal may call this route, and only with the
# stock-inventory scope. A dedicated user Bearer is still mandatory — the
# shared internal token never authorizes this surface.
STOCK_INVENTORY_S2S_REQUIRED_SCOPES = ("stock-inventory.read",)
STOCK_INVENTORY_S2S_ALLOWED_CLIENTS = ("controllership-finance-api",)


def _stock_inventory_s2s_guard(fn):
    return require_s2s_service(
        required_scopes=STOCK_INVENTORY_S2S_REQUIRED_SCOPES,
        allowed_clients=STOCK_INVENTORY_S2S_ALLOWED_CLIENTS,
    )(fn)


@router.get(
    "",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_financeiro_stock_inventory",
        path="/financeiro/stock-inventory",
    ),
)
@_stock_inventory_s2s_guard
def get_financeiro_stock_inventory_route(
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
        log_error(f"Erro de validação em stock inventory: {exc}")
        return error_response(str(exc), status_code=400)

    return execute_stock_inventory_route(
        use_case_builder=build_stock_inventory_use_case,
        request=request,
        operation_id="get_financeiro_stock_inventory",
        success_message="Stock inventory snapshot loaded successfully.",
        error_context="carregar estoque histórico",
        user_subject=delegated_user_subject(),
    )


@router.get(
    "/export",
    **OpenApiAgentMetadataBuilder.from_contract(
        "export_financeiro_stock_inventory",
        path="/financeiro/stock-inventory/export",
    ),
)
@_stock_inventory_s2s_guard
def export_financeiro_stock_inventory_route(
    period: str = PERIOD_QUERY(),
    branch: Optional[str] = BRANCH_QUERY(),
    report_scope: Optional[str] = REPORT_SCOPE_QUERY(),
    warehouse: Optional[str] = WAREHOUSE_QUERY(),
    export_format: str = Query(
        "csv",
        alias="format",
        pattern="^csv$",
        description="Export format — csv only while parity is pending.",
    ),
):
    """CSV document of the SAME P7 engine (doc 119 §8.C): metadata header,
    SHA-256 content hash and parity watermark — never an official seal."""
    try:
        request = build_stock_inventory_request(
            period=period,
            branch=branch,
            report_scope=report_scope,
            warehouse=warehouse,
            page=1,
            page_size=EXPORT_PAGE_SIZE,
        )
    except ValueError as exc:
        log_error(f"Erro de validação em stock inventory export: {exc}")
        return error_response(str(exc), status_code=400)

    try:
        result = build_export_stock_inventory_use_case().execute(
            request, user_subject=delegated_user_subject()
        )
    except StockInventoryScopeUnavailableError as exc:
        log_error(
            f"Escopo financeiro não resolvido ao exportar P7: {exc}"
        )
        return error_response(
            "Escopo de dados financeiros não autorizado.",
            status_code=403,
            code="scope_unavailable",
            recoverable=False,
        )
    except StockInventoryNotExportableError as exc:
        return error_response(
            "Relatório indisponível para exportação no estado atual.",
            status_code=409,
            code="not_exportable",
            recoverable=False,
        )
    except StockInventoryExportTruncatedError as exc:
        log_error(f"Export P7 truncada: {exc}")
        return error_response(
            "Exportação incompleta — volume acima do limite suportado.",
            status_code=503,
        )
    except ValueError as exc:
        log_error(f"Erro de validação ao exportar P7: {exc}")
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro ao exportar P7: {exc}")
        return error_response(
            "Erro interno ao exportar o registro de inventário.",
            status_code=500,
        )

    return StreamingResponse(
        result["stream"],
        media_type=result["content_type"],
        headers={
            "Content-Disposition": (
                f'attachment; filename="{result["filename"]}"'
            ),
            "X-Exported-Count": str(result["exported_count"]),
        },
    )

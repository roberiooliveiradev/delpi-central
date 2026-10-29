from __future__ import annotations

from typing import Any, Callable, Optional

from fastapi import Query, Response

from delpi_auth.context_resolver import resolve_user_context

from app.application.dto.financeiro_stock_inventory.constantes import (
    DEFAULT_PAGE,
    DEFAULT_PAGE_SIZE,
    REPORT_SCOPE_ALL_PRODUCTS,
)
from app.application.dto.financeiro_stock_inventory.stock_inventory_request import (
    StockInventoryQueryRequest,
)
from app.application.security.stock_inventory_scope import (
    StockInventoryScopeUnavailableError,
)
from app.core.responses import error_response
from app.interface.http.pagination_query import PAGE_SIZE_QUERY
from app.interface.http.route_response_helpers import api_delpi_success
from app.utils.logger import log_error


def PERIOD_QUERY():
    return Query(
        ...,
        description=(
            "Competence in YYYY-MM. The SB9 snapshot is read at the last "
            "calendar day of that month (no month substitution)."
        ),
    )


def BRANCH_QUERY():
    return Query(
        "all",
        description="Branch data filter: all | 01 | 02 (data scope only).",
    )


def REPORT_SCOPE_QUERY():
    return Query(
        REPORT_SCOPE_ALL_PRODUCTS,
        description="Operational view: all_products | mp_pi_pa.",
    )


def WAREHOUSE_QUERY():
    return Query(None, description="Warehouse filter (SB9 B9_LOCAL).")


def PAGE_QUERY():
    return Query(DEFAULT_PAGE, ge=1, description="Page number (minimum 1).")


def STOCK_INVENTORY_PAGE_SIZE_QUERY():
    return PAGE_SIZE_QUERY("page_50_200")


def build_stock_inventory_request(
    *,
    period: Optional[str],
    branch: Optional[str] = None,
    report_scope: Optional[str] = None,
    warehouse: Optional[str] = None,
    page: int = DEFAULT_PAGE,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> StockInventoryQueryRequest:
    return StockInventoryQueryRequest.from_query(
        period=period,
        branch=branch,
        report_scope=report_scope,
        warehouse=warehouse,
        page=page,
        page_size=page_size,
    )


def export_binary_response(result: dict[str, Any]) -> Response:
    """Buffered binary response for the shared CSV/PDF export contract.

    Export payloads are already fully materialized (``io.BytesIO``).
    Serving them via ``StreamingResponse`` iterates the buffer line by
    line on ``\\n`` bytes — pathological for binary content (~40 KB/s on
    multi-MB PDFs). A plain ``Response`` sends the body at once and sets
    ``Content-Length``, which browsers need for download progress.
    """
    stream = result["stream"]
    body = (
        stream.getvalue()
        if hasattr(stream, "getvalue")
        else b"".join(stream)
    )
    return Response(
        content=body,
        media_type=result["content_type"],
        headers={
            "Content-Disposition": (
                f'attachment; filename="{result["filename"]}"'
            ),
            "X-Exported-Count": str(result["exported_count"]),
        },
    )


def delegated_user_subject() -> str | None:
    """Subject of the delegated user principal, or ``None`` if the caller is
    not a human end user (legacy service token principals never qualify)."""
    user = resolve_user_context()
    if user is None or getattr(user, "principal_type", None) != "user":
        return None
    return getattr(user, "id", None) or getattr(user, "email", None)


def execute_stock_inventory_route(
    *,
    use_case_builder: Callable[[], Any],
    request: StockInventoryQueryRequest,
    operation_id: str,
    success_message: str,
    error_context: str,
    user_subject: str | None,
):
    try:
        use_case = use_case_builder()
        result = use_case.execute(request, user_subject=user_subject)
        return api_delpi_success(
            result.to_dict(),
            operation_id=operation_id,
            message=success_message,
        )
    except StockInventoryScopeUnavailableError as exc:
        log_error(f"Escopo financeiro não resolvido ao {error_context}: {exc}")
        return error_response(
            "Escopo de dados financeiros não autorizado.",
            status_code=403,
            code="scope_unavailable",
            recoverable=False,
        )
    except ValueError as exc:
        log_error(f"Erro de validação ao {error_context}: {exc}")
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro ao {error_context}: {exc}")
        return error_response(
            f"Erro interno ao {error_context}.",
            status_code=500,
        )

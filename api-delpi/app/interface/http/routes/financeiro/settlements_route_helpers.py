from __future__ import annotations

from typing import Any, Callable, Optional

from fastapi import Query

from delpi_auth.context_resolver import resolve_user_context

from app.application.dto.financeiro_settlements.constantes import (
    DEFAULT_PAGE,
    DEFAULT_PAGE_SIZE,
    DEFAULT_SORT_BY,
    DEFAULT_SORT_DIR,
)
from app.application.dto.financeiro_settlements.settlements_request import (
    SettlementsQueryRequest,
)
from app.application.security.settlement_scope import (
    SettlementScopeUnavailableError,
)
from app.core.responses import error_response
from app.interface.http.pagination_query import PAGE_SIZE_QUERY
from app.interface.http.query_param_enums import (
    SORT_DIR_QUERY_DESC as SORT_DIR_QUERY,
)
from app.interface.http.route_response_helpers import api_delpi_success
from app.utils.logger import log_error


def PERIOD_START_QUERY():
    return Query(
        None,
        description="Start date, inclusive (YYYY-MM-DD or YYYYMMDD).",
    )


def PERIOD_END_QUERY():
    return Query(
        None,
        description="End date, inclusive (YYYY-MM-DD or YYYYMMDD).",
    )


def NATURE_CODE_QUERY():
    return Query(None, description="Nature code filter (SED ED_CODIGO).")


def MOVEMENT_TYPE_QUERY():
    return Query(
        None,
        description=(
            "Raw movement code filter (FKx_TPDOC). Codes are source values; "
            "their business semantics are not classified yet."
        ),
    )


def PAGE_QUERY():
    return Query(DEFAULT_PAGE, ge=1, description="Page number (minimum 1).")


def SETTLEMENTS_PAGE_SIZE_QUERY():
    return PAGE_SIZE_QUERY("page_50_200")


def SORT_BY_QUERY():
    return Query(
        DEFAULT_SORT_BY,
        description="Sortable field whitelist: settlement_date | nature.",
    )


def SETTLEMENTS_SORT_DIR_QUERY():
    return SORT_DIR_QUERY()


def build_settlements_request(
    *,
    start_date: Optional[str],
    end_date: Optional[str],
    nature_code: Optional[str] = None,
    movement_type: Optional[str] = None,
    sort_by: str = DEFAULT_SORT_BY,
    sort_dir: str = DEFAULT_SORT_DIR,
    page: int = DEFAULT_PAGE,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> SettlementsQueryRequest:
    return SettlementsQueryRequest.from_query(
        start_date=start_date,
        end_date=end_date,
        nature_code=nature_code,
        movement_type=movement_type,
        sort_by=sort_by,
        sort_dir=sort_dir,
        page=page,
        page_size=page_size,
    )


def delegated_user_subject() -> str | None:
    """Subject of the delegated user principal, or ``None`` if the caller is
    not a human end user (legacy service token principals never qualify)."""
    user = resolve_user_context()
    if user is None or getattr(user, "principal_type", None) != "user":
        return None
    return getattr(user, "id", None) or getattr(user, "email", None)


def execute_settlements_route(
    *,
    use_case_builder: Callable[[], Any],
    request: SettlementsQueryRequest,
    operation_id: str,
    success_message: str,
    error_context: str,
    user_subject: str | None,
    side: str | None = None,
):
    try:
        use_case = use_case_builder()
        if side is None:
            result = use_case.execute(request, user_subject=user_subject)
        else:
            result = use_case.execute(
                request, side=side, user_subject=user_subject
            )
        return api_delpi_success(
            result.to_dict(),
            operation_id=operation_id,
            message=success_message,
        )
    except SettlementScopeUnavailableError as exc:
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

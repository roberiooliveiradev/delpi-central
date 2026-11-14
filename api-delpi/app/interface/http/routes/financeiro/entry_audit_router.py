"""Read-only Protheus extracts for the entry audit.

Guard: the same individual S2S contract as the other financeiro routes
the controllership BFF calls (``stock-inventory.read`` on the client
``controllership-finance-api``, plus the delegated user Bearer). No new
permission and no dataset flag — ``ENTRY_AUDIT_ENABLED`` lives on the BFF.
Fiscal rules stay out of this service.
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.application.dto.financeiro_entry_audit.entry_audit_query import (
    EntryAuditQueryError,
    EntryAuditPeriodQuery,
)
from app.composition.financeiro_entry_audit_composer import (
    build_list_entry_audit_use_case,
)
from app.core.responses import error_response
from app.interface.http.openapi_agent_metadata_builder import (
    OpenApiAgentMetadataBuilder,
)
from app.interface.http.pagination_query import PAGE_SIZE_QUERY
from app.interface.http.route_response_helpers import api_delpi_success
from app.interface.http.routes.financeiro.stock_inventory_route_helpers import (
    delegated_user_subject,
)
from app.interface.http.s2s_service_access import require_s2s_service
from app.utils.logger import log_error

router = APIRouter(
    prefix="/financeiro/entry-audit",
    tags=["Financeiro — Entry Audit"],
)

ENTRY_AUDIT_S2S_REQUIRED_SCOPES = ("stock-inventory.read",)
ENTRY_AUDIT_S2S_ALLOWED_CLIENTS = ("controllership-finance-api",)


def _guard(fn):
    return require_s2s_service(
        required_scopes=ENTRY_AUDIT_S2S_REQUIRED_SCOPES,
        allowed_clients=ENTRY_AUDIT_S2S_ALLOWED_CLIENTS,
    )(fn)


def _meta(operation_id: str, path: str) -> dict:
    """OpenAPI summary/description. ``operation_id`` stays a literal on the route."""
    meta = OpenApiAgentMetadataBuilder.from_contract(operation_id, path=path)
    meta.pop("operation_id", None)
    return meta


def _page_query():
    return Query(1, ge=1, description="Page number (minimum 1).")


def _received_from_query():
    return Query(..., description="Receipt date from, YYYY-MM-DD (F1_RECBMTO).")


def _received_to_query():
    return Query(..., description="Receipt date to, YYYY-MM-DD (F1_RECBMTO).")


def _branch_query():
    return Query(..., description="Branch data filter: 01 or 02.")


def _species_query():
    return Query(
        default=["SPED", "CTE"],
        description="Document species: SPED (NF-e) or CTE (CT-e). Repeatable.",
    )


def _require_user():
    if delegated_user_subject() is None:
        return error_response(
            "Delegated user bearer is required.",
            status_code=403,
            code="DELEGATED_USER_REQUIRED",
            recoverable=False,
        )
    return None


def _period(
    *,
    branch: str,
    received_from: str,
    received_to: str,
    species: list[str],
    page: int,
    page_size: int,
) -> EntryAuditPeriodQuery | object:
    try:
        return EntryAuditPeriodQuery.from_query(
            branch=branch,
            received_from=received_from,
            received_to=received_to,
            species=species,
            page=page,
            page_size=page_size,
        )
    except EntryAuditQueryError as exc:
        return error_response(str(exc), status_code=422, code="VALIDATION_ERROR")


def _run(loader, operation_id: str, message: str):
    denied = _require_user()
    if denied is not None:
        return denied
    try:
        data = loader(build_list_entry_audit_use_case())
    except Exception as exc:
        log_error(f"Erro ao ler entry-audit {operation_id}: {exc}")
        return error_response(
            "Erro interno ao ler os documentos de entrada.",
            status_code=500,
        )
    return api_delpi_success(data=data, message=message, operation_id=operation_id)


@router.get(
    "/documents",
    operation_id="list_entry_audit_documents",
    **_meta("list_entry_audit_documents", "/financeiro/entry-audit/documents"),
)
@_guard
def list_entry_audit_documents_route(
    branch: str = _branch_query(),
    received_from: str = _received_from_query(),
    received_to: str = _received_to_query(),
    species: list[str] = _species_query(),
    page: int = _page_query(),
    page_size: int = PAGE_SIZE_QUERY("page_50_200"),
):
    query = _period(
        branch=branch,
        received_from=received_from,
        received_to=received_to,
        species=species,
        page=page,
        page_size=page_size,
    )
    if not isinstance(query, EntryAuditPeriodQuery):
        return query
    return _run(
        lambda use_case: use_case.documents(query),
        "list_entry_audit_documents",
        "Entry audit documents loaded successfully.",
    )


@router.get(
    "/items",
    operation_id="list_entry_audit_items",
    **_meta("list_entry_audit_items", "/financeiro/entry-audit/items"),
)
@_guard
def list_entry_audit_items_route(
    branch: str = _branch_query(),
    received_from: str = _received_from_query(),
    received_to: str = _received_to_query(),
    species: list[str] = _species_query(),
    page: int = _page_query(),
    page_size: int = PAGE_SIZE_QUERY("page_50_200"),
):
    query = _period(
        branch=branch,
        received_from=received_from,
        received_to=received_to,
        species=species,
        page=page,
        page_size=page_size,
    )
    if not isinstance(query, EntryAuditPeriodQuery):
        return query
    return _run(
        lambda use_case: use_case.items(query),
        "list_entry_audit_items",
        "Entry audit items loaded successfully.",
    )


@router.get(
    "/fiscal-book",
    operation_id="list_entry_audit_fiscal_book",
    **_meta("list_entry_audit_fiscal_book", "/financeiro/entry-audit/fiscal-book"),
)
@_guard
def list_entry_audit_fiscal_book_route(
    branch: str = _branch_query(),
    received_from: str = _received_from_query(),
    received_to: str = _received_to_query(),
    species: list[str] = _species_query(),
    page: int = _page_query(),
    page_size: int = PAGE_SIZE_QUERY("page_50_200"),
):
    query = _period(
        branch=branch,
        received_from=received_from,
        received_to=received_to,
        species=species,
        page=page,
        page_size=page_size,
    )
    if not isinstance(query, EntryAuditPeriodQuery):
        return query
    return _run(
        lambda use_case: use_case.fiscal_book(query),
        "list_entry_audit_fiscal_book",
        "Entry audit fiscal book loaded successfully.",
    )


@router.get(
    "/tes",
    operation_id="list_entry_audit_tes",
    **_meta("list_entry_audit_tes", "/financeiro/entry-audit/tes"),
)
@_guard
def list_entry_audit_tes_route(
    page: int = _page_query(),
    page_size: int = PAGE_SIZE_QUERY("page_50_200"),
):
    if page_size < 1 or page_size > 200:
        return error_response(
            "page_size must be between 1 and 200.",
            status_code=422,
            code="VALIDATION_ERROR",
        )
    return _run(
        lambda use_case: use_case.tes(page=page, page_size=page_size),
        "list_entry_audit_tes",
        "Entry audit TES catalog loaded successfully.",
    )


@router.get(
    "/branches",
    operation_id="list_entry_audit_branches",
    **_meta("list_entry_audit_branches", "/financeiro/entry-audit/branches"),
)
@_guard
def list_entry_audit_branches_route():
    return _run(
        lambda use_case: use_case.branches(),
        "list_entry_audit_branches",
        "Entry audit branches loaded successfully.",
    )

"""Supplies supplier master-data reads — SA2010 (company 01).

Serves the Portal Suprimentos BFF through the individual S2S credential
(``supplies-api`` client, ``suppliers.read`` scope) and keeps the direct-user
path on the sibling supplies permission set. The legacy shared service token
never authorizes this surface.
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.application.dto.supplies.suppliers_request import SuppliersListRequest
from app.application.security.api_delpi_permissions import KPI_SUPPLIES_ACCESS
from app.composition.supplies_composer import (
    build_list_supplies_suppliers_use_case,
)
from app.core.exceptions import DatabaseConnectionError
from app.core.responses import error_response
from app.interface.http.openapi_agent_metadata_builder import (
    OpenApiAgentMetadataBuilder,
)
from app.interface.http.pagination_query import PAGE_SIZE_QUERY
from app.interface.http.route_response_helpers import api_delpi_success
from app.interface.http.s2s_service_access import require_s2s_or_any_permission
from app.utils.logger import log_error

router = APIRouter(
    prefix="/supplies/suppliers",
    tags=["Supplies — Suppliers"],
)

_SUPPLIERS_READ_SCOPE = ("suppliers.read",)
_SUPPLIES_BFF_CLIENTS = ("supplies-api",)
_SORT_BY_VALUES = ("supplier_name", "supplier_code", "tax_id", "state")
_SORT_DIR_VALUES = ("asc", "desc")

_ITEM_FIELDS = [
    "supplier_id",
    "supplier_code",
    "supplier_store",
    "supplier_name",
    "supplier_short_name",
    "tax_id",
    "state",
    "blocked",
]


@router.get(
    "",
    **OpenApiAgentMetadataBuilder.from_contract(
        "list_supplies_suppliers",
        path="/supplies/suppliers",
    ),
)
@require_s2s_or_any_permission(
    KPI_SUPPLIES_ACCESS,
    required_scopes=_SUPPLIERS_READ_SCOPE,
    allowed_clients=_SUPPLIES_BFF_CLIENTS,
)
def list_supplies_suppliers(
    query: str | None = Query(
        default=None,
        min_length=2,
        description=(
            "Search over supplier code (prefix), legal name and trade name "
            "(accent-insensitive contains), tax id digits, or 'code store' pair."
        ),
    ),
    state: str | None = Query(
        default=None,
        min_length=2,
        max_length=2,
        description="Two-letter state filter (A2_EST).",
    ),
    blocked: bool | None = Query(
        default=None,
        description="Registration block flag (A2_MSBLQL).",
    ),
    page: int = Query(default=1, ge=1),
    page_size: int = PAGE_SIZE_QUERY(
        "page_20_100", description="Rows per page (max 100)."
    ),
    sort_by: str = Query(
        default="supplier_name",
        enum=list(_SORT_BY_VALUES),
        description="Sortable columns: supplier_name, supplier_code, tax_id, state.",
    ),
    sort_dir: str = Query(
        default="asc",
        enum=list(_SORT_DIR_VALUES),
        description="Sort direction.",
    ),
):
    """operationId: list_supplies_suppliers — paged supplier search for the BFF."""
    try:
        request = SuppliersListRequest(
            query=query,
            state=state,
            blocked=blocked,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_dir=sort_dir,
        )
        result = build_list_supplies_suppliers_use_case().execute(request)
        return api_delpi_success(
            result,
            operation_id="list_supplies_suppliers",
            message="Fornecedores buscados com sucesso.",
            fields=_ITEM_FIELDS,
        )
    except ValueError as exc:
        log_error(f"Erro de validação ao listar fornecedores: {exc}")
        return error_response(str(exc), status_code=400)
    except DatabaseConnectionError as exc:
        log_error(f"Erro de banco ao listar fornecedores: {exc}")
        return error_response(
            "Erro de conexão com o banco ao listar fornecedores.",
            status_code=503,
        )
    except Exception as exc:
        log_error(f"Erro ao listar fornecedores: {exc}")
        return error_response(
            "Erro interno ao listar fornecedores.",
            status_code=500,
        )

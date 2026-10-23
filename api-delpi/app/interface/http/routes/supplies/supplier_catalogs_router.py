"""Catálogos TOTVS do cadastro de fornecedores — consultas read-only.

Serve o BFF Portal Suprimentos via credencial S2S individual
(``supplies-api`` client, ``suppliers.read`` scope) e o caminho de usuário
direto pela permissão de Suprimentos. A allowlist de catálogos é fechada no
repositório — nenhum nome vindo do cliente escolhe tabela SQL.
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.application.security.api_delpi_permissions import KPI_SUPPLIES_ACCESS
from app.application.use_cases.supplies.list_supplier_catalog_items_use_case import (
    ListSupplierCatalogItemsUseCase,
)
from app.core.exceptions import DatabaseConnectionError
from app.core.responses import error_response
from app.infrastructure.persistence.totvs.supplier_repositories.totvs_supplier_catalogs_repository import (
    SUPPLIER_CATALOG_KINDS,
    TotvsSupplierCatalogsRepository,
)
from app.interface.http.openapi_agent_metadata_builder import (
    OpenApiAgentMetadataBuilder,
)
from app.interface.http.pagination_query import LIMIT_QUERY
from app.interface.http.route_response_helpers import api_delpi_success
from app.interface.http.s2s_service_access import require_s2s_or_any_permission
from app.utils.logger import log_error

router = APIRouter(
    prefix="/supplies/supplier-catalogs",
    tags=["Supplies — Supplier catalogs"],
)

_SUPPLIERS_READ_SCOPE = ("suppliers.read",)
_SUPPLIES_BFF_CLIENTS = ("supplies-api",)


@router.get(
    "/{catalog}",
    **OpenApiAgentMetadataBuilder.from_contract(
        "list_supplies_supplier_catalog_items",
        path="/supplies/supplier-catalogs/{catalog}",
    ),
)
@require_s2s_or_any_permission(
    KPI_SUPPLIES_ACCESS,
    required_scopes=_SUPPLIERS_READ_SCOPE,
    allowed_clients=_SUPPLIES_BFF_CLIENTS,
)
def list_supplier_catalog_items(
    catalog: str,
    query: str | None = Query(
        default=None,
        max_length=60,
        description="Search by code prefix or description (accent-insensitive).",
    ),
    state: str | None = Query(
        default=None,
        min_length=2,
        max_length=2,
        description="Two-letter UF — required for the 'municipalities' catalog.",
    ),
    code: str | None = Query(
        default=None,
        max_length=6,
        description="Exact code filter — 'customers' only (lists the stores of the given customer).",
    ),
    limit: int = LIMIT_QUERY(
        "limit_100_500",
        description="Max items per page (1-500).",
    ),
):
    """operationId: list_supplies_supplier_catalog_items — opções validadas do Protheus."""
    try:
        result = ListSupplierCatalogItemsUseCase(
            repository=TotvsSupplierCatalogsRepository()
        ).execute(
            catalog,
            query=query,
            state=state,
            code=code,
            limit=limit,
        )
        return api_delpi_success(
            result,
            operation_id="list_supplies_supplier_catalog_items",
            message="Catálogo carregado com sucesso.",
        )
    except ValueError as exc:
        return error_response(str(exc), status_code=400)
    except DatabaseConnectionError as exc:
        log_error(f"Erro de conexão ao consultar catálogo {catalog}: {exc}")
        return error_response(
            "Erro de conexão ao consultar o catálogo.",
            status_code=503,
        )
    except Exception as exc:
        log_error(f"Erro ao consultar catálogo {catalog}: {exc}")
        return error_response(
            "Erro interno ao consultar o catálogo.",
            status_code=500,
        )

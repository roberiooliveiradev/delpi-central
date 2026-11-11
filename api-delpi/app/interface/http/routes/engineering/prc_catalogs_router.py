"""Engineering product-registration read-only catalog routes.

Catálogos TOTVS e busca SA2 autorizados ao bounded context Engenharia
(portal engineering → engineering-api → api-delpi → TOTVS). Permissão de
Engenharia própria — nenhum escopo de Suprimentos é emprestado.
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.application.dto.supplies.suppliers_request import SuppliersListRequest
from app.application.security.api_delpi_permissions import (
    PRC_READ_ACCESS,
)
from app.composition.supplies_composer import (
    build_list_supplies_suppliers_use_case,
)
from app.core.responses import error_response
from app.infrastructure.persistence.totvs.engineering_repositories.prc_catalogs_repository import (
    PRC_CATALOG_KINDS,
    PrcCatalogsRepository,
)
from app.interface.http.pagination_query import PAGE_SIZE_QUERY
from app.interface.http.route_response_helpers import api_delpi_success
from app.utils.logger import log_error
from delpi_auth.authorization import require_any_permission

router = APIRouter(
    prefix="/engineering/product-registration",
    tags=["Engineering — Product Registration"],
)


@router.get("/catalogs/{catalog}", operation_id="prc_catalog_items")
@require_any_permission(PRC_READ_ACCESS)
def list_prc_catalog_items(
    catalog: str,
    query: str | None = Query(
        default=None,
        max_length=60,
        description="Search by code prefix or description (accent-insensitive).",
    ),
    limit: int = Query(default=200, ge=1, le=500),
):
    if catalog not in PRC_CATALOG_KINDS:
        return error_response(
            "Catálogo não suportado.", status_code=404
        )
    try:
        # Instância por request: BaseRepository guarda conexão/cursor em
        # self — compartilhar singleton entre requests concorrentes faz uma
        # thread zerar o cursor da outra ('NoneType' … 'fetchall').
        items, has_more = PrcCatalogsRepository().list_catalog_items(
            catalog, query=query, limit=limit
        )
        return api_delpi_success(
            {
                "items": items,
                "hasMore": has_more,
                "catalog": catalog,
            },
            operation_id="prc_catalog_items",
        )
    except Exception as exc:
        log_error(f"prc_catalog_items failed: {exc}")
        return error_response(
            "Falha ao consultar o catálogo.", status_code=500
        )


@router.get("/suppliers", operation_id="prc_supplier_search")
@require_any_permission(PRC_READ_ACCESS)
def search_prc_suppliers(
    query: str = Query(..., min_length=2, max_length=80),
    page: int = Query(default=1, ge=1),
    page_size: int = PAGE_SIZE_QUERY(
        "page_20_100", description="Rows per page (max 100)."
    ),
):
    try:
        data = build_list_supplies_suppliers_use_case().execute(
            SuppliersListRequest(
                query=query,
                page=page,
                page_size=page_size,
            )
        )
        return api_delpi_success(data, operation_id="prc_supplier_search")
    except Exception as exc:
        log_error(f"prc_supplier_search failed: {exc}")
        return error_response(
            "Falha ao buscar fornecedores.", status_code=500
        )

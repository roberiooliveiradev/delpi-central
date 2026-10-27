"""Product search for the Portal Suprimentos market-intelligence Comex
perspective — read-only TOTVS SB1 access.

Serves the supplies-api BFF via the individual S2S credential
(``supplies-api`` client) and the direct-user path via the supplies
permission. The response is a reduced projection: selection fields plus
the *registered* fiscal classification (``B1_POSIPI``) with a mechanical
format status — the ERP value is never altered and never inferred.
"""

from __future__ import annotations

import re
from typing import Any, Optional

from fastapi import APIRouter, Query

from app.application.dto.product.list_products_requests import (
    ListProductsRequest,
)
from app.application.security.api_delpi_permissions import KPI_SUPPLIES_ACCESS
from app.composition.product_composer import build_search_products_use_case
from app.core.responses import error_response
from app.interface.http.pagination_query import PAGE_SIZE_QUERY
from app.interface.http.query_param_enums import SORT_DIR_QUERY_OPTIONAL
from app.interface.http.route_response_helpers import api_delpi_success
from app.interface.http.s2s_service_access import require_s2s_or_any_permission
from app.utils.logger import log_error

router = APIRouter(
    prefix="/supplies/products",
    tags=["Supplies — Products"],
)

_SUPPLIES_BFF_CLIENTS = ("supplies-api",)

_NCM_RE = re.compile(r"^[0-9]{8}$")


def _ncm_status(raw: str | None) -> str:
    """Mechanical format check on the registered B1_POSIPI value —
    ``missing`` (blank or the ``00000000`` placeholder), ``malformed``
    (nonblank but not 8 numeric digits) or ``present``. Never rewrites
    the stored classification."""
    value = (raw or "").strip()
    if not value or set(value) == {"0"}:
        return "missing"
    return "present" if _NCM_RE.match(value) else "malformed"


def _catalog_item(product: dict[str, Any]) -> dict[str, Any]:
    """Reduced selection projection — no cadastral mirror of SB1."""
    ncm = (product.get("ncm_ipi_position") or "").strip()
    return {
        "code": (product.get("code") or "").strip(),
        "description": (product.get("description") or "").strip(),
        "type": (product.get("type") or "").strip(),
        "group_code": (product.get("group_code") or "").strip(),
        "subgroup": (product.get("subgroup") or "").strip(),
        "unit": (product.get("unit") or "").strip(),
        "ncm_code": ncm or None,
        "ncm_status": _ncm_status(ncm),
        "active": (product.get("active") or "").strip(),
        "blocked": (product.get("blocked") or "").strip(),
    }


@router.get(
    "/search",
    summary="Busca paginada de produtos para seleção Comex (Suprimentos)",
    description=(
        "Busca produtos reais da SB1010 por código, descrição, tipo "
        "(MP/PI/PA), grupo e subgrupo, retornando a NCM cadastrada "
        "(B1_POSIPI) com status de formato. Projeção reduzida de seleção — "
        "não é um espelho do cadastro."
    ),
    operation_id="search_supplies_products",
)
@require_s2s_or_any_permission(
    KPI_SUPPLIES_ACCESS,
    allowed_clients=_SUPPLIES_BFF_CLIENTS,
)
def search_supplies_products(
    code: Optional[str] = Query(None, description="Prefixo do código."),
    description: Optional[str] = Query(
        None,
        description="Termos contidos na descrição (acento-insensível).",
    ),
    product_type: Optional[str] = Query(
        None,
        description=(
            "Tipos de produto (SB1.B1_TIPO) separados por vírgula — "
            "ex.: MP,PI,PA. Códigos de 2 caracteres."
        ),
    ),
    group_code: Optional[str] = Query(
        None, description="Grupo exato (SB1.B1_GRUPO)."
    ),
    subgroup: Optional[str] = Query(
        None, description="Subgrupo exato (SB1.B1_SUBGRUP)."
    ),
    page: int = Query(1, ge=1),
    page_size: int = PAGE_SIZE_QUERY("page_50_500"),
    sort: Optional[str] = Query(None),
    direction: Optional[str] = SORT_DIR_QUERY_OPTIONAL(),
):
    """operationId: search_supplies_products."""
    try:
        type_list = (
            [t.strip().upper() for t in product_type.split(",") if t.strip()]
            if product_type
            else None
        )
        if type_list and any(len(t) != 2 for t in type_list):
            return error_response(
                "product_type inválido: use códigos de 2 caracteres "
                "separados por vírgula (ex.: MP,PI,PA).",
                status_code=400,
            )

        dto = ListProductsRequest(
            code=code,
            group_code=group_code,
            subgroup=subgroup,
            product_type=type_list,
            description=description,
            page=page,
            page_size=page_size,
            sort=sort,
            direction=direction,
        )
        result = build_search_products_use_case().execute(dto)
        payload = result.to_dict()
        payload["items"] = [
            _catalog_item(item) for item in payload.get("items", [])
        ]
        return api_delpi_success(
            payload,
            operation_id="search_supplies_products",
            message="Produtos buscados com sucesso.",
        )

    except Exception as exc:
        log_error(f"Erro ao buscar produtos para Suprimentos: {exc}")
        return error_response(
            "Erro interno ao buscar produtos.",
            status_code=500,
        )

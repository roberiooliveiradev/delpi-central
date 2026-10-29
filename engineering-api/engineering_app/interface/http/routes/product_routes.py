"""E-PRD-01 — estrutura/BOM de produto (G5, READ governado).

Decisão de coordenação: o Portal Engenharia não acessa api-delpi
diretamente. A Engineering API delega o Bearer humano à rota oficial do
owner (`GET /products/{code}/structure` — Products domain) e retorna o
payload oficial intacto, sem reprocessar ou inventar atributos.

AuthZ: `engineering.access` nesta borda; autorização efetiva de produtos
permanece no owner downstream — 401/403 → `forbidden` honesto.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from delpi_auth.authorization import require_any_permission
from delpi_auth.context_resolver import resolve_user_context

from engineering_app.application.ports.home_sources import HomeSourceContext
from engineering_app.composition.lmp_composer import (
    build_delegated_auxiliary_source,
)
from engineering_app.core.responses import fail, ok
from engineering_app.middleware.request_observability_middleware import (
    get_request_id,
)

router = APIRouter()

ENGINEERING_ACCESS = "engineering.access"


@router.get(
    "/v1/products/{product_code}/structure",
    operation_id="get_product_structure",
    summary="Estrutura/BOM do produto — delegação governada ao owner",
)
@require_any_permission([ENGINEERING_ACCESS])
async def get_product_structure(
    product_code: str,
    max_depth: int = Query(default=6, ge=1, le=12),
    page_size: int = Query(default=200, ge=1, le=500),
):
    user = resolve_user_context()
    if getattr(user, "principal_type", None) != "user":
        return fail(
            "Estrutura de produto exige principal humano.",
            403,
            operation_id="get_product_structure",
        )

    code = product_code.strip()
    if not code:
        return fail("product_code obrigatório.", 400, operation_id="get_product_structure")

    ctx = HomeSourceContext(
        user_id=str(getattr(user, "id", "") or ""),
        access_token=str(getattr(user, "access_token", "") or ""),
        request_id=get_request_id(),
    )
    result = await build_delegated_auxiliary_source().fetch_product_structure(
        ctx, code=code, max_depth=max_depth, page_size=page_size
    )
    if result.get("status") == "forbidden":
        return fail(
            "Acesso negado pelo owner de produtos.",
            403,
            operation_id="get_product_structure",
        )
    return ok(
        result,
        message="Estrutura do produto carregada.",
        operation_id="get_product_structure",
    )

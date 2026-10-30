"""E-PRD — catálogo e ficha de produtos (READ governado, doc 63).

Decisão de coordenação: o Portal Engenharia não acessa api-delpi
diretamente. A Engineering API delega o Bearer humano às rotas oficiais
do owner (`/products/*` — Products domain, TOTVS SB1/SG1/SA5 e acervo
de desenhos do file server via Cockpit) e retorna o payload oficial
intacto, sem reprocessar ou inventar atributos.

AuthZ: `engineering.access` nesta borda; autorização efetiva de produtos
permanece no owner downstream — 401/403 → `forbidden` honesto, 404 →
`not_found` honesto (produto sem cadastro/sem desenho), falhas de fonte
→ `unavailable` (nunca dados silenciosos).
"""

from __future__ import annotations

from fastapi import APIRouter, Query, Response
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


def _human_context(operation_id: str):
    """Principal humano obrigatório → HomeSourceContext ou fail 403."""
    user = resolve_user_context()
    if getattr(user, "principal_type", None) != "user":
        return None, fail(
            "Consulta de produtos exige principal humano.",
            403,
            operation_id=operation_id,
        )
    return HomeSourceContext(
        user_id=str(getattr(user, "id", "") or ""),
        access_token=str(getattr(user, "access_token", "") or ""),
        request_id=get_request_id(),
    ), None


def _delegated(
    result: dict,
    *,
    operation_id: str,
    ok_message: str,
    not_found_message: str,
):
    """Estados honestos do adapter delegado → envelope HTTP."""
    status = result.get("status")
    if status == "available":
        return ok(
            result.get("data"),
            message=ok_message,
            operation_id=operation_id,
        )
    if status == "forbidden":
        return fail(
            "Acesso negado pelo owner de produtos.",
            403,
            operation_id=operation_id,
        )
    if status == "not_found":
        return fail(
            not_found_message,
            404,
            operation_id=operation_id,
        )
    return fail(
        "Fonte de produtos indisponível.",
        502,
        data=result,
        operation_id=operation_id,
    )


@router.get(
    "/v1/products",
    operation_id="search_products",
    summary="Busca/listagem de produtos — delegação governada ao owner",
)
@require_any_permission([ENGINEERING_ACCESS])
async def search_products(
    code: str | None = Query(default=None),
    description: str | None = Query(default=None),
    group_code: str | None = Query(default=None),
    subgroup: str | None = Query(default=None),
    product_type: str | None = Query(
        default=None,
        description="Tipos separados por vírgula, códigos de 2 caracteres (ex.: MP,PI,PA).",
    ),
    customer_reference: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=500),
    sort: str | None = Query(default=None),
    direction: str | None = Query(default=None),
):
    ctx, error = _human_context("search_products")
    if error:
        return error
    result = await build_delegated_auxiliary_source().fetch_product_search(
        ctx,
        code=code,
        description=description,
        group_code=group_code,
        subgroup=subgroup,
        product_type=product_type,
        customer_reference=customer_reference,
        page=page,
        page_size=page_size,
        sort=sort,
        direction=direction,
    )
    return _delegated(
        result,
        operation_id="search_products",
        ok_message="Produtos carregados.",
        not_found_message="Nenhum produto encontrado.",
    )


@router.get(
    "/v1/products/{product_code}",
    operation_id="get_product_detail",
    summary="Ficha cadastral do produto (visão engineering, sem custo/fiscal)",
)
@require_any_permission([ENGINEERING_ACCESS])
async def get_product_detail(product_code: str):
    ctx, error = _human_context("get_product_detail")
    if error:
        return error
    code = product_code.strip()
    if not code:
        return fail(
            "product_code obrigatório.", 400, operation_id="get_product_detail"
        )
    result = await build_delegated_auxiliary_source().fetch_product_detail(
        ctx, code=code, view="engineering"
    )
    return _delegated(
        result,
        operation_id="get_product_detail",
        ok_message="Ficha do produto carregada.",
        not_found_message=f"Produto {code} não encontrado.",
    )


@router.get(
    "/v1/products/{product_code}/parents",
    operation_id="get_product_parents",
    summary="Onde o produto é usado (BOM reversa) — delegação governada",
)
@require_any_permission([ENGINEERING_ACCESS])
async def get_product_parents(
    product_code: str,
    max_depth: int | None = Query(default=None, ge=1, le=12),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=200, ge=1, le=500),
):
    ctx, error = _human_context("get_product_parents")
    if error:
        return error
    code = product_code.strip()
    if not code:
        return fail(
            "product_code obrigatório.", 400, operation_id="get_product_parents"
        )
    result = await build_delegated_auxiliary_source().fetch_product_parents(
        ctx, code=code, max_depth=max_depth, page=page, page_size=page_size
    )
    return _delegated(
        result,
        operation_id="get_product_parents",
        ok_message="Onde o produto é usado carregado.",
        not_found_message=f"Produto {code} não encontrado.",
    )


@router.get(
    "/v1/products/{product_code}/suppliers",
    operation_id="get_product_suppliers",
    summary="Fornecedores do produto — delegação governada ao owner",
)
@require_any_permission([ENGINEERING_ACCESS])
async def get_product_suppliers(
    product_code: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=500),
):
    ctx, error = _human_context("get_product_suppliers")
    if error:
        return error
    code = product_code.strip()
    if not code:
        return fail(
            "product_code obrigatório.", 400, operation_id="get_product_suppliers"
        )
    result = await build_delegated_auxiliary_source().fetch_product_suppliers(
        ctx, code=code, page=page, page_size=page_size
    )
    return _delegated(
        result,
        operation_id="get_product_suppliers",
        ok_message="Fornecedores do produto carregados.",
        not_found_message=f"Produto {code} não encontrado.",
    )


@router.get(
    "/v1/products/{product_code}/drawing",
    operation_id="get_product_drawing",
    summary="Metadados do desenho técnico (acervo oficial file server)",
)
@require_any_permission([ENGINEERING_ACCESS])
async def get_product_drawing(product_code: str):
    ctx, error = _human_context("get_product_drawing")
    if error:
        return error
    code = product_code.strip()
    if not code:
        return fail(
            "product_code obrigatório.", 400, operation_id="get_product_drawing"
        )
    result = await build_delegated_auxiliary_source().fetch_product_drawing(
        ctx, code=code
    )
    return _delegated(
        result,
        operation_id="get_product_drawing",
        ok_message="Metadados do desenho carregados.",
        not_found_message=f"Produto {code} sem desenho disponível.",
    )


@router.get(
    "/v1/products/{product_code}/drawing/pdf",
    operation_id="get_product_drawing_pdf",
    summary="PDF do desenho técnico — proxy binário governado ao owner",
)
@require_any_permission([ENGINEERING_ACCESS])
async def get_product_drawing_pdf(product_code: str):
    ctx, error = _human_context("get_product_drawing_pdf")
    if error:
        return error
    code = product_code.strip()
    if not code:
        return fail(
            "product_code obrigatório.", 400, operation_id="get_product_drawing_pdf"
        )
    result = await build_delegated_auxiliary_source().fetch_product_drawing_pdf(
        ctx, code=code
    )
    status = result.get("status")
    if status == "available":
        return Response(
            content=result["content"],
            media_type=result.get("content_type") or "application/pdf",
            headers={
                "Content-Disposition": result.get("content_disposition")
                or f'inline; filename="{code}.pdf"'
            },
        )
    if status == "forbidden":
        return fail(
            "Acesso negado pelo owner do acervo de desenhos.",
            403,
            operation_id="get_product_drawing_pdf",
        )
    if status == "not_found":
        return fail(
            f"Produto {code} sem desenho disponível.",
            404,
            operation_id="get_product_drawing_pdf",
        )
    return fail(
        "Acervo de desenhos indisponível.",
        502,
        data=result,
        operation_id="get_product_drawing_pdf",
    )


@router.get(
    "/v1/products/{product_code}/purchase-price-history",
    operation_id="get_product_purchase_price_history",
    summary="Histórico de preço de compra do produto — delegação governada",
)
@require_any_permission([ENGINEERING_ACCESS])
async def get_product_purchase_price_history(
    product_code: str,
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    branch: str | None = Query(default=None),
    history_limit: int | None = Query(default=None, ge=1, le=500),
):
    ctx, error = _human_context("get_product_purchase_price_history")
    if error:
        return error
    code = product_code.strip()
    if not code:
        return fail(
            "product_code obrigatório.",
            400,
            operation_id="get_product_purchase_price_history",
        )
    result = (
        await build_delegated_auxiliary_source().fetch_product_purchase_price_history(
            ctx,
            code=code,
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            history_limit=history_limit,
        )
    )
    return _delegated(
        result,
        operation_id="get_product_purchase_price_history",
        ok_message="Histórico de preço de compra carregado.",
        not_found_message=f"Produto {code} não encontrado.",
    )


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

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

import hashlib

from fastapi import APIRouter, Query, Response
from delpi_auth.authorization import require_any_permission
from delpi_auth.context_resolver import resolve_user_context

from engineering_app.application.ports.home_sources import HomeSourceContext
from engineering_app.composition.lmp_composer import (
    build_delegated_auxiliary_source,
)
from engineering_app.core.filenames import safe_pdf_filename
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
    group_code: str | None = Query(
        default=None,
        description="Grupos separados por vírgula (ex.: 3019,3020) — semântica OR.",
    ),
    subgroup: str | None = Query(default=None),
    product_type: str | None = Query(
        default=None,
        description="Tipos separados por vírgula, códigos de 2 caracteres (ex.: MP,PI,PA).",
    ),
    customer_reference: str | None = Query(default=None),
    previous_code: str | None = Query(default=None),
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
        previous_code=previous_code,
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
    "/v1/products/filter-options",
    operation_id="get_product_filter_options",
    summary="Opções oficiais de filtro do catálogo (grupos e tipos) — delegação ao owner",
)
@require_any_permission([ENGINEERING_ACCESS])
async def get_product_filter_options():
    ctx, error = _human_context("get_product_filter_options")
    if error:
        return error
    result = await build_delegated_auxiliary_source().fetch_product_filter_options(ctx)
    return _delegated(
        result,
        operation_id="get_product_filter_options",
        ok_message="Opções de filtro carregadas.",
        not_found_message="Opções de filtro indisponíveis.",
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
    "/v1/products/{product_code}/routing",
    operation_id="get_product_routing",
    summary="Roteiro de fabricação do produto (SG2) — delegação governada",
)
@require_any_permission([ENGINEERING_ACCESS])
async def get_product_routing(
    product_code: str,
    branch: str | None = Query(default=None),
    max_depth: int | None = Query(default=None, ge=1, le=15),
    page: int | None = Query(default=None, ge=1),
    page_size: int | None = Query(default=None, ge=1, le=500),
):
    ctx, error = _human_context("get_product_routing")
    if error:
        return error
    code = product_code.strip()
    if not code:
        return fail(
            "product_code obrigatório.", 400, operation_id="get_product_routing"
        )
    result = await build_delegated_auxiliary_source().fetch_product_guide(
        ctx,
        code=code,
        branch=branch.strip() if branch else None,
        max_depth=max_depth,
        page=page,
        page_size=page_size,
    )
    return _delegated(
        result,
        operation_id="get_product_routing",
        ok_message="Roteiro do produto carregado.",
        not_found_message=f"Produto {code} não encontrado ou sem roteiro.",
    )


@router.post(
    "/v1/products/{product_code}/line-balance",
    operation_id="post_product_line_balance",
    summary=(
        "Análise determinística de balanceamento de linha — mesmo "
        "domínio de analyze(routing.line_balance), read-only"
    ),
)
@require_any_permission([ENGINEERING_ACCESS])
async def post_product_line_balance(
    product_code: str,
    body: dict | None = None,
):
    """BFF da calculadora do Portal — delega o Bearer humano à fonte
    oficial de roteiro e executa ``build_balance_result`` (domínio
    EVA). Nenhum cálculo, dedup ou regra no consumidor."""
    from engineering_app.domain.routing.line_balance import (
        BALANCE_INPUT_FIELDS,
        build_balance_result,
        parse_bom_levels,
    )

    ctx, error = _human_context("post_product_line_balance")
    if error:
        return error
    code = product_code.strip()
    if not code:
        return fail(
            "product_code obrigatório.",
            400,
            operation_id="post_product_line_balance",
        )
    params = dict(body or {})
    unknown = sorted(set(params) - BALANCE_INPUT_FIELDS)
    if unknown:
        return fail(
            f"Parâmetros não suportados: {unknown}.",
            400,
            operation_id="post_product_line_balance",
        )
    if "product_code" in params and str(params["product_code"]).strip() != code:
        return fail(
            "product_code do corpo diverge do path.",
            400,
            operation_id="post_product_line_balance",
        )
    try:
        bom_levels = parse_bom_levels(params.get("bom_levels"))
    except ValueError:
        return fail(
            "bom_levels deve ser uma lista de níveis inteiros.",
            400,
            operation_id="post_product_line_balance",
        )
    max_depth = params.get("max_depth")
    if max_depth is not None and not (
        isinstance(max_depth, int)
        and not isinstance(max_depth, bool)
        and 1 <= max_depth <= 15
    ):
        return fail(
            "max_depth deve ser um inteiro entre 1 e 15.",
            400,
            operation_id="post_product_line_balance",
        )
    branch = str(params["branch"]).strip() if params.get("branch") else None
    result = await build_delegated_auxiliary_source().fetch_product_guide(
        ctx,
        code=code,
        branch=branch,
        max_depth=max_depth,
        page=None,
        page_size=None,
    )
    status = (result or {}).get("status")
    if status == "forbidden":
        return fail(
            "Acesso negado pelo owner de produtos.",
            403,
            operation_id="post_product_line_balance",
        )
    if status == "not_found":
        return fail(
            f"Produto {code} não encontrado ou sem roteiro.",
            404,
            operation_id="post_product_line_balance",
        )
    if status != "available":
        return fail(
            "Fonte oficial de roteiro indisponível.",
            502,
            operation_id="post_product_line_balance",
        )
    items = ((result.get("data") or {}).get("items")) or []
    data = build_balance_result(
        items,
        product_code=code,
        branch=branch,
        max_depth=max_depth,
        bom_levels=bom_levels,
        demand=params.get("demand"),
        available_minutes=params.get("available_minutes"),
        batch_size=params.get("batch_size"),
        num_stations=params.get("num_stations"),
    )
    return ok(
        data,
        message="Análise determinística de balanceamento de linha.",
        operation_id="post_product_line_balance",
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
    response_class=Response,
    responses={
        200: {
            "description": "PDF oficial do produto (binário)",
            "content": {
                "application/pdf": {
                    "schema": {"type": "string", "format": "binary"}
                }
            },
        },
        400: {"description": "product_code inválido — envelope JSON"},
        403: {
            "description": "Sem engineering.access ou acesso negado pelo "
            "owner do acervo — envelope JSON"
        },
        404: {
            "description": "Produto sem desenho disponível — envelope JSON"
        },
        502: {
            "description": "Acervo de desenhos indisponível — envelope JSON"
        },
    },
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
        content = result["content"]
        filename = safe_pdf_filename(result.get("filename"), fallback=code)
        return Response(
            content=content,
            media_type="application/pdf",
            headers={
                # attachment fixo — downloadável pelo consumidor (ChatGPT);
                # a disposição upstream (inline) nunca é ecoada.
                "Content-Disposition": f'attachment; filename="{filename}"',
                "X-Document-Sha256": hashlib.sha256(content).hexdigest(),
                "X-Document-Size": str(len(content)),
                "X-Document-Filename": filename,
                "X-Document-Product-Code": code,
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

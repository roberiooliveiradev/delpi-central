from __future__ import annotations

from fastapi import APIRouter, Path, Query

from delpi_auth.authorization import require_any_permission

from app.application.security.api_delpi_permissions import (
    INSPECOES_PROCESSO_READ_PERMISSIONS,
)
from app.composition.process_inspection_plans_composer import (
    build_get_process_inspection_plans_product_use_case,
    build_get_process_inspection_plans_summary_use_case,
    build_list_process_inspection_plans_orders_without_plan_use_case,
    build_list_process_inspection_plans_products_use_case,
    build_list_process_inspection_plans_products_without_plan_use_case,
)
from app.core.responses import error_response, not_found_response
from app.interface.http.openapi_agent_metadata_builder import OpenApiAgentMetadataBuilder
from app.interface.http.query_param_enums import BRANCH_QUERY_OPTIONAL
from app.interface.http.route_response_helpers import api_delpi_success
from app.interface.http.routes.process_inspection_plans.process_inspection_plans_branch_access import (
    branch_access_error,
)
from app.utils.logger import log_error

router = APIRouter(
    prefix="/process-inspection-plans",
    tags=["Planos de inspeção de processo"],
)

# meta.fields em pt-BR — consumo TV/chat (kpi_field_labels / picker de campo).
_SUMMARY_FIELDS = {
    "products_without_plan": "Produtos sem plano de inspeção",
    "orders_without_plan": "OPs abertas sem plano",
    "total_open_orders": "Total de OPs abertas",
    "orders_with_plan": "OPs abertas com plano",
    "registered_pct": "% de inspeções cadastradas",
    "distribution": "Distribuição de ordens",
}

_ORDER_FIELDS = {
    "branch": "Filial",
    "product_code": "Produto",
    "product_description": "Descrição do produto",
    "production_order": "OP",
    "observation": "Observação",
}

_PRODUCT_WITHOUT_FIELDS = {
    "product_code": "Produto",
    "product_description": "Descrição do produto",
    "open_orders_count": "Qtd. de OPs abertas",
}

_PRODUCT_WITH_FIELDS = {
    "product_code": "Produto",
    "product_description": "Descrição do produto",
    "revision": "Revisão ativa",
    "description": "Descrição do plano",
    "inspection_type": "Tipo de inspeção",
    "created_at": "Data de cadastro",
    "start_date": "Data de início",
}

_PRODUCT_DETAIL_FIELDS = {
    "product_code": "Produto",
    "include_bom": "Incluir estrutura (BOM)",
    "total": "Qtd. de nós de inspeção",
}


@router.get(
    "/summary",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_process_inspection_plans_summary",
        path="/process-inspection-plans/summary",
    ),
)
@require_any_permission(INSPECOES_PROCESSO_READ_PERMISSIONS)
def get_process_inspection_plans_summary_route(
    branch: str | None = BRANCH_QUERY_OPTIONAL(),
):
    branch_error = branch_access_error(branch)
    if branch_error:
        return branch_error

    try:
        use_case = build_get_process_inspection_plans_summary_use_case()
        result = use_case.execute(branch=branch)
        return api_delpi_success(
            result.to_dict(),
            operation_id="get_process_inspection_plans_summary",
            message="Process inspection plans summary loaded successfully.",
            fields=_SUMMARY_FIELDS,
        )
    except ValueError as exc:
        log_error(f"Validation error on process inspection plans summary: {exc}")
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Error loading process inspection plans summary: {exc}")
        return error_response(
            "Internal error loading process inspection plans summary.",
            status_code=500,
        )


@router.get(
    "/orders-without-plan",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_process_inspection_plans_orders_without_plan",
        path="/process-inspection-plans/orders-without-plan",
    ),
)
@require_any_permission(INSPECOES_PROCESSO_READ_PERMISSIONS)
def get_process_inspection_plans_orders_without_plan_route(
    branch: str | None = BRANCH_QUERY_OPTIONAL(),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
):
    branch_error = branch_access_error(branch)
    if branch_error:
        return branch_error

    try:
        use_case = build_list_process_inspection_plans_orders_without_plan_use_case()
        result = use_case.execute(branch=branch, page=page, page_size=page_size)
        return api_delpi_success(
            result.to_dict(),
            operation_id="get_process_inspection_plans_orders_without_plan",
            message="Open orders without inspection plan loaded successfully.",
            fields=_ORDER_FIELDS,
        )
    except ValueError as exc:
        log_error(f"Validation error on orders without plan: {exc}")
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Error loading orders without plan: {exc}")
        return error_response(
            "Internal error loading orders without inspection plan.",
            status_code=500,
        )


@router.get(
    "/products-without-plan",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_process_inspection_plans_products_without_plan",
        path="/process-inspection-plans/products-without-plan",
    ),
)
@require_any_permission(INSPECOES_PROCESSO_READ_PERMISSIONS)
def get_process_inspection_plans_products_without_plan_route(
    branch: str | None = BRANCH_QUERY_OPTIONAL(),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
):
    branch_error = branch_access_error(branch)
    if branch_error:
        return branch_error

    try:
        use_case = build_list_process_inspection_plans_products_without_plan_use_case()
        result = use_case.execute(branch=branch, page=page, page_size=page_size)
        return api_delpi_success(
            result.to_dict(),
            operation_id="get_process_inspection_plans_products_without_plan",
            message="Products without inspection plan loaded successfully.",
            fields=_PRODUCT_WITHOUT_FIELDS,
        )
    except ValueError as exc:
        log_error(f"Validation error on products without plan: {exc}")
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Error loading products without plan: {exc}")
        return error_response(
            "Internal error loading products without inspection plan.",
            status_code=500,
        )


@router.get(
    "/products",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_process_inspection_plans_products",
        path="/process-inspection-plans/products",
    ),
)
@require_any_permission(INSPECOES_PROCESSO_READ_PERMISSIONS)
def get_process_inspection_plans_products_route(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
):
    try:
        use_case = build_list_process_inspection_plans_products_use_case()
        result = use_case.execute(page=page, page_size=page_size)
        return api_delpi_success(
            result.to_dict(),
            operation_id="get_process_inspection_plans_products",
            message="Products with inspection plan loaded successfully.",
            fields=_PRODUCT_WITH_FIELDS,
        )
    except ValueError as exc:
        log_error(f"Validation error on products with plan: {exc}")
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Error loading products with plan: {exc}")
        return error_response(
            "Internal error loading products with inspection plan.",
            status_code=500,
        )


@router.get(
    "/products/{code}",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_process_inspection_plans_product",
        path="/process-inspection-plans/products/{code}",
    ),
)
@require_any_permission(INSPECOES_PROCESSO_READ_PERMISSIONS)
def get_process_inspection_plans_product_route(
    code: str = Path(..., min_length=1, max_length=30),
    include_bom: bool = Query(
        default=False,
        description="Include BOM components when true",
    ),
):
    try:
        use_case = build_get_process_inspection_plans_product_use_case()
        result = use_case.execute(product_code=code, include_bom=include_bom)
        if result is None:
            return not_found_response(
                f"No process inspection plan found for product {code}."
            )
        return api_delpi_success(
            result.to_dict(),
            operation_id="get_process_inspection_plans_product",
            message="Process inspection plan loaded successfully.",
            fields=_PRODUCT_DETAIL_FIELDS,
            sections=[
                {
                    "key": "items",
                    "label": "Nós do plano de inspeção",
                    "shape": "list",
                }
            ],
        )
    except ValueError as exc:
        log_error(f"Validation error on product plan detail: {exc}")
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Error loading product plan detail: {exc}")
        return error_response(
            "Internal error loading process inspection plan.",
            status_code=500,
        )

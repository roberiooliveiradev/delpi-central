from __future__ import annotations

from typing import Optional

from fastapi import APIRouter

from delpi_auth.authorization import require_any_permission

from app.application.dto.supplies.safety_stock_request import peer_branch_for
from app.application.security.api_delpi_permissions import SAFETY_STOCK_READ_PERMISSIONS
from app.application.services.composite_sections_builder import build_composite_sections
from app.composition.supplies_composer import (
    build_get_safety_stock_consumption_analysis_item_details_use_case,
    build_get_safety_stock_consumption_analysis_items_use_case,
    build_get_safety_stock_consumption_analysis_summary_use_case,
    build_get_safety_stock_filters_use_case,
    build_get_safety_stock_item_details_use_case,
    build_get_safety_stock_item_suppliers_use_case,
    build_get_safety_stock_items_use_case,
    build_get_safety_stock_summary_use_case,
    build_get_safety_stock_supplier_price_history_use_case,
)
from app.core.exceptions import DatabaseConnectionError
from app.core.responses import error_response
from app.interface.http.openapi_agent_metadata_builder import OpenApiAgentMetadataBuilder
from app.interface.http.routes.supplies.safety_stock_branch_access import (
    branch_access_error,
    branch_view_allowed,
    list_viewable_branches,
)
from app.interface.http.routes.supplies.safety_stock_route_helpers import (
    ANALYSIS_SORT_BY_QUERY,
    ANALYSIS_STATUS_QUERY,
    BRANCH_QUERY,
    INCLUDE_BLOCKED_QUERY,
    INCLUDE_WITHOUT_SAFETY_STOCK_QUERY,
    PAGE_QUERY,
    PAGE_SIZE_QUERY,
    PRODUCT_GROUP_QUERY,
    SEARCH_QUERY,
    SORT_BY_QUERY,
    SORT_DIRECTION_QUERY,
    STATUS_QUERY,
    SUPPLIER_STORE_QUERY,
    UNIT_QUERY,
    build_consumption_analysis_items_request,
    build_consumption_analysis_query_request,
    build_safety_stock_item_details_request,
    build_safety_stock_items_request,
    build_safety_stock_query_request,
    build_safety_stock_supplier_price_history_request,
    execute_safety_stock_route,
)
from app.interface.http.route_response_helpers import api_delpi_success
from app.utils.logger import log_error

_SAFETY_STOCK_DETAIL_SECTIONS = (
    "open_purchase_orders",
    "open_commitments",
    "stock_projection",
    "monthly_consumption",
    "annual_comparison",
)
_CONSUMPTION_ANALYSIS_DETAIL_SECTIONS = (
    "monthly_consumption",
    "annual_comparison",
    "calculation_memory",
)

router = APIRouter(
    prefix="/supplies/safety-stock",
    tags=["Suprimentos — Estoque de segurança"],
)


@router.get(
    "/filters",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_supplies_safety_stock_filters",
        path="/supplies/safety-stock/filters",
    ),
)
@require_any_permission(SAFETY_STOCK_READ_PERMISSIONS)
def get_safety_stock_filters_route(
    branch: str = BRANCH_QUERY(),
    include_blocked: bool = INCLUDE_BLOCKED_QUERY(),
):
    branch_error = branch_access_error(branch)
    if branch_error:
        return branch_error

    try:
        request = build_safety_stock_query_request(
            branch=branch,
            include_blocked=include_blocked,
        )
    except ValueError as exc:
        log_error(f"Erro de validação ao carregar filtros de estoque de segurança: {exc}")
        return error_response(str(exc), status_code=400)

    try:
        use_case = build_get_safety_stock_filters_use_case()
        result = use_case.execute(request)
        result["authorized_branches"] = list_viewable_branches()

        return api_delpi_success(
            result,
            operation_id="get_supplies_safety_stock_filters",
            message="Filtros de estoque de segurança carregados com sucesso.",
        )
    except Exception as exc:
        log_error(f"Erro ao carregar filtros de estoque de segurança: {exc}")
        return error_response(
            "Erro interno ao carregar filtros de estoque de segurança.",
            status_code=500,
        )


@router.get(
    "/summary",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_supplies_safety_stock_summary",
        path="/supplies/safety-stock/summary",
    ),
)
@require_any_permission(SAFETY_STOCK_READ_PERMISSIONS)
def get_safety_stock_summary_route(
    branch: str = BRANCH_QUERY(),
    include_blocked: bool = INCLUDE_BLOCKED_QUERY(),
    product_group: Optional[str] = PRODUCT_GROUP_QUERY(),
    unit: Optional[str] = UNIT_QUERY(),
    search: Optional[str] = SEARCH_QUERY(),
    status: Optional[str] = STATUS_QUERY(),
    include_without_safety_stock: bool = INCLUDE_WITHOUT_SAFETY_STOCK_QUERY(),
):
    branch_error = branch_access_error(branch)
    if branch_error:
        return branch_error

    try:
        request = build_safety_stock_query_request(
            branch=branch,
            include_blocked=include_blocked,
            product_group=product_group,
            unit=unit,
            search=search,
            status=status,
            include_without_safety_stock=include_without_safety_stock,
        )
    except ValueError as exc:
        log_error(f"Erro de validação ao buscar resumo de estoque de segurança: {exc}")
        return error_response(str(exc), status_code=400)

    return execute_safety_stock_route(
        use_case_builder=build_get_safety_stock_summary_use_case,
        request=request,
        operation_id="get_supplies_safety_stock_summary",
        success_message="Resumo de estoque de segurança carregado com sucesso.",
        error_context="buscar resumo de estoque de segurança",
    )


@router.get(
    "/items",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_supplies_safety_stock_items",
        path="/supplies/safety-stock/items",
    ),
)
@require_any_permission(SAFETY_STOCK_READ_PERMISSIONS)
def get_safety_stock_items_route(
    branch: str = BRANCH_QUERY(),
    page: int = PAGE_QUERY(),
    page_size: int = PAGE_SIZE_QUERY(),
    search: Optional[str] = SEARCH_QUERY(),
    status: Optional[str] = STATUS_QUERY(),
    product_group: Optional[str] = PRODUCT_GROUP_QUERY(),
    unit: Optional[str] = UNIT_QUERY(),
    include_blocked: bool = INCLUDE_BLOCKED_QUERY(),
    include_without_safety_stock: bool = INCLUDE_WITHOUT_SAFETY_STOCK_QUERY(),
    sort_by: str = SORT_BY_QUERY(),
    sort_direction: str = SORT_DIRECTION_QUERY(),
):
    branch_error = branch_access_error(branch)
    if branch_error:
        return branch_error

    try:
        request = build_safety_stock_items_request(
            branch=branch,
            page=page,
            page_size=page_size,
            include_blocked=include_blocked,
            product_group=product_group,
            unit=unit,
            search=search,
            status=status,
            include_without_safety_stock=include_without_safety_stock,
            sort_by=sort_by,
            sort_direction=sort_direction,
        )
    except ValueError as exc:
        log_error(f"Erro de validação ao listar itens de estoque de segurança: {exc}")
        return error_response(str(exc), status_code=400)

    return execute_safety_stock_route(
        use_case_builder=build_get_safety_stock_items_use_case,
        request=request,
        operation_id="get_supplies_safety_stock_items",
        success_message="Itens de estoque de segurança carregados com sucesso.",
        error_context="listar itens de estoque de segurança",
    )


@router.get(
    "/items/{code}/details",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_supplies_safety_stock_item_details",
        path="/supplies/safety-stock/items/{code}/details",
    ),
)
@require_any_permission(SAFETY_STOCK_READ_PERMISSIONS)
def get_safety_stock_item_details_route(
    code: str,
    branch: str = BRANCH_QUERY(),
):
    branch_error = branch_access_error(branch)
    if branch_error:
        return branch_error

    try:
        peer = peer_branch_for(branch)
        request = build_safety_stock_item_details_request(
            branch=branch,
            product_code=code,
            peer_branch=peer if peer and branch_view_allowed(peer) else None,
        )
    except ValueError as exc:
        log_error(f"Erro de validação ao buscar detalhe de estoque de segurança: {exc}")
        return error_response(str(exc), status_code=400)

    try:
        use_case = build_get_safety_stock_item_details_use_case()
        result = use_case.execute(request)
        if result is None:
            return error_response(
                "Matéria-prima não encontrada para a filial informada.",
                status_code=404,
            )
        return api_delpi_success(
            result,
            operation_id="get_supplies_safety_stock_item_details",
            message="Detalhe de estoque de segurança carregado com sucesso.",
            sections=build_composite_sections(
                result,
                section_keys=_SAFETY_STOCK_DETAIL_SECTIONS,
            ),
        )
    except DatabaseConnectionError:
        return error_response(
            "Indisponibilidade temporária do Protheus. Tente novamente em instantes.",
            status_code=503,
        )
    except Exception as exc:
        log_error(f"Erro ao buscar detalhe de estoque de segurança: {exc}")
        return error_response(
            "Erro interno ao buscar detalhe de estoque de segurança.",
            status_code=500,
        )


@router.get(
    "/items/{code}/suppliers",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_supplies_safety_stock_item_suppliers",
        path="/supplies/safety-stock/items/{code}/suppliers",
    ),
)
@require_any_permission(SAFETY_STOCK_READ_PERMISSIONS)
def get_safety_stock_item_suppliers_route(
    code: str,
    branch: str = BRANCH_QUERY(),
):
    branch_error = branch_access_error(branch)
    if branch_error:
        return branch_error

    try:
        request = build_safety_stock_item_details_request(
            branch=branch,
            product_code=code,
        )
    except ValueError as exc:
        log_error(
            f"Erro de validação ao buscar fornecedores vinculados de estoque de segurança: {exc}"
        )
        return error_response(str(exc), status_code=400)

    try:
        use_case = build_get_safety_stock_item_suppliers_use_case()
        result = use_case.execute(request)
        return api_delpi_success(
            result,
            operation_id="get_supplies_safety_stock_item_suppliers",
            message="Fornecedores vinculados carregados com sucesso.",
        )
    except DatabaseConnectionError:
        return error_response(
            "Indisponibilidade temporária do Protheus. Tente novamente em instantes.",
            status_code=503,
        )
    except Exception as exc:
        log_error(f"Erro ao buscar fornecedores vinculados de estoque de segurança: {exc}")
        return error_response(
            "Erro interno ao buscar fornecedores vinculados.",
            status_code=500,
        )


@router.get(
    "/consumption-analysis/summary",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_supplies_safety_stock_consumption_analysis_summary",
        path="/supplies/safety-stock/consumption-analysis/summary",
    ),
)
@require_any_permission(SAFETY_STOCK_READ_PERMISSIONS)
def get_safety_stock_consumption_analysis_summary_route(
    branch: str = BRANCH_QUERY,
    include_blocked: bool = INCLUDE_BLOCKED_QUERY,
    product_group: Optional[str] = PRODUCT_GROUP_QUERY,
    unit: Optional[str] = UNIT_QUERY,
    search: Optional[str] = SEARCH_QUERY,
    analysis_status: Optional[str] = ANALYSIS_STATUS_QUERY,
):
    branch_error = branch_access_error(branch)
    if branch_error:
        return branch_error

    try:
        request = build_consumption_analysis_query_request(
            branch=branch,
            include_blocked=include_blocked,
            product_group=product_group,
            unit=unit,
            search=search,
            analysis_status=analysis_status,
        )
    except ValueError as exc:
        log_error(f"Erro de validação ao buscar resumo da análise de consumo: {exc}")
        return error_response(str(exc), status_code=400)

    return execute_safety_stock_route(
        use_case_builder=build_get_safety_stock_consumption_analysis_summary_use_case,
        request=request,
        operation_id="get_supplies_safety_stock_consumption_analysis_summary",
        success_message="Resumo da análise de consumo carregado com sucesso.",
        error_context="buscar resumo da análise de consumo",
    )


@router.get(
    "/consumption-analysis/items",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_supplies_safety_stock_consumption_analysis_items",
        path="/supplies/safety-stock/consumption-analysis/items",
    ),
)
@require_any_permission(SAFETY_STOCK_READ_PERMISSIONS)
def get_safety_stock_consumption_analysis_items_route(
    branch: str = BRANCH_QUERY,
    page: int = PAGE_QUERY,
    page_size: int = PAGE_SIZE_QUERY,
    search: Optional[str] = SEARCH_QUERY,
    analysis_status: Optional[str] = ANALYSIS_STATUS_QUERY,
    product_group: Optional[str] = PRODUCT_GROUP_QUERY,
    unit: Optional[str] = UNIT_QUERY,
    include_blocked: bool = INCLUDE_BLOCKED_QUERY,
    sort_by: str = ANALYSIS_SORT_BY_QUERY,
    sort_direction: str = SORT_DIRECTION_QUERY,
):
    branch_error = branch_access_error(branch)
    if branch_error:
        return branch_error

    try:
        request = build_consumption_analysis_items_request(
            branch=branch,
            page=page,
            page_size=page_size,
            include_blocked=include_blocked,
            product_group=product_group,
            unit=unit,
            search=search,
            analysis_status=analysis_status,
            sort_by=sort_by,
            sort_direction=sort_direction,
        )
    except ValueError as exc:
        log_error(f"Erro de validação ao listar análise de consumo: {exc}")
        return error_response(str(exc), status_code=400)

    return execute_safety_stock_route(
        use_case_builder=build_get_safety_stock_consumption_analysis_items_use_case,
        request=request,
        operation_id="get_supplies_safety_stock_consumption_analysis_items",
        success_message="Itens da análise de consumo carregados com sucesso.",
        error_context="listar análise de consumo",
    )


@router.get(
    "/consumption-analysis/items/{code}",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_supplies_safety_stock_consumption_analysis_item_details",
        path="/supplies/safety-stock/consumption-analysis/items/{code}",
    ),
)
@require_any_permission(SAFETY_STOCK_READ_PERMISSIONS)
def get_safety_stock_consumption_analysis_item_details_route(
    code: str,
    branch: str = BRANCH_QUERY,
):
    branch_error = branch_access_error(branch)
    if branch_error:
        return branch_error

    try:
        request = build_safety_stock_item_details_request(
            branch=branch,
            product_code=code,
        )
    except ValueError as exc:
        log_error(f"Erro de validação ao buscar detalhe da análise de consumo: {exc}")
        return error_response(str(exc), status_code=400)

    try:
        use_case = build_get_safety_stock_consumption_analysis_item_details_use_case()
        result = use_case.execute(request)
        if result is None:
            return error_response(
                "Produto sem estoque de segurança e movimentos elegíveis no período.",
                status_code=404,
            )
        return api_delpi_success(
            result,
            operation_id="get_supplies_safety_stock_consumption_analysis_item_details",
            message="Detalhe da análise de consumo carregado com sucesso.",
            sections=build_composite_sections(
                result,
                section_keys=_CONSUMPTION_ANALYSIS_DETAIL_SECTIONS,
            ),
        )
    except DatabaseConnectionError:
        return error_response(
            "Indisponibilidade temporária do Protheus. Tente novamente em instantes.",
            status_code=503,
        )
    except Exception as exc:
        log_error(f"Erro ao buscar detalhe da análise de consumo: {exc}")
        return error_response(
            "Erro interno ao buscar detalhe da análise de consumo.",
            status_code=500,
        )


@router.get(
    "/items/{code}/suppliers/{supplier_code}/purchase-price-history",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_supplies_safety_stock_supplier_purchase_price_history",
        path=(
            "/supplies/safety-stock/items/{code}/suppliers/"
            "{supplier_code}/purchase-price-history"
        ),
    ),
)
@require_any_permission(SAFETY_STOCK_READ_PERMISSIONS)
def get_safety_stock_supplier_purchase_price_history_route(
    code: str,
    supplier_code: str,
    branch: str = BRANCH_QUERY(),
    supplier_store: str = SUPPLIER_STORE_QUERY(),
):
    branch_error = branch_access_error(branch)
    if branch_error:
        return branch_error

    try:
        request = build_safety_stock_supplier_price_history_request(
            branch=branch,
            product_code=code,
            supplier_code=supplier_code,
            supplier_store=supplier_store,
        )
    except ValueError as exc:
        log_error(
            "Erro de validação ao buscar histórico de preço por fornecedor "
            f"de estoque de segurança: {exc}"
        )
        return error_response(str(exc), status_code=400)

    try:
        use_case = build_get_safety_stock_supplier_price_history_use_case()
        result = use_case.execute(request)
        return api_delpi_success(
            result,
            operation_id="get_supplies_safety_stock_supplier_purchase_price_history",
            message="Histórico de preço do fornecedor carregado com sucesso.",
        )
    except DatabaseConnectionError:
        return error_response(
            "Indisponibilidade temporária do Protheus. Tente novamente em instantes.",
            status_code=503,
        )
    except Exception as exc:
        log_error(
            f"Erro ao buscar histórico de preço por fornecedor de estoque de segurança: {exc}"
        )
        return error_response(
            "Erro interno ao buscar histórico de preço do fornecedor.",
            status_code=500,
        )

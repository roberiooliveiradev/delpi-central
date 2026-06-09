# app/interface/http/routes/product_routes.py
from fastapi import APIRouter, Query, Request
from fastapi.responses import StreamingResponse, JSONResponse

from typing import Optional
from delpi_auth.authorization import require_permission

from app.application.security.api_delpi_permissions import API_DELPI_ACCESS
from app.core.responses import error_response, not_found_response
from app.utils.logger import log_error

from app.application.dto.product.list_products_requests import ListProductsRequest
from app.application.dto.product.list_product_structured_request import ListProductStructureRequest
from app.application.dto.product.list_product_parents_request import ListProductParentsRequest
from app.application.dto.product.export_structure_excel_request import ExportStructureExcelRequest
from app.application.dto.product.list_product_suppliers_request import ListProductSuppliersRequest
from app.application.dto.product.list_product_customers_request import ListProductCustomersRequest
from app.application.dto.product.list_product_inspection_request import ListProductInspectionRequest
from app.application.dto.product.list_product_guide_request import ListProductGuideRequest
from app.application.dto.product.list_product_internal_movements_request import ListProductInternalMovementsRequest
from app.application.dto.product.list_product_stock_request import ListProductStockRequest
from app.application.dto.product.list_product_inbound_invoice_items_request import ListProductInboundInvoiceItemsRequest
from app.application.dto.product.list_product_outbound_invoice_items_request import ListProductOutboundInvoiceItemsRequest
from app.application.dto.product.list_product_purchases_request import ListProductPurchasesRequest
from app.application.dto.product.get_product_sales_summary_request import GetProductSalesSummaryRequest
from app.application.dto.product.get_product_sales_open_orders_request import GetProductSalesOpenOrdersRequest
from app.application.dto.product.get_product_sales_billing_request import GetProductSalesBillingRequest
from app.application.dto.product.get_product_pricing_request import GetProductPricingRequest
from app.application.dto.product.product_playbook_request import ProductPlaybookRequest
from app.application.dto.product.product_cost_impact_request import ProductCostImpactRequest
from app.application.dto.product.product_raw_material_price_request import (
    ProductRawMaterialPriceRequest,
)
from app.application.dto.product.product_analyser_request import ProductAnalyserRequest

from app.interface.http.openapi_agent_metadata import (
    PRODUCT_ANALYSER,
    PRODUCT_CUSTOMERS,
    PRODUCT_DETAIL,
    PRODUCT_GUIDE,
    PRODUCT_INBOUND_INVOICE_ITEMS,
    PRODUCT_INSPECTION,
    PRODUCT_INTERNAL_MOVEMENTS,
    PRODUCT_OUTBOUND_INVOICE_ITEMS,
    PRODUCT_PARENTS,
    PRODUCT_PRICING,
    PRODUCT_PURCHASES,
    PRODUCT_SALES_BILLING,
    PRODUCT_SALES_OPEN_ORDERS,
    PRODUCT_SALES_SUMMARY,
    PRODUCT_SEARCH,
    PRODUCT_STOCK,
    PRODUCT_STRUCTURE,
    PRODUCT_STRUCTURE_EXCLUSIVITY,
    PRODUCT_PRODUCTION_STATUS,
    PRODUCT_SHIPPING_STATUS,
    PRODUCT_FACTORY_STATUS,
    PRODUCT_COST_IMPACT_SIMULATION,
    PRODUCT_LAST_PURCHASE,
    PRODUCT_PURCHASE_PRICE_HISTORY,
    PRODUCT_PURCHASE_BUDGET_HISTORY,
    PRODUCT_RAW_MATERIAL_PRICE_INTELLIGENCE,
    PRODUCT_SUMMARY,
    PRODUCT_SUPPLIERS,
)
from app.interface.http.routes.product_response_helpers import (
    STOCK_FIELD_LABELS,
    product_success,
)
from app.interface.http.schemas.api_delpi_responses import (
    CompositeAnalysisResponse,
    HierarchyResponse,
    PagedListStockResponse,
    PlaybookReportResponse,
    ProductDetailResponse,
    ProductSearchResponse,
    ProductSnapshotResponse,
)
from app.interface.http.schemas.openapi_examples import (
    PRODUCT_ANALYSER_EXAMPLE,
    PRODUCT_DETAIL_EXAMPLE,
    PRODUCT_FACTORY_STATUS_EXAMPLE,
    PRODUCT_SEARCH_EXAMPLE,
    PRODUCT_STOCK_EXAMPLE,
    PRODUCT_STRUCTURE_EXAMPLE,
    PRODUCT_SUMMARY_EXAMPLE,
)
from app.interface.http.schemas.openapi_route_helpers import openapi_example_response
from app.application.services.composite_sections_builder import build_composite_sections
from app.application.services.product.protheus_field_normalizer import (
    narrow_product_fields,
    normalize_playbook_payload,
    normalize_stock_payload,
)
from app.composition.product_composer import (
    build_search_products_use_case,
    build_list_structure_use_case,
    build_export_structure_excel_use_case,
    build_list_parents_use_case,
    build_list_product_suppliers_use_case,
    build_list_customers_use_case,
    build_list_product_inspection_use_case,
    build_list_product_guide_use_case,
    build_list_product_internal_movements_use_case,
    build_list_product_stock_use_case,
    build_list_product_inbound_invoice_items_use_case,
    build_list_product_outbound_invoice_items_use_case,
    build_list_product_purchases,
    build_get_product_sales_summary,
    build_get_product_sales_open_orders,
    build_get_product_sales_billing,
    build_get_product_pricing,
    build_product_analyser_use_case,
    build_get_product_structure_exclusivity_use_case,
    build_get_product_production_status_use_case,
    build_get_product_shipping_status_use_case,
    build_get_product_factory_status_use_case,
    build_get_product_cost_impact_simulation_use_case,
    build_get_product_last_purchase_use_case,
    build_get_product_purchase_price_history_use_case,
    build_get_product_purchase_budget_history_use_case,
    build_get_product_raw_material_price_intelligence_use_case,
    )



router = APIRouter()

@router.get(
    "/search",
    **PRODUCT_SEARCH,
    response_model=ProductSearchResponse,
    openapi_extra=openapi_example_response(PRODUCT_SEARCH_EXAMPLE),
)
@require_permission(API_DELPI_ACCESS)
def search_products_route(
    code: Optional[str] = Query(None),
    group_code: Optional[str] = Query(None),
    description: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    sort: Optional[str]=Query(None),
    direction: Optional[str] = Query(None)
):
    try:

        dto = ListProductsRequest(
            code=code,
            group_code=group_code,
            description=description,
            page=page,
            page_size=page_size,
            sort=sort,
            direction=direction,
        )

        use_case = build_search_products_use_case()

        result = use_case.execute(dto)

        return product_success(
            result.to_dict(),
            operation_id="search_products",
            entity="product_search",
            shape="paged_list",
        )

    except Exception as e:
        log_error(f"Erro ao buscar produtos: {e}")
        return error_response(str(e))

@router.get(
    "/{code}",
    **PRODUCT_DETAIL,
    response_model=ProductDetailResponse,
    openapi_extra=openapi_example_response(PRODUCT_DETAIL_EXAMPLE),
)
@require_permission(API_DELPI_ACCESS)
def get_product_detail(
    code: str,
    view: str = Query(
        "full",
        description="full=cadastro completo; summary=subconjunto (~15 campos)",
    ),
    legacy: bool = Query(
        False,
        description="Reservado para campos normalizados futuros no cadastro",
    ),
):
    try:
        dto = ListProductsRequest(code=code, page=1, page_size=1)
        use_case = build_search_products_use_case()
        result = use_case.execute(dto)

        if not result.items:
            return not_found_response(
                f"Produto {code} não encontrado",
                code="PRODUCT_NOT_FOUND",
            )

        product = result.items[0]
        product_dict = product.to_dict() if hasattr(product, "to_dict") else vars(product)
        product_dict = narrow_product_fields(product_dict, view=view)

        return product_success(
            {"product": product_dict},
            operation_id="get_product_detail",
            entity="product",
            shape="product_snapshot",
            code=code,
        )

    except Exception as e:
        log_error(f"Erro ao buscar produto {code}: {e}")
        return error_response(str(e))


@router.get(
    "/{code}/summary",
    **PRODUCT_SUMMARY,
    response_model=ProductSnapshotResponse,
    openapi_extra=openapi_example_response(PRODUCT_SUMMARY_EXAMPLE),
)
@require_permission(API_DELPI_ACCESS)
def get_product_summary(code: str):
    try:
        product_dto = ListProductsRequest(code=code, page=1, page_size=1)
        product_uc = build_search_products_use_case()
        product_result = product_uc.execute(product_dto)

        if not product_result.items:
            return not_found_response(
                f"Produto {code} não encontrado",
                code="PRODUCT_NOT_FOUND",
            )

        product = product_result.items[0]
        product_dict = product.to_dict() if hasattr(product, "to_dict") else vars(product)

        stock_items = []
        try:
            stock_dto = ListProductStockRequest(code=code)
            stock_uc = build_list_product_stock_use_case()
            stock_result = stock_uc.execute(stock_dto)
            stock_items = [s.to_dict() if hasattr(s, "to_dict") else vars(s) for s in (stock_result.items or [])][:10]
        except Exception:
            pass

        prices = []
        try:
            pricing_dto = GetProductPricingRequest(code=code)
            from app.composition.product_composer import build_get_product_pricing
            pricing_uc = build_get_product_pricing()
            pricing_result = pricing_uc.execute(pricing_dto)
            if hasattr(pricing_result, "to_dict"):
                pr_data = pricing_result.to_dict()
                prices = pr_data.get("prices") or []
            elif hasattr(pricing_result, "prices"):
                prices = [p.to_dict() if hasattr(p, "to_dict") else vars(p) for p in (pricing_result.prices or [])]
        except Exception:
            pass

        return product_success(
            {
                "product": product_dict,
                "stock": stock_items,
                "prices": prices,
            },
            operation_id="get_product_summary",
            entity="product",
            shape="product_snapshot",
            code=code,
            message="Resumo do produto carregado com sucesso.",
        )

    except Exception as e:
        log_error(f"Erro ao gerar resumo do produto {code}: {e}")
        return error_response(str(e))


@router.get(
    "/{code}/structure",
    **PRODUCT_STRUCTURE,
    response_model=HierarchyResponse,
    openapi_extra=openapi_example_response(PRODUCT_STRUCTURE_EXAMPLE),
)
@require_permission(API_DELPI_ACCESS)
def get_structure(
    code: str,
    max_depth: Optional[int] = None,
    page: Optional[int] = None,
    page_size: Optional[int] = None
):

    try:

        dto = ListProductStructureRequest(
            code=code,
            max_depth=max_depth,
            page=page,
            page_size=page_size
        )

        use_case = build_list_structure_use_case()

        result = use_case.execute(dto)

        return product_success(
            result,
            operation_id="get_product_structure",
            entity="product_structure",
            shape="hierarchy",
            code=code,
            message="Estrutura do produto carregada com sucesso.",
        )

    except Exception as e:
        log_error(f"Erro ao buscar estrutura do produto {code}: {e}")
        return error_response(str(e))


@router.get("/{code}/structure/exclusivity", **PRODUCT_STRUCTURE_EXCLUSIVITY)
@require_permission(API_DELPI_ACCESS)
def get_structure_exclusivity(
    code: str,
    max_depth: Optional[int] = Query(default=None, ge=1, le=100),
    legacy: bool = Query(False, description="Devolve SIM/NAO em vez de booleanos"),
):
    try:
        dto = ProductPlaybookRequest(code=code, max_depth=max_depth, legacy=legacy)
        use_case = build_get_product_structure_exclusivity_use_case()
        result = normalize_playbook_payload(use_case.execute(dto), legacy=legacy)

        return product_success(
            result,
            operation_id=PRODUCT_STRUCTURE_EXCLUSIVITY["operation_id"],
            entity="product_structure_exclusivity",
            shape="playbook_report",
            code=code,
            message="Estrutura com exclusividade de MPs carregada com sucesso.",
        )

    except ValueError as exc:
        log_error(f"Erro de validação na estrutura com exclusividade de {code}: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as e:
        log_error(f"Erro ao buscar estrutura com exclusividade de {code}: {e}")
        return error_response(str(e), status_code=500)


@router.get("/{code}/production-status", **PRODUCT_PRODUCTION_STATUS)
@require_permission(API_DELPI_ACCESS)
def get_production_status(
    code: str,
    reference_date: Optional[str] = Query(default=None),
    max_depth: Optional[int] = Query(default=None, ge=1, le=100),
    branch: Optional[str] = Query(default=None, min_length=2, max_length=2),
    legacy: bool = Query(False, description="Devolve SIM/NAO em vez de booleanos"),
):
    try:
        dto = ProductPlaybookRequest(
            code=code,
            reference_date=reference_date,
            max_depth=max_depth,
            branch=branch,
            legacy=legacy,
        )
        use_case = build_get_product_production_status_use_case()
        result = normalize_playbook_payload(use_case.execute(dto), legacy=legacy)

        return product_success(
            result,
            operation_id=PRODUCT_PRODUCTION_STATUS["operation_id"],
            entity="product_production_status",
            shape="playbook_report",
            code=code,
            message="Situação produtiva do produto carregada com sucesso.",
        )

    except ValueError as exc:
        log_error(f"Erro de validação na situação produtiva de {code}: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as e:
        log_error(f"Erro ao buscar situação produtiva de {code}: {e}")
        return error_response(str(e), status_code=500)


@router.get("/{code}/shipping-status", **PRODUCT_SHIPPING_STATUS)
@require_permission(API_DELPI_ACCESS)
def get_shipping_status(
    code: str,
    reference_date: Optional[str] = Query(default=None),
    date_start: Optional[str] = Query(default=None),
    date_end: Optional[str] = Query(default=None),
    branch: Optional[str] = Query(default=None, min_length=2, max_length=2),
    legacy: bool = Query(False, description="Omite datas ISO normalizadas"),
):
    try:
        dto = ProductPlaybookRequest(
            code=code,
            reference_date=reference_date,
            date_start=date_start,
            date_end=date_end,
            branch=branch,
            legacy=legacy,
        )
        use_case = build_get_product_shipping_status_use_case()
        result = normalize_playbook_payload(use_case.execute(dto), legacy=legacy)

        return product_success(
            result,
            operation_id=PRODUCT_SHIPPING_STATUS["operation_id"],
            entity="product_shipping_status",
            shape="playbook_report",
            code=code,
            message="Status de expedição do produto carregado com sucesso.",
        )

    except ValueError as exc:
        log_error(f"Erro de validação no status de expedição de {code}: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as e:
        log_error(f"Erro ao buscar status de expedição de {code}: {e}")
        return error_response(str(e), status_code=500)


@router.get(
    "/{code}/factory-status",
    **PRODUCT_FACTORY_STATUS,
    response_model=PlaybookReportResponse,
    openapi_extra=openapi_example_response(PRODUCT_FACTORY_STATUS_EXAMPLE),
)
@require_permission(API_DELPI_ACCESS)
def get_factory_status(
    code: str,
    reference_date: Optional[str] = Query(default=None),
    date_start: Optional[str] = Query(default=None),
    date_end: Optional[str] = Query(default=None),
    max_depth: Optional[int] = Query(default=None, ge=1, le=100),
    branch: Optional[str] = Query(default=None, min_length=2, max_length=2),
    legacy: bool = Query(False, description="Devolve SIM/NAO em vez de booleanos"),
):
    try:
        dto = ProductPlaybookRequest(
            code=code,
            reference_date=reference_date,
            date_start=date_start,
            date_end=date_end,
            max_depth=max_depth,
            branch=branch,
            legacy=legacy,
        )
        use_case = build_get_product_factory_status_use_case()
        result = normalize_playbook_payload(use_case.execute(dto), legacy=legacy)

        return product_success(
            result,
            operation_id="get_product_factory_status",
            entity="product_factory_status",
            shape="composite_analysis",
            code=code,
            sections=build_composite_sections(
                result,
                view="full",
                section_keys=(
                    "structure",
                    "raw_material_stock",
                    "production",
                    "shipping",
                ),
            ),
            message="Status fabril completo do produto carregado com sucesso.",
        )

    except ValueError as exc:
        log_error(f"Erro de validação no status fabril de {code}: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as e:
        log_error(f"Erro ao buscar status fabril de {code}: {e}")
        return error_response(str(e), status_code=500)


@router.get(
    "/{code}/cost-impact-simulation",
    **PRODUCT_COST_IMPACT_SIMULATION,
    response_model=CompositeAnalysisResponse,
)
@require_permission(API_DELPI_ACCESS)
def get_cost_impact_simulation(
    code: str,
    max_depth: Optional[int] = Query(default=None, ge=1, le=100),
    price_source: str = Query(
        default="standard_cost",
        description="Fonte de custo unitário: standard_cost (B1_CUSTD) ou last_purchase (B1_UPRC)",
    ),
    adjustment_percent: float = Query(
        default=0.0,
        ge=-100,
        le=1000,
        description="Reajuste percentual simulado aplicado a todas as MPs",
    ),
    top_n: Optional[int] = Query(
        default=None,
        ge=1,
        le=200,
        description="Limita o ranking retornado às N MPs de maior impacto",
    ),
):
    try:
        if price_source not in ("standard_cost", "last_purchase"):
            raise ValueError(
                "price_source inválido. Use standard_cost ou last_purchase."
            )

        dto = ProductCostImpactRequest(
            code=code,
            max_depth=max_depth,
            price_source=price_source,
            adjustment_percent=adjustment_percent,
            top_n=top_n,
        )
        use_case = build_get_product_cost_impact_simulation_use_case()
        result = use_case.execute(dto)

        if not result.get("product"):
            return not_found_response(
                f"Produto {code} não encontrado.",
                code="PRODUCT_NOT_FOUND",
            )

        return product_success(
            result,
            operation_id="get_product_cost_impact_simulation",
            entity="product_cost_impact_simulation",
            shape="composite_analysis",
            code=code,
            sections=build_composite_sections(
                result,
                view="full",
                section_keys=("materials", "summary", "simulation"),
            ),
            message="Simulação de impacto de custos carregada com sucesso.",
        )

    except ValueError as exc:
        log_error(f"Erro de validação na simulação de custo de {code}: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as e:
        log_error(f"Erro ao simular impacto de custo de {code}: {e}")
        return error_response(str(e), status_code=500)


def _raw_material_price_dto(
    code: str,
    date_start: Optional[str],
    date_end: Optional[str],
    branch: Optional[str],
    history_limit: Optional[int],
) -> ProductRawMaterialPriceRequest:
    return ProductRawMaterialPriceRequest(
        code=code,
        date_start=date_start,
        date_end=date_end,
        branch=branch,
        history_limit=history_limit,
    )


@router.get("/{code}/last-purchase", **PRODUCT_LAST_PURCHASE)
@require_permission(API_DELPI_ACCESS)
def get_last_purchase(
    code: str,
    branch: Optional[str] = Query(default=None, min_length=2, max_length=2),
):
    try:
        dto = _raw_material_price_dto(code, None, None, branch, None)
        result = build_get_product_last_purchase_use_case().execute(dto)

        if not result.get("product"):
            return not_found_response(
                f"Produto {code} não encontrado.",
                code="PRODUCT_NOT_FOUND",
            )

        return product_success(
            result,
            operation_id=PRODUCT_LAST_PURCHASE["operation_id"],
            entity="product_last_purchase",
            shape="playbook_report",
            code=code,
            message="Última compra válida carregada com sucesso.",
        )

    except ValueError as exc:
        log_error(f"Erro de validação na última compra de {code}: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as e:
        log_error(f"Erro ao buscar última compra de {code}: {e}")
        return error_response(str(e), status_code=500)


@router.get("/{code}/purchase-price-history", **PRODUCT_PURCHASE_PRICE_HISTORY)
@require_permission(API_DELPI_ACCESS)
def get_purchase_price_history(
    code: str,
    date_start: Optional[str] = Query(default=None),
    date_end: Optional[str] = Query(default=None),
    branch: Optional[str] = Query(default=None, min_length=2, max_length=2),
    history_limit: Optional[int] = Query(default=None, ge=1, le=200),
):
    try:
        dto = _raw_material_price_dto(code, date_start, date_end, branch, history_limit)
        result = build_get_product_purchase_price_history_use_case().execute(dto)

        if not result.get("product"):
            return not_found_response(
                f"Produto {code} não encontrado.",
                code="PRODUCT_NOT_FOUND",
            )

        return product_success(
            result,
            operation_id=PRODUCT_PURCHASE_PRICE_HISTORY["operation_id"],
            entity="product_purchase_price_history",
            shape="playbook_report",
            code=code,
            message="Histórico de preço de compra carregado com sucesso.",
        )

    except ValueError as exc:
        log_error(f"Erro de validação no histórico de preço de {code}: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as e:
        log_error(f"Erro ao buscar histórico de preço de {code}: {e}")
        return error_response(str(e), status_code=500)


@router.get("/{code}/purchase-budget-history", **PRODUCT_PURCHASE_BUDGET_HISTORY)
@require_permission(API_DELPI_ACCESS)
def get_purchase_budget_history(
    code: str,
    date_start: Optional[str] = Query(default=None),
    date_end: Optional[str] = Query(default=None),
    branch: Optional[str] = Query(default=None, min_length=2, max_length=2),
):
    try:
        dto = _raw_material_price_dto(code, date_start, date_end, branch, None)
        result = build_get_product_purchase_budget_history_use_case().execute(dto)

        if not result.get("product"):
            return not_found_response(
                f"Produto {code} não encontrado.",
                code="PRODUCT_NOT_FOUND",
            )

        return product_success(
            result,
            operation_id=PRODUCT_PURCHASE_BUDGET_HISTORY["operation_id"],
            entity="product_purchase_budget_history",
            shape="playbook_report",
            code=code,
            message="Histórico de orçamento de compra carregado com sucesso.",
        )

    except ValueError as exc:
        log_error(f"Erro de validação no histórico de orçamento de {code}: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as e:
        log_error(f"Erro ao buscar histórico de orçamento de {code}: {e}")
        return error_response(str(e), status_code=500)


@router.get(
    "/{code}/raw-material-price-intelligence",
    **PRODUCT_RAW_MATERIAL_PRICE_INTELLIGENCE,
    response_model=CompositeAnalysisResponse,
)
@require_permission(API_DELPI_ACCESS)
def get_raw_material_price_intelligence(
    code: str,
    date_start: Optional[str] = Query(default=None),
    date_end: Optional[str] = Query(default=None),
    branch: Optional[str] = Query(default=None, min_length=2, max_length=2),
    history_limit: Optional[int] = Query(default=None, ge=1, le=200),
):
    try:
        dto = _raw_material_price_dto(code, date_start, date_end, branch, history_limit)
        result = build_get_product_raw_material_price_intelligence_use_case().execute(dto)

        if not result.get("product"):
            return not_found_response(
                f"Produto {code} não encontrado.",
                code="PRODUCT_NOT_FOUND",
            )

        return product_success(
            result,
            operation_id=PRODUCT_RAW_MATERIAL_PRICE_INTELLIGENCE["operation_id"],
            entity="product_raw_material_price_intelligence",
            shape="composite_analysis",
            code=code,
            sections=build_composite_sections(
                result,
                view="full",
                section_keys=(
                    "last_purchase",
                    "budget_history",
                    "price_history",
                    "price_variation",
                ),
            ),
            message="Análise de preço da matéria-prima carregada com sucesso.",
        )

    except ValueError as exc:
        log_error(f"Erro de validação na análise de preço de {code}: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as e:
        log_error(f"Erro ao buscar análise de preço de {code}: {e}")
        return error_response(str(e), status_code=500)


@router.get("/{code}/structure/excel")
@require_permission(API_DELPI_ACCESS)
async def structure_excel_public(
    request: Request,
    code: str,
    format: str = Query("json")
):

    try:

        dto = ExportStructureExcelRequest(code=code)

        use_case = build_export_structure_excel_use_case()

        excel_stream = use_case.execute(dto)

        filename = f"Estrutura_{code}.xlsx"

        if format.lower() == "xlsx":

            return StreamingResponse(
                excel_stream,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}"
                }
            )

        public_url = str(request.url.replace(query="format=xlsx"))

        return JSONResponse(
            content={
                "message": "Arquivo Excel gerado com sucesso!",
                "download_url": public_url
            }
        )

    except Exception as e:

        log_error(f"Erro ao gerar planilha Excel pública de {code}: {e}")

        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )
    
@router.get("/{code}/parents", **PRODUCT_PARENTS)
@require_permission(API_DELPI_ACCESS)
def parents(
    code: str,
    max_depth: Optional[int] = None,
    page: Optional[int] = None,
    page_size: Optional[int] = None
):

    try:

        dto = ListProductParentsRequest(
            code=code,
            max_depth=max_depth,
            page=page,
            page_size=page_size
        )

        use_case = build_list_parents_use_case()

        result = use_case.execute(dto)

        return product_success(
            result,
            operation_id=PRODUCT_PARENTS["operation_id"],
            entity="product_parents",
            shape="hierarchy",
            code=code,
        )

    except Exception as e:

        log_error(f"Erro ao consultar pais do item {code}: {e}")

        return error_response(str(e))

@router.get("/{code}/suppliers", **PRODUCT_SUPPLIERS)
@require_permission(API_DELPI_ACCESS)
def suppliers(
    code: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500)
):

    try:

        dto = ListProductSuppliersRequest(
            code=code,
            page=page,
            page_size=page_size
        )

        use_case = build_list_product_suppliers_use_case()

        result = use_case.execute(dto)

        return product_success(
            result.to_dict(),
            operation_id=PRODUCT_SUPPLIERS["operation_id"],
            entity="product_suppliers",
            shape="paged_list",
            code=code,
        )

    except Exception as e:

        log_error(f"Erro ao consultar fornecedores do item {code}: {e}")

        return error_response(str(e))
    
@router.get("/{code}/customers", **PRODUCT_CUSTOMERS)
@require_permission(API_DELPI_ACCESS)
def customers(
    code: str,
    page: Optional[int] = Query(1, ge=1),
    page_size: Optional[int] = Query(50, ge=1, le=500)
):

    try:

        dto = ListProductCustomersRequest(
            code=code,
            page=page,
            page_size=page_size
        )

        use_case = build_list_customers_use_case()
        print(use_case)
        result = use_case.execute(dto)

        return product_success(
            result.to_dict(),
            operation_id=PRODUCT_CUSTOMERS["operation_id"],
            entity="product_customers",
            shape="paged_list",
            code=code,
        )

    except Exception as e:

        log_error(f"Erro ao consultar clientes do item {code}: {e}")

        return error_response(str(e))
    
@router.get("/{code}/inspection", **PRODUCT_INSPECTION)
@require_permission(API_DELPI_ACCESS)
def inspection(
    code: str,
    page: int | None = Query(None, ge=1),
    page_size: int | None = Query(None, ge=1, le=500),
    max_depth: int | None = Query(None, ge=1, le=15)
):

    try:

        dto = ListProductInspectionRequest(
            code=code,
            page=page,
            page_size=page_size,
            max_depth=max_depth
        )

        use_case = build_list_product_inspection_use_case()

        result = use_case.execute(dto)

        return product_success(
            result,
            operation_id=PRODUCT_INSPECTION["operation_id"],
            entity="product_inspection",
            shape="paged_list",
            code=code,
        )

    except Exception as e:

        log_error(f"Erro ao consultar inspeção do item {code}: {e}")

        return error_response(str(e))
    
@router.get("/{code}/guide", **PRODUCT_GUIDE)
@require_permission(API_DELPI_ACCESS)
def guide(
    code: str,
    branch: Optional[str] = Query(None),
    page: int | None = Query(None, ge=1),
    page_size: int | None = Query(None, ge=1, le=500),
    max_depth: int | None = Query(None, ge=1, le=15)
):

    try:

        dto = ListProductGuideRequest(
            code=code,
            page=page,
            page_size=page_size,
            branch=branch,
            max_depth=max_depth
        )

        use_case = build_list_product_guide_use_case()

        result = use_case.execute(dto)

        return product_success(
            result,
            operation_id=PRODUCT_GUIDE["operation_id"],
            entity="product_guide",
            shape="paged_list",
            code=code,
        )

    except Exception as e:

        log_error(f"Erro ao consultar roteiro do item {code}: {e}")

        return error_response(str(e))

@router.get("/{code}/internal-movements", **PRODUCT_INTERNAL_MOVEMENTS)
@require_permission(API_DELPI_ACCESS)
def internal_movements(
    code: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    date_start: Optional[str] = Query(None),
    date_end: Optional[str] = Query(None),
    branch: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    tm: Optional[str] = Query(None),
    op: Optional[str] = Query(None)
):

    try:

        dto = ListProductInternalMovementsRequest(
            code=code,
            page=page,
            page_size=page_size,
            date_start=date_start,
            date_end=date_end,
            branch=branch,
            location=location,
            tm=tm,
            op=op
        )

        use_case = build_list_product_internal_movements_use_case()

        result = use_case.execute(dto)

        return product_success(
            result,
            operation_id=PRODUCT_INTERNAL_MOVEMENTS["operation_id"],
            entity="product_internal_movements",
            shape="paged_list",
            code=code,
        )

    except Exception as e:

        log_error(f"Erro ao consultar movimentações internas de {code}: {e}")

        return error_response(str(e))
    
@router.get(
    "/{code}/stock",
    **PRODUCT_STOCK,
    response_model=PagedListStockResponse,
    openapi_extra=openapi_example_response(PRODUCT_STOCK_EXAMPLE),
)
@require_permission(API_DELPI_ACCESS)
def stock(
    code: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    branch: Optional[str] = Query(None),
    warehouse: Optional[str] = Query(
        None,
        description="Filtra por armazém (preferido; equivalente a location)",
    ),
    location: Optional[str] = Query(
        None,
        description="Alias legado de warehouse — preferir warehouse",
    ),
    legacy: bool = Query(False, description="Omite alias location nos itens de estoque"),
):

    try:

        dto = ListProductStockRequest(
            code=code,
            page=page,
            page_size=page_size,
            branch=branch,
            location=warehouse or location,
        )

        use_case = build_list_product_stock_use_case()

        result = normalize_stock_payload(use_case.execute(dto), legacy=legacy)

        return product_success(
            result,
            operation_id="get_product_stock",
            entity="product_stock",
            shape="paged_list",
            code=code,
            fields=STOCK_FIELD_LABELS,
            message="Estoque do produto carregado com sucesso.",
        )

    except Exception as e:

        log_error(f"Erro ao consultar estoque do item {code}: {e}")

        return error_response(str(e))
    
@router.get("/{code}/inbound-invoice-items", **PRODUCT_INBOUND_INVOICE_ITEMS)
@require_permission(API_DELPI_ACCESS)
def inbound_invoice_items(
    code: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    issue_date_start: Optional[str] = Query(None),
    issue_date_end: Optional[str] = Query(None),
    supplier: Optional[str] = Query(None),
    branch: Optional[str] = Query(None)
):

    try:

        dto = ListProductInboundInvoiceItemsRequest(
            code=code,
            page=page,
            page_size=page_size,
            issue_date_start=issue_date_start,
            issue_date_end=issue_date_end,
            supplier=supplier,
            branch=branch
        )

        use_case = build_list_product_inbound_invoice_items_use_case()

        result = use_case.execute(dto)

        return product_success(
            result,
            operation_id=PRODUCT_INBOUND_INVOICE_ITEMS["operation_id"],
            entity="product_inbound_invoice_items",
            shape="paged_list",
            code=code,
            message=f"Inbound invoices for {code} fetched successfully.",
        )

    except Exception as e:
        log_error(f"Erro ao consultar NF-es de entrada para {code}: {e}")
        return error_response(f"Unexpected error: {e}")
    
@router.get("/{code}/outbound-invoice-items", **PRODUCT_OUTBOUND_INVOICE_ITEMS)
@require_permission(API_DELPI_ACCESS)
def outbound_invoice_items(
    code: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    issue_date_start: Optional[str] = Query(None),
    issue_date_end: Optional[str] = Query(None),
    customer: Optional[str] = Query(None),
    branch: Optional[str] = Query(None)
):

    try:

        dto = ListProductOutboundInvoiceItemsRequest(
            code=code,
            page=page,
            page_size=page_size,
            issue_date_start=issue_date_start,
            issue_date_end=issue_date_end,
            customer=customer,
            branch=branch
        )

        use_case = build_list_product_outbound_invoice_items_use_case()

        result = use_case.execute(dto)

        return product_success(
            result,
            operation_id=PRODUCT_OUTBOUND_INVOICE_ITEMS["operation_id"],
            entity="product_outbound_invoice_items",
            shape="paged_list",
            code=code,
            message=f"Outbound invoices for {code} fetched successfully.",
        )

    except Exception as e:
        log_error(f"Erro ao consultar NF-es de saída para {code}: {e}")
        return error_response(f"Unexpected error: {e}")
    
@router.get("/{code}/purchases", **PRODUCT_PURCHASES)
@require_permission(API_DELPI_ACCESS)
def purchases(
    code: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500)
):

    try:

        use_case = build_list_product_purchases()

        result = use_case.execute(
            ListProductPurchasesRequest(
                code=code,
                page=page,
                page_size=page_size
            )
        )

        return product_success(
            result,
            operation_id=PRODUCT_PURCHASES["operation_id"],
            entity="product_purchases",
            shape="paged_list",
            code=code,
            message=f"Purchases for {code} fetched successfully (page {page}/{result['total_pages']}).",
        )

    except Exception as e:

        log_error(f"Erro ao consultar compras do item {code}: {e}")

        return error_response(f"Unexpected error: {e}")
    
@router.get("/{code}/sales", **PRODUCT_SALES_SUMMARY)
@require_permission(API_DELPI_ACCESS)
def product_sales_summary(code: str):

    try:

        use_case = build_get_product_sales_summary()

        result = use_case.execute(
            GetProductSalesSummaryRequest(code=code)
        )

        return product_success(
            result,
            operation_id=PRODUCT_SALES_SUMMARY["operation_id"],
            entity="product_sales",
            shape="scalar",
            code=code,
            message=f"Sales summary for product {code} fetched successfully.",
        )

    except Exception as e:

        log_error(f"Erro ao consultar vendas do produto {code}: {e}")

        return error_response(f"Unexpected error: {e}")
    
@router.get("/{code}/sales/open-orders", **PRODUCT_SALES_OPEN_ORDERS)
@require_permission(API_DELPI_ACCESS)
def product_sales_open_orders(code: str):

    try:

        use_case = build_get_product_sales_open_orders()

        result = use_case.execute(
            GetProductSalesOpenOrdersRequest(code=code)
        )

        return product_success(
            result,
            operation_id=PRODUCT_SALES_OPEN_ORDERS["operation_id"],
            entity="product_open_orders",
            shape="paged_list",
            code=code,
            message=f"Open sales orders for product {code} fetched successfully.",
        )

    except Exception as e:

        log_error(f"Erro ao consultar carteira do produto {code}: {e}")

        return error_response(f"Unexpected error: {e}")
    
@router.get("/{code}/sales/billing", **PRODUCT_SALES_BILLING)
@require_permission(API_DELPI_ACCESS)
def product_sales_billing(code: str):

    try:

        use_case = build_get_product_sales_billing()

        result = use_case.execute(
            GetProductSalesBillingRequest(code=code)
        )

        return product_success(
            result,
            operation_id=PRODUCT_SALES_BILLING["operation_id"],
            entity="product_billing",
            shape="scalar",
            code=code,
            message=f"Billing summary for product {code} fetched successfully.",
        )

    except Exception as e:

        log_error(f"Erro ao consultar faturamento do produto {code}: {e}")

        return error_response(f"Unexpected error: {e}")
    
@router.get("/{code}/pricing", **PRODUCT_PRICING)
@require_permission(API_DELPI_ACCESS)
def product_pricing(code: str):

    try:

        use_case = build_get_product_pricing()

        result = use_case.execute(
            GetProductPricingRequest(code=code)
        )

        if isinstance(result, dict) and result.get("success") is False:
            return error_response(
                str(result.get("message") or f"Preços não encontrados para {code}"),
                status_code=404,
                code="PRODUCT_PRICING_NOT_FOUND",
                recoverable=False,
            )

        return product_success(
            result,
            operation_id=PRODUCT_PRICING["operation_id"],
            entity="product_pricing",
            shape="scalar",
            code=code,
            message=f"Preços do produto {code} carregados com sucesso.",
        )

    except Exception as e:

        log_error(f"Erro ao consultar preços do produto {code}: {e}")

        return error_response(f"Unexpected error: {e}")

@router.get(
    "/{code}/analyser",
    **PRODUCT_ANALYSER,
    response_model=CompositeAnalysisResponse,
    openapi_extra=openapi_example_response(PRODUCT_ANALYSER_EXAMPLE),
)
@require_permission(API_DELPI_ACCESS)
def product_analyser(
    code: str,
    view: str = Query(
        "full",
        description="full=dimensões completas; summary=amostra leve (opt-in)",
    ),
):

    try:
        normalized_view = (view or "full").strip().lower()
        if normalized_view not in {"full", "summary"}:
            return error_response(
                "view inválida. Use full ou summary.",
                status_code=400,
                code="INVALID_VIEW",
                recoverable=True,
            )

        dto = ProductAnalyserRequest(code=code, view=normalized_view)

        use_case = build_product_analyser_use_case()

        result = use_case.execute(dto)

        return product_success(
            result,
            operation_id="get_product_analyser",
            entity="product_analyser",
            shape="composite_analysis",
            code=code,
            sections=build_composite_sections(
                result,
                view=normalized_view,
                section_keys=("structure", "guide", "inspection"),
            ),
            message="Analisador do produto carregado com sucesso.",
        )

    except Exception as e:

        log_error(f"Erro ao analisar completamente o produto {code}: {e}")

        return error_response(str(e))
# app/interface/http/routes/product_routes.py
from fastapi import APIRouter, Query, Request
from fastapi.responses import StreamingResponse, JSONResponse

from typing import Optional
from delpi_auth.authorization import require_permission
from app.core.responses import success_response, error_response
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
from app.application.dto.product.product_analyser_request import ProductAnalyserRequest

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
    build_product_analyser_use_case
    )



router = APIRouter()

@router.get("/search")
@require_permission("api-delpi.access")
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

        return success_response(data=result.to_dict())

    except Exception as e:
        log_error(f"Erro ao buscar produtos: {e}")
        return error_response(str(e))

@router.get("{code}/structure")
@require_permission("api-delpi.access")
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

        return success_response(data=result)

    except Exception as e:
        log_error(f"Erro ao buscar estrutura do produto {code}: {e}")
        return error_response(str(e))

@router.get("/{code}/structure/excel")
@require_permission("api-delpi.access")
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
    
@router.get("/{code}/parents")
@require_permission("api-delpi.access")
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

        return success_response(data=result)

    except Exception as e:

        log_error(f"Erro ao consultar pais do item {code}: {e}")

        return error_response(str(e))

@router.get("/{code}/suppliers")
@require_permission("api-delpi.access")
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

        return success_response(data=result.to_dict())

    except Exception as e:

        log_error(f"Erro ao consultar fornecedores do item {code}: {e}")

        return error_response(str(e))
    
@router.get("/{code}/customers")
@require_permission("api-delpi.access")
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

        return success_response(data=result.to_dict())

    except Exception as e:

        log_error(f"Erro ao consultar clientes do item {code}: {e}")

        return error_response(str(e))
    
@router.get("/{code}/inspection")
@require_permission("api-delpi.access")
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

        return success_response(data=result)

    except Exception as e:

        log_error(f"Erro ao consultar inspeção do item {code}: {e}")

        return error_response(str(e))
    
@router.get("/{code}/guide")
@require_permission("api-delpi.access")
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

        return success_response(data=result)

    except Exception as e:

        log_error(f"Erro ao consultar roteiro do item {code}: {e}")

        return error_response(str(e))

@router.get("/{code}/internal-movements")
@require_permission("api-delpi.access")
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

        return success_response(data=result)

    except Exception as e:

        log_error(f"Erro ao consultar movimentações internas de {code}: {e}")

        return error_response(str(e))
    
@router.get("/{code}/stock")
@require_permission("api-delpi.access")
def stock(
    code: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    branch: Optional[str] = Query(None),
    location: Optional[str] = Query(None)
):

    try:

        dto = ListProductStockRequest(
            code=code,
            page=page,
            page_size=page_size,
            branch=branch,
            location=location
        )

        use_case = build_list_product_stock_use_case()

        result = use_case.execute(dto)

        return success_response(data=result)

    except Exception as e:

        log_error(f"Erro ao consultar estoque do item {code}: {e}")

        return error_response(str(e))
    
@router.get("/{code}/inbound-invoice-items")
@require_permission("api-delpi.access")
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

        return success_response(
            data=result,
            message=f"Inbound invoices for {code} fetched successfully."
        )

    except Exception as e:
        log_error(f"Erro ao consultar NF-es de entrada para {code}: {e}")
        return error_response(f"Unexpected error: {e}")
    
@router.get("/{code}/outbound-invoice-items")
@require_permission("api-delpi.access")
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

        return success_response(
            data=result,
            message=f"Outbound invoices for {code} fetched successfully."
        )

    except Exception as e:
        log_error(f"Erro ao consultar NF-es de saída para {code}: {e}")
        return error_response(f"Unexpected error: {e}")
    
@router.get(
    "/{code}/purchases",
    summary="Purchase history for product"
)
@require_permission("api-delpi.access")
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

        return success_response(
            data=result,
            message=f"Purchases for {code} fetched successfully (page {page}/{result['total_pages']})."
        )

    except Exception as e:

        log_error(f"Erro ao consultar compras do item {code}: {e}")

        return error_response(f"Unexpected error: {e}")
    
@router.get(
    "/{code}/sales",
    summary="Product sales summary"
)
@require_permission("api-delpi.access")
def product_sales_summary(code: str):

    try:

        use_case = build_get_product_sales_summary()

        result = use_case.execute(
            GetProductSalesSummaryRequest(code=code)
        )

        return success_response(
            data=result,
            message=f"Sales summary for product {code} fetched successfully."
        )

    except Exception as e:

        log_error(f"Erro ao consultar vendas do produto {code}: {e}")

        return error_response(f"Unexpected error: {e}")
    
@router.get(
    "/{code}/sales/open-orders",
    summary="Open sales orders portfolio"
)
@require_permission("api-delpi.access")
def product_sales_open_orders(code: str):

    try:

        use_case = build_get_product_sales_open_orders()

        result = use_case.execute(
            GetProductSalesOpenOrdersRequest(code=code)
        )

        return success_response(
            data=result,
            message=f"Open sales orders for product {code} fetched successfully."
        )

    except Exception as e:

        log_error(f"Erro ao consultar carteira do produto {code}: {e}")

        return error_response(f"Unexpected error: {e}")
    
@router.get(
    "/{code}/sales/billing",
    summary="Product billing summary"
)
@require_permission("api-delpi.access")
def product_sales_billing(code: str):

    try:

        use_case = build_get_product_sales_billing()

        result = use_case.execute(
            GetProductSalesBillingRequest(code=code)
        )

        return success_response(
            data=result,
            message=f"Billing summary for product {code} fetched successfully."
        )

    except Exception as e:

        log_error(f"Erro ao consultar faturamento do produto {code}: {e}")

        return error_response(f"Unexpected error: {e}")
    
@router.get(
    "/{code}/pricing",
    summary="Product commercial pricing"
)
@require_permission("api-delpi.access")
def product_pricing(code: str):

    try:

        use_case = build_get_product_pricing()

        result = use_case.execute(
            GetProductPricingRequest(code=code)
        )

        return success_response(
            data=result,
            message=f"Product pricing for {code} fetched successfully."
        )

    except Exception as e:

        log_error(f"Erro ao consultar preços do produto {code}: {e}")

        return error_response(f"Unexpected error: {e}")

@router.get("/{code}/analyser")
@require_permission("api-delpi.access")
def product_analyser(code: str):

    try:

        dto = ProductAnalyserRequest(code=code)

        use_case = build_product_analyser_use_case()

        result = use_case.execute(dto)

        return success_response(data=result)

    except Exception as e:

        log_error(f"Erro ao analisar completamente o produto {code}: {e}")

        return error_response(str(e))
# app/interface/http/routes/sale_routes.py

from fastapi import APIRouter, Query, Request
from fastapi.responses import StreamingResponse, JSONResponse

from typing import Optional
from delpi_auth.authorization import require_permission
from app.core.responses import success_response, error_response
from app.utils.logger import log_error

from app.application.dto.sale_order.list_sale_order_request import ListSaleOrderRequest
from app.composition.sale_composer import (
    build_list_sale_order_use_case,
)
from app.interface.http.openapi_agent_metadata import SALE_ORDERS_LIST


router = APIRouter()

@router.get("/", **SALE_ORDERS_LIST)
@require_permission("api-delpi.access")
def list_sale_order_route(
    date_start: Optional[str] = None,
    date_end: Optional[str] = None,
    page: int = Query(None, ge=1),
    page_size: int = Query(None, ge=1),
):
    try:

        dto = ListSaleOrderRequest(
            date_start=date_start,
            date_end=date_end,
            page=page,
            page_size=page_size
        )

        use_case = build_list_sale_order_use_case()

        result = use_case.execute(dto)

        return success_response(data=result.to_dict())

    except Exception as e:
        log_error(f"Erro ao buscar ordens de venda: {e}")
        return error_response(str(e))

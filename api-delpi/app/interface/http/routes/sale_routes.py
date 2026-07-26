# app/interface/http/routes/sale_routes.py

from fastapi import APIRouter, Query, Request
from fastapi.responses import StreamingResponse, JSONResponse

from typing import Optional
from delpi_auth.authorization import require_permission

from app.application.security.api_delpi_permissions import API_DELPI_ACCESS
from app.core.responses import error_response
from app.interface.http.period_query_params import (
    END_DATE_QUERY,
    LEGACY_DATE_END_QUERY,
    LEGACY_DATE_START_QUERY,
    START_DATE_QUERY,
    resolve_period_dates,
)
from app.interface.http.route_response_helpers import api_delpi_success
from app.utils.logger import log_error

from app.application.dto.sale_order.list_sale_order_request import ListSaleOrderRequest
from app.composition.sale_composer import (
    build_list_sale_order_use_case,
)
from app.interface.http.openapi_agent_metadata import SALE_ORDERS_LIST


router = APIRouter()

@router.get("/", **SALE_ORDERS_LIST)
@require_permission(API_DELPI_ACCESS)
def list_sale_order_route(
    start_date: Optional[str] = START_DATE_QUERY(),
    end_date: Optional[str] = END_DATE_QUERY(),
    date_start: Optional[str] = LEGACY_DATE_START_QUERY(),
    date_end: Optional[str] = LEGACY_DATE_END_QUERY(),
    page: int = Query(None, ge=1),
    page_size: int = Query(None, ge=1),
):
    start_date, end_date = resolve_period_dates(
        start_date=start_date,
        end_date=end_date,
        date_start=date_start,
        date_end=date_end,
    )
    try:

        dto = ListSaleOrderRequest(
            date_start=start_date,
            date_end=end_date,
            page=page,
            page_size=page_size
        )

        use_case = build_list_sale_order_use_case()

        result = use_case.execute(dto)

        return api_delpi_success(
            result.to_dict(),
            operation_id=SALE_ORDERS_LIST["operation_id"],
        )

    except Exception as e:
        log_error(f"Erro ao buscar ordens de venda: {e}")
        return error_response(str(e))

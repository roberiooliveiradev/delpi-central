from typing import Optional

from fastapi import APIRouter, Query
from delpi_auth.authorization import require_permission

from app.application.dto.production.production_operational_request import (
    ProductionOperationalRequest,
)
from app.application.security.api_delpi_permissions import API_DELPI_ACCESS
from app.composition.production_operational_composer import (
    build_get_purchases_top_products_use_case,
)
from app.core.responses import error_response
from app.interface.http.openapi_agent_metadata import PURCHASES_TOP_PRODUCTS
from app.interface.http.period_query_params import (
    END_DATE_QUERY,
    LEGACY_DATE_END_QUERY,
    LEGACY_DATE_START_QUERY,
    START_DATE_QUERY,
    resolve_period_dates,
)
from app.interface.http.route_response_helpers import api_delpi_success
from app.utils.logger import log_error
from app.interface.http.query_param_enums import (
    BRANCH_QUERY_OPTIONAL,
)

router = APIRouter(prefix="/purchases", tags=["Compras operacionais"])


@router.get("/top-products", **PURCHASES_TOP_PRODUCTS)
@require_permission(API_DELPI_ACCESS)
def get_top_products(
    start_date: Optional[str] = START_DATE_QUERY(),
    end_date: Optional[str] = END_DATE_QUERY(),
    date_start: Optional[str] = LEGACY_DATE_START_QUERY(),
    date_end: Optional[str] = LEGACY_DATE_END_QUERY(),
    branch: Optional[str] = BRANCH_QUERY_OPTIONAL(),
    limit: Optional[int] = Query(default=None, ge=1, le=200),
):
    start_date, end_date = resolve_period_dates(
        start_date=start_date,
        end_date=end_date,
        date_start=date_start,
        date_end=date_end,
    )
    try:
        dto = ProductionOperationalRequest(
            date_start=start_date,
            date_end=end_date,
            branch=branch,
            limit=limit,
        )
        result = build_get_purchases_top_products_use_case().execute(dto)
        return api_delpi_success(
            result,
            operation_id=PURCHASES_TOP_PRODUCTS["operation_id"],
            message="Produtos mais comprados consultados com sucesso.",
        )
    except ValueError as exc:
        log_error(f"Erro de validação em purchases/top-products: {exc}")
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro em purchases/top-products: {exc}")
        return error_response(str(exc), status_code=500)

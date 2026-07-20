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
from app.interface.http.route_response_helpers import api_delpi_success
from app.utils.logger import log_error
from app.interface.http.query_param_enums import (
    BRANCH_QUERY_OPTIONAL,
)

router = APIRouter(prefix="/purchases", tags=["Compras operacionais"])


@router.get("/top-products", **PURCHASES_TOP_PRODUCTS)
@require_permission(API_DELPI_ACCESS)
def get_top_products(
    date_start: Optional[str] = Query(default=None),
    date_end: Optional[str] = Query(default=None),
    branch: Optional[str] = BRANCH_QUERY_OPTIONAL,
    limit: Optional[int] = Query(default=None, ge=1, le=200),
):
    try:
        dto = ProductionOperationalRequest(
            date_start=date_start,
            date_end=date_end,
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

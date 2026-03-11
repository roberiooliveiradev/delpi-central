# app/interface/http/routes/product_routes.py
from fastapi import APIRouter, Query
from typing import Optional
from app.application.dto.list_products_requests import ListProductsRequest
from app.application.dto.list_product_structured_request import ListProductStructureRequest

from app.core.responses import success_response, error_response
from app.utils.logger import log_error
from app.composition.product_composer import (
    build_search_products_use_case,
    build_list_structure_use_case,
    )
from delpi_auth.authorization import require_permission

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

@router.get("/structure/{code}")
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
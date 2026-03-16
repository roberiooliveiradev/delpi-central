# app/interface/http/routes/lmp_routes.py

from fastapi import APIRouter, Query, Request
from fastapi.responses import StreamingResponse, JSONResponse

from typing import Optional
from delpi_auth.authorization import require_permission
from app.core.responses import success_response, error_response
from app.utils.logger import log_error

from app.application.dto.lmp.list_lmp_request import ListLMPRequest
from app.application.dto.lmp.get_lmp_request import GetLMPRequest
from app.composition.lmp_composer import (
    build_list_lmp_use_case,
    build_get_lmp_use_case,
    )


router = APIRouter()

@router.get("/")
@require_permission("api-delpi.access")
def list_lmps_route(
    date_start: Optional[str] = None,
    date_end: Optional[str] = None,
    page: int = Query(None, ge=1),
    page_size: int = Query(None, ge=1),
):
    try:

        dto = ListLMPRequest(
            date_start=date_start,
            date_end=date_end,
            page=page,
            page_size=page_size
        )

        use_case = build_list_lmp_use_case()

        result = use_case.execute(dto)

        return success_response(data=result.to_dict())

    except Exception as e:
        log_error(f"Erro ao listar LMP's: {e}")
        return error_response(str(e))
    
@router.get("/{code}")
@require_permission("api-delpi.access")
def get_lmp_route(
    sale_number: str
):
    try:
        dto = GetLMPRequest(
            sale_number=sale_number
        )
        use_case = build_get_lmp_use_case()

        result = use_case.execute(dto)

        return success_response(
            data=result,
            message=f"LMP in sale order {sale_number} fetched successfully."
        )
    except Exception as e:
        log_error(f"Erro ao buscar LMP: {e}")
        return error_response(str(e))
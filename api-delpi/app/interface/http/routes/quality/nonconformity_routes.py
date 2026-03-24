# app/interface/http/routes/quality/nonconformity_routes.py
from fastapi import APIRouter, Query
from typing import Optional

from delpi_auth.authorization import require_permission
from app.core.responses import success_response, error_response
from app.utils.logger import log_error

from app.application.dto.nonconformity.list_nonconformity_request import (
    ListNonconformityRequest,
)
from app.composition.nonconformity_composer import (
    build_list_nonconformity_use_case,
)

router = APIRouter()


@router.get("/")
@require_permission("api-delpi.quality.access")
def list_nonconformity_route(
    type: str = Query("all", pattern="^(internal|external|all)$"),
    branch: Optional[str] = None,
    date_start: Optional[str] = None,
    date_end: Optional[str] = None,
    status: Optional[str] = None,
    item_code: Optional[str] = None,
    description: Optional[str] = None,
    page: int = Query(None, ge=1),
    page_size: int = Query(None, ge=1),
):
    try:
        dto = ListNonconformityRequest(
            type=type,
            branch=branch,
            date_start=date_start,
            date_end=date_end,
            status=status,
            item_code=item_code,
            description=description,
            page=page,
            page_size=page_size
        )

        use_case = build_list_nonconformity_use_case()
        result = use_case.execute(dto)

        return success_response(data=result.to_dict())

    except ValueError as e:
        log_error(f"Erro de validação ao buscar não conformidades: {e}")
        return error_response(str(e), status_code=400)

    except Exception as e:
        log_error(f"Erro ao buscar não conformidades: {e}")
        return error_response("Erro interno ao buscar não conformidades.", status_code=500)
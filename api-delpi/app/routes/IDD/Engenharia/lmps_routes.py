from fastapi import APIRouter, HTTPException, Query, Request
from app.core.responses import success_response, error_response
from app.core.exceptions import DatabaseConnectionError
from app.utils.logger import log_info, log_error
from app.repositories.base_repository import BaseRepository
from pydantic import BaseModel
from typing import Optional
from app.models.product_model import ProductSearchRequest
from fastapi.responses import StreamingResponse
from fastapi.responses import JSONResponse

from delpi_auth.authorization import require_permission


router = APIRouter()


@router.get("/search")
@require_permission("api-delpi.access")
def search_lmps_route(
    code: Optional[str] = Query(None),
    group: Optional[str] = Query(None),
    description: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500)
):
    # try:
    #     result = search_lmps(code, group, description, page, page_size)
    #     return success_response(data=result)
    # except Exception as e:
    #     return error_response(str(e))
    pass
# app/interface/http/routes/financial_routes.py
from fastapi import APIRouter, Query
from typing import Optional

from app.core.responses import success_response, error_response
from app.utils.logger import log_error
from delpi_auth.authorization import require_permission

from app.application.dto.financial.get_rol_request import GetRolRequest
from app.composition.financial_composer import build_get_rol_use_case


router = APIRouter()


@router.get("/rol")
@require_permission("api-delpi.access")
def get_rol(
    branch: Optional[str] = Query(None, min_length=2, max_length=2),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    try:
        dto = GetRolRequest(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
        )

        use_case = build_get_rol_use_case()
        result = use_case.execute(dto)

        return success_response(
            data=result,
            message="ROL consultado com sucesso."
        )

    except Exception as e:
        log_error(f"Erro ao consultar ROL: {e}")
        return error_response(str(e))
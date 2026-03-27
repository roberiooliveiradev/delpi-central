# app/interface/http/routes/engineering/lmp_routes.py
from typing import Optional

from fastapi import APIRouter, Query
from delpi_auth.authorization import require_permission

from app.application.dto.lmp.list_lmp_request import ListLMPRequest
from app.application.dto.lmp.get_lmp_request import GetLMPRequest
from app.core.responses import success_response, error_response
from app.utils.logger import log_error
from app.composition.lmp_composer import (
    build_list_lmp_use_case,
    build_list_lmp_dashboard_use_case,
    build_get_lmp_use_case,
)

router = APIRouter()


@router.get("/")
@require_permission("api-delpi.access")
def list_lmps_route(
    date_start: Optional[str] = None,
    date_end: Optional[str] = None,
    branch: Optional[str] = None,
    page: Optional[int] = Query(None, ge=1),
    page_size: Optional[int] = Query(None, ge=1),
):
    try:
        dto = ListLMPRequest(
            date_start=date_start,
            date_end=date_end,
            branch=branch,
            page=page,
            page_size=page_size,
        )

        use_case = build_list_lmp_use_case()
        result = use_case.execute(dto)

        return success_response(
            data=result.to_dict(),
            message="LMPs listadas com sucesso."
        )

    except ValueError as e:
        log_error(f"Erro de validação ao listar LMPs: {e}")
        return error_response(str(e), status_code=400)

    except Exception as e:
        log_error(f"Erro ao listar LMPs: {e}")
        return error_response("Erro interno ao listar LMPs.", status_code=500)


@router.get("/dashboard")
@require_permission("api-delpi.access")
def list_lmps_dashboard_route(
    date_start: Optional[str] = None,
    date_end: Optional[str] = None,
    status: str = Query("Todos"),
    branch: Optional[str] = None,
    page: Optional[int] = Query(None, ge=1),
    page_size: Optional[int] = Query(None, ge=1),
):
    try:
        dto = ListLMPRequest(
            date_start=date_start,
            date_end=date_end,
            branch=branch,
            page=page,
            page_size=page_size,
        )

        use_case = build_list_lmp_dashboard_use_case()
        result = use_case.execute(dto, status_filter=status)

        return success_response(
            data=result,
            message="Dashboard de LMPs carregado com sucesso."
        )

    except ValueError as e:
        log_error(f"Erro de validação ao listar dashboard de LMPs: {e}")
        return error_response(str(e), status_code=400)

    except Exception as e:
        log_error(f"Erro ao listar dashboard de LMPs: {e}")
        return error_response("Erro interno ao listar dashboard de LMPs.", status_code=500)


@router.get("/{sale_number}")
@require_permission("api-delpi.access")
def get_lmp_route(sale_number: str):
    try:
        dto = GetLMPRequest(sale_number=sale_number)

        use_case = build_get_lmp_use_case()
        result = use_case.execute(dto)

        return success_response(
            data=result,
            message=f"LMP da ordem de venda {sale_number} carregada com sucesso."
        )

    except ValueError as e:
        log_error(f"Erro de validação ao buscar LMP {sale_number}: {e}")
        return error_response(str(e), status_code=400)

    except Exception as e:
        log_error(f"Erro ao buscar LMP {sale_number}: {e}")
        return error_response("Erro interno ao buscar LMP.", status_code=500)
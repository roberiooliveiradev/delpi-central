# app/interface/http/routes/quality/ppm_routes.py

from fastapi import APIRouter, Query
from typing import Optional

from delpi_auth.authorization import require_permission
from app.core.responses import success_response, error_response
from app.utils.logger import log_error

from app.application.dto.ppm.list_ppm_request import ListPpmRequest
from app.application.dto.ppm.ppm_summary_request import PpmSummaryRequest
from app.composition.ppm_composer import (
    build_list_ppm_use_case,
    build_get_ppm_summary_use_case,
)

router = APIRouter()


@router.get("/internal/summary")
@require_permission("api-delpi.access")
def get_internal_ppm_summary(
    branch: Optional[str] = None,
    date_start: Optional[str] = None,
    date_end: Optional[str] = None,
):
    try:
        dto = PpmSummaryRequest(
            type="internal",
            branch=branch,
            date_start=date_start,
            date_end=date_end,
        )

        use_case = build_get_ppm_summary_use_case()
        result = use_case.execute(dto)

        return success_response(data=result.to_dict())

    except Exception as e:
        log_error(f"Erro ao buscar resumo de PPM interno: {e}")
        return error_response(str(e))


@router.get("/external/summary")
@require_permission("api-delpi.access")
def get_external_ppm_summary(
    branch: Optional[str] = None,
    date_start: Optional[str] = None,
    date_end: Optional[str] = None,
):
    try:
        dto = PpmSummaryRequest(
            type="external",
            branch=branch,
            date_start=date_start,
            date_end=date_end,
        )

        use_case = build_get_ppm_summary_use_case()
        result = use_case.execute(dto)

        return success_response(data=result.to_dict())

    except Exception as e:
        log_error(f"Erro ao buscar resumo de PPM externo: {e}")
        return error_response(str(e))


@router.get("/internal")
@require_permission("api-delpi.access")
def list_internal_ppm(
    branch: Optional[str] = None,
    date_start: Optional[str] = None,
    date_end: Optional[str] = None,
    page: int = Query(None, ge=1),
    page_size: int = Query(None, ge=1),
):
    try:
        dto = ListPpmRequest(
            type="internal",
            branch=branch,
            date_start=date_start,
            date_end=date_end,
            page=page,
            page_size=page_size,
        )

        use_case = build_list_ppm_use_case()
        result = use_case.execute(dto)

        return success_response(data=result.to_dict())

    except Exception as e:
        log_error(f"Erro ao listar PPM interno: {e}")
        return error_response(str(e))


@router.get("/external")
@require_permission("api-delpi.access")
def list_external_ppm(
    branch: Optional[str] = None,
    date_start: Optional[str] = None,
    date_end: Optional[str] = None,
    page: int = Query(None, ge=1),
    page_size: int = Query(None, ge=1),
):
    try:
        dto = ListPpmRequest(
            type="external",
            branch=branch,
            date_start=date_start,
            date_end=date_end,
            page=page,
            page_size=page_size,
        )

        use_case = build_list_ppm_use_case()
        result = use_case.execute(dto)

        return success_response(data=result.to_dict())

    except Exception as e:
        log_error(f"Erro ao listar PPM externo: {e}")
        return error_response(str(e))
from fastapi import APIRouter, Query
from typing import Optional

from delpi_auth.authorization import require_any_permission

from app.core.responses import success_response, error_response
from app.utils.logger import log_error

from app.application.dto.auditoria_5s.audit_5s_summary_request import (
    Audit5SSummaryRequest,
)
from app.application.dto.kaizen.kaizen_summary_request import (
    KaizenSummaryRequest,
)
from app.application.dto.nonconformity.list_nonconformity_request import (
    ListNonconformityRequest,
)
from app.application.dto.ppm.list_ppm_request import ListPpmRequest
from app.application.dto.ppm.ppm_summary_request import PpmSummaryRequest

from app.composition.quality_composer import (
    build_get_audit_5s_summary_use_case,
    build_get_kaizen_summary_use_case,
    build_get_ppm_summary_use_case,
    build_list_nonconformity_use_case,
    build_list_ppm_use_case,
)

router = APIRouter(prefix="/quality", tags=["Qualidade"])


@router.get("/nonconformities")
@require_any_permission(["api-delpi.quality.access", "dashboard-quality.view"])
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
            page_size=page_size,
        )

        use_case = build_list_nonconformity_use_case()
        result = use_case.execute(dto)

        return success_response(data=result.to_dict())

    except ValueError as exc:
        log_error(f"Erro de validação ao buscar não conformidades: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao buscar não conformidades: {exc}")
        return error_response(
            "Erro interno ao buscar não conformidades.",
            status_code=500,
        )


@router.get("/kaizens/summary")
@require_any_permission(["api-delpi.quality.access", "dashboard-quality.view"])
def get_kaizen_summary(
    title: str | None = Query(default=None),
    status: str | None = Query(default=None),
    branch: str | None = Query(default=None),
    date_start: str | None = Query(default=None),
    date_end: str | None = Query(default=None),
):
    try:
        use_case = build_get_kaizen_summary_use_case()

        request = KaizenSummaryRequest(
            title=title,
            status=status,
            branch=branch,
            date_start=date_start,
            date_end=date_end,
        )

        summary = use_case.execute(request)

        return success_response(data=summary.to_dict())

    except ValueError as exc:
        log_error(f"Erro de validação ao gerar resumo de kaizens: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao gerar resumo de kaizens: {exc}")
        return error_response(
            "Erro interno ao gerar resumo de kaizens.",
            status_code=500,
        )


@router.get("/audit-5s/summary")
@require_any_permission(["api-delpi.quality.access", "dashboard-quality.view"])
def get_audit_5s_summary(
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    branch: str | None = Query(default=None),
):
    try:
        use_case = build_get_audit_5s_summary_use_case()

        request = Audit5SSummaryRequest(
            start_date=start_date,
            end_date=end_date,
            branch=branch,
        )

        summary = use_case.execute(request)

        return success_response(data=summary.to_dict())

    except ValueError as exc:
        log_error(f"Erro de validação ao gerar resumo das auditorias 5S: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao gerar resumo das auditorias 5S: {exc}")
        return error_response(
            "Erro interno ao gerar resumo das auditorias 5S.",
            status_code=500,
        )


@router.get("/ppm/internal/summary")
@require_any_permission(["api-delpi.quality.access", "dashboard-quality.view"])
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

    except ValueError as exc:
        log_error(f"Erro de validação ao buscar resumo de PPM interno: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao buscar resumo de PPM interno: {exc}")
        return error_response(
            "Erro interno ao buscar resumo de PPM interno.",
            status_code=500,
        )


@router.get("/ppm/external/summary")
@require_any_permission(["api-delpi.quality.access", "dashboard-quality.view"])
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

    except ValueError as exc:
        log_error(f"Erro de validação ao buscar resumo de PPM externo: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao buscar resumo de PPM externo: {exc}")
        return error_response(
            "Erro interno ao buscar resumo de PPM externo.",
            status_code=500,
        )


@router.get("/ppm/internal")
@require_any_permission(["api-delpi.quality.access", "dashboard-quality.view"])
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

    except ValueError as exc:
        log_error(f"Erro de validação ao listar PPM interno: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao listar PPM interno: {exc}")
        return error_response(
            "Erro interno ao listar PPM interno.",
            status_code=500,
        )


@router.get("/ppm/external")
@require_any_permission(["api-delpi.quality.access", "dashboard-quality.view"])
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

    except ValueError as exc:
        log_error(f"Erro de validação ao listar PPM externo: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao listar PPM externo: {exc}")
        return error_response(
            "Erro interno ao listar PPM externo.",
            status_code=500,
        )
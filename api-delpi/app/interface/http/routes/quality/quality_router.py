from fastapi import APIRouter, Query
from typing import Optional

from delpi_auth.authorization import require_any_permission

from app.application.security.api_delpi_permissions import KPI_QUALITY_ACCESS

from app.core.responses import error_response
from app.interface.http.route_response_helpers import api_delpi_success
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
from app.application.dto.nonconformity.nonconformity_series_request import (
    NonconformitySeriesRequest,
)
from app.application.dto.ppm.list_ppm_request import ListPpmRequest
from app.application.dto.ppm.ppm_series_request import PpmSeriesRequest
from app.application.dto.ppm.ppm_summary_request import PpmSummaryRequest

from app.application.services.strategic_indicators import dashboard_goal_source_keys as goal_keys
from app.composition.quality_composer import (
    build_get_audit_5s_summary_use_case,
    build_get_kaizen_summary_use_case,
    build_get_ppm_series_use_case,
    build_get_ppm_summary_use_case,
    build_get_nonconformity_series_use_case,
    build_list_nonconformity_use_case,
    build_list_ppm_use_case,
    build_list_quality_branches_use_case,
)
from app.interface.http.routes.shared.dashboard_goal_enrichment import enrich_dashboard_metric
from app.interface.http.kpi_field_labels import (
    QUALITY_AUDIT_5S_FIELD_LABELS,
    QUALITY_KAIZEN_FIELD_LABELS,
    QUALITY_PPM_FIELD_LABELS,
    kpi_fields,
)
from app.interface.http.routes.quality.audit_5s_operational_router import (
    router as audit_5s_operational_router,
)

router = APIRouter(prefix="/quality", tags=["Qualidade"])
router.include_router(audit_5s_operational_router)


@router.get("/branches")
@require_any_permission(KPI_QUALITY_ACCESS)
def list_quality_branches(
    date_start: Optional[str] = None,
    date_end: Optional[str] = None,
):
    try:
        use_case = build_list_quality_branches_use_case()
        result = use_case.execute(
            date_start=date_start,
            date_end=date_end,
        )

        return api_delpi_success(
            result.to_dict(),
            operation_id="list_quality_branches",
        )

    except ValueError as exc:
        log_error(f"Erro de validação ao listar filiais de qualidade: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao listar filiais de qualidade: {exc}")
        return error_response(
            "Erro interno ao listar filiais de qualidade.",
            status_code=500,
        )


@router.get("/nonconformities/series")
@require_any_permission(KPI_QUALITY_ACCESS)
def get_nonconformity_series(
    type: str = Query("all", pattern="^(internal|external|all)$"),
    granularity: str = Query("month", pattern="^(day|week|month|year)$"),
    branch: Optional[str] = None,
    date_start: Optional[str] = None,
    date_end: Optional[str] = None,
    status: Optional[str] = None,
    item_code: Optional[str] = None,
    description: Optional[str] = None,
):
    try:
        dto = NonconformitySeriesRequest(
            type=type,
            granularity=granularity,
            branch=branch,
            date_start=date_start,
            date_end=date_end,
            status=status,
            item_code=item_code,
            description=description,
        )

        use_case = build_get_nonconformity_series_use_case()
        result = use_case.execute(dto)

        return api_delpi_success(
            result.to_dict(),
            operation_id="get_nonconformity_series",
        )
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao buscar série de NC: {exc}")
        return error_response(
            "Erro interno ao buscar série de não conformidades.",
            status_code=500,
        )


@router.get("/nonconformities")
@require_any_permission(KPI_QUALITY_ACCESS)
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

        return api_delpi_success(
            result.to_dict(),
            operation_id="list_nonconformities",
        )
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao buscar não conformidades: {exc}")
        return error_response(
            "Erro interno ao buscar não conformidades.",
            status_code=500,
        )


@router.get("/kaizens/summary")
@require_any_permission(KPI_QUALITY_ACCESS)
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

        summary = enrich_dashboard_metric(
            use_case.execute(request).to_dict(),
            source_key=goal_keys.QUALITY_KAIZEN_IDEAS,
            start_date=date_start,
            end_date=date_end,
            branch=branch,
        )

        return api_delpi_success(
            summary,
            operation_id="get_kaizen_summary",
            fields=kpi_fields(QUALITY_KAIZEN_FIELD_LABELS),
        )

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
@require_any_permission(KPI_QUALITY_ACCESS)
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

        summary = enrich_dashboard_metric(
            use_case.execute(request).to_dict(),
            source_key=goal_keys.QUALITY_AUDIT_5S,
            start_date=start_date,
            end_date=end_date,
            branch=branch,
        )

        return api_delpi_success(
            summary,
            operation_id="get_audit_5s_summary",
            fields=kpi_fields(QUALITY_AUDIT_5S_FIELD_LABELS),
        )
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao gerar resumo das auditorias 5S: {exc}")
        return error_response(
            "Erro interno ao gerar resumo das auditorias 5S.",
            status_code=500,
        )


@router.get("/ppm/internal/summary")
@require_any_permission(KPI_QUALITY_ACCESS)
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
        result = enrich_dashboard_metric(
            use_case.execute(dto).to_dict(),
            source_key=goal_keys.QUALITY_PPM_INTERNAL,
            start_date=date_start,
            end_date=date_end,
            branch=branch,
        )

        return api_delpi_success(
            result,
            operation_id="get_ppm_internal_summary",
            fields=kpi_fields(QUALITY_PPM_FIELD_LABELS),
        )
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao buscar resumo de PPM interno: {exc}")
        return error_response(
            "Erro interno ao buscar resumo de PPM interno.",
            status_code=500,
        )


@router.get("/ppm/external/summary")
@require_any_permission(KPI_QUALITY_ACCESS)
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
        result = enrich_dashboard_metric(
            use_case.execute(dto).to_dict(),
            source_key=goal_keys.QUALITY_PPM_EXTERNAL,
            start_date=date_start,
            end_date=date_end,
            branch=branch,
        )

        return api_delpi_success(
            result,
            operation_id="get_ppm_external_summary",
            fields=kpi_fields(QUALITY_PPM_FIELD_LABELS),
        )
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao buscar resumo de PPM externo: {exc}")
        return error_response(
            "Erro interno ao buscar resumo de PPM externo.",
            status_code=500,
        )


@router.get("/ppm/internal/series")
@require_any_permission(KPI_QUALITY_ACCESS)
def get_internal_ppm_series(
    granularity: str = Query("month", pattern="^(day|week|month|year)$"),
    branch: Optional[str] = None,
    date_start: Optional[str] = None,
    date_end: Optional[str] = None,
):
    return _get_ppm_series_route(
        ppm_type="internal",
        granularity=granularity,
        branch=branch,
        date_start=date_start,
        date_end=date_end,
    )


@router.get("/ppm/external/series")
@require_any_permission(KPI_QUALITY_ACCESS)
def get_external_ppm_series(
    granularity: str = Query("month", pattern="^(day|week|month|year)$"),
    branch: Optional[str] = None,
    date_start: Optional[str] = None,
    date_end: Optional[str] = None,
):
    return _get_ppm_series_route(
        ppm_type="external",
        granularity=granularity,
        branch=branch,
        date_start=date_start,
        date_end=date_end,
    )


@router.get("/ppm/internal")
@require_any_permission(KPI_QUALITY_ACCESS)
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

        return api_delpi_success(
            result.to_dict(),
            operation_id="list_ppm_internal",
        )
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao listar PPM interno: {exc}")
        return error_response(
            "Erro interno ao listar PPM interno.",
            status_code=500,
        )


@router.get("/ppm/external")
@require_any_permission(KPI_QUALITY_ACCESS)
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

        return api_delpi_success(
            result.to_dict(),
            operation_id="list_ppm_external",
        )
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao listar PPM externo: {exc}")
        return error_response(
            "Erro interno ao listar PPM externo.",
            status_code=500,
        )


def _get_ppm_series_route(
    *,
    ppm_type: str,
    granularity: str,
    branch: Optional[str],
    date_start: Optional[str],
    date_end: Optional[str],
):
    try:
        dto = PpmSeriesRequest(
            type=ppm_type,
            granularity=granularity,
            branch=branch,
            date_start=date_start,
            date_end=date_end,
        )

        use_case = build_get_ppm_series_use_case()
        result = use_case.execute(dto)

        return api_delpi_success(
            result.to_dict(),
            operation_id=f"get_ppm_{ppm_type}_series",
        )
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao buscar série de PPM {ppm_type}: {exc}")
        return error_response(
            f"Erro interno ao buscar série de PPM {ppm_type}.",
            status_code=500,
        )
from fastapi import APIRouter, Query

from app.interface.http.period_query_params import (
    END_DATE_QUERY,
    LEGACY_DATE_END_QUERY,
    LEGACY_DATE_START_QUERY,
    START_DATE_QUERY,
    resolve_period_dates,
)
from app.interface.http.query_param_enums import (
    BRANCH_QUERY_OPTIONAL,
    KAIZEN_STATUS_QUERY,
    NONCONFORMITY_QI2_STATUS_QUERY,
    GRANULARITY_QUERY_MONTH,
    NONCONFORMITY_TYPE_QUERY,
)
from typing import Optional

from delpi_auth.authorization import require_any_permission

from app.application.security.api_delpi_permissions import KPI_QUALITY_ACCESS

from app.core.responses import error_response, not_found_response
from app.interface.http.route_response_helpers import api_delpi_success
from app.interface.http.openapi_agent_metadata_builder import OpenApiAgentMetadataBuilder
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

from app.application.services.quality.quality_kpi_parity_service import (
    attach_quality_kpi_parity,
)
from app.application.services.strategic_indicators import dashboard_goal_source_keys as goal_keys
from app.composition.quality_composer import (
    build_get_audit_5s_summary_use_case,
    build_get_kaizen_by_id_use_case,
    build_get_kaizen_summary_use_case,
    build_get_nonconformity_series_use_case,
    build_get_nonconformity_streak_use_case,
    build_list_nonconformity_use_case,
    build_list_quality_branches_use_case,
)
from app.interface.http.kpi_field_labels import (
    QUALITY_AUDIT_5S_FIELD_LABELS,
    QUALITY_KAIZEN_FIELD_LABELS,
    QUALITY_KAIZEN_DETAIL_FIELD_LABELS,
    QUALITY_NONCONFORMITY_STREAK_FIELD_LABELS,
    kpi_fields,
)
from app.interface.http.openapi_agent_metadata import (
    QUALITY_KAIZEN_BY_ID,
    QUALITY_KAIZEN_SUMMARY,
    QUALITY_NONCONFORMITY_STREAK,
)
from app.interface.http.routes.quality.action_plans_read_router import (
    router as action_plans_read_router,
)
from app.interface.http.routes.quality.action_plans_intelligence_router import (
    router as action_plans_intelligence_router,
)
from app.interface.http.routes.quality.solution_patterns_router import (
    router as solution_patterns_router,
)
from app.interface.http.routes.quality.audit_5s_operational_router import (
    router as audit_5s_operational_router,
)
from app.interface.http.routes.quality.kaizen_records_router import (
    router as kaizen_records_router,
)
from app.interface.http.routes.quality.losses_routes import router as losses_router
from app.interface.http.routes.quality.ppm_routes import router as ppm_router
from app.interface.http.routes.quality.quality_labels_router import (
    router as quality_labels_router,
)
from app.interface.http.routes.shared.dashboard_goal_enrichment import enrich_dashboard_metric

router = APIRouter(prefix="/quality", tags=["Qualidade"])
router.include_router(action_plans_read_router)
router.include_router(action_plans_intelligence_router)
router.include_router(solution_patterns_router)
router.include_router(audit_5s_operational_router)
router.include_router(kaizen_records_router)
router.include_router(ppm_router)
router.include_router(losses_router)
router.include_router(quality_labels_router)


@router.get("/branches", operation_id="list_quality_branches")
@require_any_permission(KPI_QUALITY_ACCESS)
def list_quality_branches(
    start_date: Optional[str] = START_DATE_QUERY(),
    end_date: Optional[str] = END_DATE_QUERY(),
    date_start: Optional[str] = LEGACY_DATE_START_QUERY(),
    date_end: Optional[str] = LEGACY_DATE_END_QUERY(),
):
    try:
        start_date, end_date = resolve_period_dates(
            start_date=start_date,
            end_date=end_date,
            date_start=date_start,
            date_end=date_end,
        )
        use_case = build_list_quality_branches_use_case()
        result = use_case.execute(
            date_start=start_date,
            date_end=end_date,
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


@router.get("/nonconformities/series", operation_id="get_nonconformity_series")
@require_any_permission(KPI_QUALITY_ACCESS)
def get_nonconformity_series(
    type: str = NONCONFORMITY_TYPE_QUERY(),
    granularity: str = GRANULARITY_QUERY_MONTH(),
    branch: Optional[str] = BRANCH_QUERY_OPTIONAL(),
    start_date: Optional[str] = START_DATE_QUERY(),
    end_date: Optional[str] = END_DATE_QUERY(),
    date_start: Optional[str] = LEGACY_DATE_START_QUERY(),
    date_end: Optional[str] = LEGACY_DATE_END_QUERY(),
    status: Optional[str] = NONCONFORMITY_QI2_STATUS_QUERY(),
    item_code: Optional[str] = None,
    description: Optional[str] = None,
):
    try:
        start_date, end_date = resolve_period_dates(
            start_date=start_date,
            end_date=end_date,
            date_start=date_start,
            date_end=date_end,
        )
        dto = NonconformitySeriesRequest(
            type=type,
            granularity=granularity,
            branch=branch,
            date_start=start_date,
            date_end=end_date,
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

    except ValueError as exc:
        log_error(f"Erro de validação ao buscar série de NC: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao buscar série de NC: {exc}")
        return error_response(
            "Erro interno ao buscar série de não conformidades.",
            status_code=500,
        )


@router.get("/nonconformities/streak", **QUALITY_NONCONFORMITY_STREAK)
@require_any_permission(KPI_QUALITY_ACCESS)
def get_nonconformity_streak(
    type: str = NONCONFORMITY_TYPE_QUERY(default="customer"),
    branch: Optional[str] = BRANCH_QUERY_OPTIONAL(),
    product_prefix: Optional[str] = Query(
        None,
        description=(
            "Finished-product code prefix (QI2_ITEM). Use 9048 for plugs, "
            "9026 for components. Digits only; empty = all products."
        ),
    ),
):
    try:
        use_case = build_get_nonconformity_streak_use_case()
        result = use_case.execute(
            filter_type=type,
            branch=branch,
            product_prefix=product_prefix,
        )

        return api_delpi_success(
            result,
            operation_id="get_nonconformity_streak",
            fields=kpi_fields(QUALITY_NONCONFORMITY_STREAK_FIELD_LABELS),
        )

    except ValueError as exc:
        log_error(f"Erro de validação ao calcular streak de NC: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao calcular streak de NC: {exc}")
        return error_response(
            "Erro interno ao calcular dias sem não conformidades.",
            status_code=500,
        )


@router.get("/nonconformities", operation_id="list_nonconformities")
@require_any_permission(KPI_QUALITY_ACCESS)
def list_nonconformity_route(
    type: str = NONCONFORMITY_TYPE_QUERY(),
    branch: Optional[str] = BRANCH_QUERY_OPTIONAL(),
    start_date: Optional[str] = START_DATE_QUERY(),
    end_date: Optional[str] = END_DATE_QUERY(),
    date_start: Optional[str] = LEGACY_DATE_START_QUERY(),
    date_end: Optional[str] = LEGACY_DATE_END_QUERY(),
    status: Optional[str] = NONCONFORMITY_QI2_STATUS_QUERY(),
    item_code: Optional[str] = None,
    description: Optional[str] = None,
    page: int = Query(None, ge=1),
    page_size: int = Query(None, ge=1),
):
    try:
        start_date, end_date = resolve_period_dates(
            start_date=start_date,
            end_date=end_date,
            date_start=date_start,
            date_end=date_end,
        )
        dto = ListNonconformityRequest(
            type=type,
            branch=branch,
            date_start=start_date,
            date_end=end_date,
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

    except ValueError as exc:
        log_error(f"Erro de validação ao buscar não conformidades: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao buscar não conformidades: {exc}")
        return error_response(
            "Erro interno ao buscar não conformidades.",
            status_code=500,
        )


@router.get("/kaizens/summary", **QUALITY_KAIZEN_SUMMARY)
@require_any_permission(KPI_QUALITY_ACCESS)
def get_kaizen_summary(
    title: str | None = Query(default=None),
    status: str | None = KAIZEN_STATUS_QUERY(),
    branch: str | None = BRANCH_QUERY_OPTIONAL(),
    start_date: str | None = START_DATE_QUERY(),
    end_date: str | None = END_DATE_QUERY(),
    date_start: str | None = LEGACY_DATE_START_QUERY(),
    date_end: str | None = LEGACY_DATE_END_QUERY(),
):
    try:
        start_date, end_date = resolve_period_dates(
            start_date=start_date,
            end_date=end_date,
            date_start=date_start,
            date_end=date_end,
        )
        use_case = build_get_kaizen_summary_use_case()

        request = KaizenSummaryRequest(
            title=title,
            status=status,
            branch=branch,
            date_start=start_date,
            date_end=end_date,
        )

        summary = use_case.execute(request).to_dict()
        summary["ideas_goal"] = {
            "total_kaizens": summary.get("total_kaizens", 0),
        }
        summary = enrich_dashboard_metric(
            summary,
            source_key=goal_keys.QUALITY_KAIZEN_IDEAS,
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            summary_key="ideas_goal",
        )
        summary = enrich_dashboard_metric(
            summary,
            source_key=goal_keys.QUALITY_KAIZEN_FINANCIAL,
            start_date=start_date,
            end_date=end_date,
            branch=branch,
        )
        summary = attach_quality_kpi_parity(
            summary,
            primary_field="total_savings",
            branch=branch,
            start_date=start_date,
            end_date=end_date,
            summary_extra_fields=("total_kaizens", "total_savings", "total_hours_saved"),
            nested_blocks={"ideas_goal": "total_kaizens"},
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


@router.get(
    "/kaizens/summary/series",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_kaizen_summary_series",
        path="/quality/kaizens/summary/series",
    ),
)
@require_any_permission(KPI_QUALITY_ACCESS)
def get_kaizen_summary_series(
    branch: str | None = BRANCH_QUERY_OPTIONAL(),
    start_date: str | None = START_DATE_QUERY(),
    end_date: str | None = END_DATE_QUERY(),
    date_start: str | None = LEGACY_DATE_START_QUERY(),
    date_end: str | None = LEGACY_DATE_END_QUERY(),
    granularity: str = GRANULARITY_QUERY_MONTH(),
):
    from app.application.use_cases.quality.get_quality_scalar_series_use_case import (
        GetQualityScalarSeriesUseCase,
    )

    start_date, end_date = resolve_period_dates(
        start_date=start_date,
        end_date=end_date,
        date_start=date_start,
        date_end=date_end,
    )

    def fetch_metrics(scope_branch, bucket_start, bucket_end):
        summary = build_get_kaizen_summary_use_case().execute(
            KaizenSummaryRequest(
                title=None,
                status=None,
                branch=scope_branch,
                date_start=bucket_start,
                date_end=bucket_end,
            )
        ).to_dict()
        return {
            "total_kaizens": summary.get("total_kaizens"),
            "total_savings": summary.get("total_savings"),
        }

    try:
        result = GetQualityScalarSeriesUseCase(
            metric="kaizen_summary",
            fetch_metrics=fetch_metrics,
        ).execute(
            branch=branch,
            date_start=start_date,
            date_end=end_date,
            granularity=granularity,
        )
        return api_delpi_success(
            result.to_dict(),
            operation_id="get_kaizen_summary_series",
            message="Kaizen summary series loaded.",
        )
    except ValueError as exc:
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro ao carregar série kaizen: {exc}")
        return error_response("Erro interno ao carregar série kaizen.", status_code=500)


@router.get("/kaizens/{kaizen_id:path}", **QUALITY_KAIZEN_BY_ID)
@require_any_permission(KPI_QUALITY_ACCESS)
def get_kaizen_by_id(kaizen_id: str):
    try:
        use_case = build_get_kaizen_by_id_use_case()
        detail = use_case.execute(kaizen_id)

        if detail is None:
            return not_found_response("Kaizen não encontrado.")

        return api_delpi_success(
            detail.to_dict(),
            operation_id="get_kaizen_by_id",
            fields=kpi_fields(QUALITY_KAIZEN_DETAIL_FIELD_LABELS),
        )

    except Exception as exc:
        log_error(f"Erro ao buscar detalhe do kaizen: {exc}")
        return error_response(
            "Erro interno ao buscar detalhe do kaizen.",
            status_code=500,
        )


@router.get("/audit-5s/summary", operation_id="get_audit_5s_summary")
@require_any_permission(KPI_QUALITY_ACCESS)
def get_audit_5s_summary(
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    branch: str | None = BRANCH_QUERY_OPTIONAL(),
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
        summary = attach_quality_kpi_parity(
            summary,
            primary_field="average_score",
            branch=branch,
            start_date=start_date,
            end_date=end_date,
            summary_extra_fields=("average_score",),
        )

        return api_delpi_success(
            summary,
            operation_id="get_audit_5s_summary",
            fields=kpi_fields(QUALITY_AUDIT_5S_FIELD_LABELS),
        )

    except ValueError as exc:
        log_error(f"Erro de validação ao gerar resumo das auditorias 5S: {exc}")
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro ao gerar resumo das auditorias 5S: {exc}")
        return error_response(
            "Erro interno ao gerar resumo das auditorias 5S.",
            status_code=500,
        )



@router.get(
    "/audit-5s/summary/series",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_audit_5s_summary_series",
        path="/quality/audit-5s/summary/series",
    ),
)
@require_any_permission(KPI_QUALITY_ACCESS)
def get_audit_5s_summary_series(
    branch: str | None = BRANCH_QUERY_OPTIONAL(),
    start_date: str | None = START_DATE_QUERY(),
    end_date: str | None = END_DATE_QUERY(),
    granularity: str = GRANULARITY_QUERY_MONTH(),
):
    from app.application.use_cases.quality.get_quality_scalar_series_use_case import (
        GetQualityScalarSeriesUseCase,
    )

    def fetch_metrics(scope_branch, bucket_start, bucket_end):
        summary = build_get_audit_5s_summary_use_case().execute(
            Audit5SSummaryRequest(
                start_date=bucket_start,
                end_date=bucket_end,
                branch=scope_branch,
            )
        ).to_dict()
        return {"average_score": summary.get("average_score")}

    try:
        result = GetQualityScalarSeriesUseCase(
            metric="audit_5s_summary",
            fetch_metrics=fetch_metrics,
        ).execute(
            branch=branch,
            date_start=start_date,
            date_end=end_date,
            granularity=granularity,
        )
        return api_delpi_success(
            result.to_dict(),
            operation_id="get_audit_5s_summary_series",
            message="Audit 5S summary series loaded.",
        )
    except ValueError as exc:
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro ao carregar série audit-5s: {exc}")
        return error_response(
            "Erro interno ao carregar série audit-5s.",
            status_code=500,
        )


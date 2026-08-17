"""Rotas de perdas (custo refugo/retrabalho × ROL) sob /quality — dashboard + SI."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter

from delpi_auth.authorization import require_any_permission

from app.application.security.api_delpi_permissions import KPI_QUALITY_ACCESS
from app.application.services.strategic_indicators import dashboard_goal_source_keys as goal_keys
from app.composition.refugos_composer import build_get_refugos_scrap_cost_pct_use_case
from app.composition.retrabalho_composer import (
    build_get_retrabalho_rework_cost_pct_use_case,
)
from app.core.responses import error_response
from app.interface.http.kpi_field_labels import (
    REFUGOS_SCRAP_COST_PCT_FIELD_LABELS,
    RETRABALHO_REWORK_COST_PCT_FIELD_LABELS,
    kpi_fields,
)
from app.interface.http.openapi_agent_metadata_builder import OpenApiAgentMetadataBuilder
from app.interface.http.period_query_params import (
    END_DATE_QUERY,
    LEGACY_DATE_END_QUERY,
    LEGACY_DATE_START_QUERY,
    START_DATE_QUERY,
    resolve_period_dates,
)
from app.interface.http.query_param_enums import BRANCH_QUERY_OPTIONAL, GRANULARITY_QUERY_MONTH
from app.application.use_cases.quality.get_quality_scalar_series_use_case import (
    GetQualityScalarSeriesUseCase,
)
from app.interface.http.route_response_helpers import api_delpi_success
from app.interface.http.routes.refugos.refugos_route_helpers import (
    build_refugos_query_request,
)
from app.interface.http.routes.retrabalho.retrabalho_route_helpers import (
    build_retrabalho_query_request,
)
from app.interface.http.routes.shared.dashboard_goal_enrichment import (
    enrich_dashboard_metric,
)
from app.utils.logger import log_error

router = APIRouter(tags=["Qualidade — Perdas"])


@router.get(
    "/scrap-cost-pct",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_quality_scrap_cost_pct",
        path="/quality/scrap-cost-pct",
    ),
)
@require_any_permission(KPI_QUALITY_ACCESS)
def get_quality_scrap_cost_pct(
    branch: Optional[str] = BRANCH_QUERY_OPTIONAL(),
    start_date: Optional[str] = START_DATE_QUERY(),
    end_date: Optional[str] = END_DATE_QUERY(),
    date_start: Optional[str] = LEGACY_DATE_START_QUERY(),
    date_end: Optional[str] = LEGACY_DATE_END_QUERY(),
):
    start_date, end_date = resolve_period_dates(
        start_date=start_date,
        end_date=end_date,
        date_start=date_start,
        date_end=date_end,
    )
    try:
        request = build_refugos_query_request(
            filial=branch,
            data_inicio=start_date,
            data_fim=end_date,
            require_filial=False,
        )
    except ValueError as exc:
        log_error(f"Erro de validação ao carregar custo de refugo / ROL (quality): {exc}")
        return error_response(str(exc), status_code=400)

    try:
        use_case = build_get_refugos_scrap_cost_pct_use_case()
        result = use_case.execute(request)
        result = enrich_dashboard_metric(
            result,
            source_key=goal_keys.QUALITY_SCRAP_COST_PCT,
            start_date=start_date,
            end_date=end_date,
            branch=branch,
        )
        return api_delpi_success(
            result,
            operation_id="get_quality_scrap_cost_pct",
            message="Custo de refugo / ROL carregado com sucesso.",
            fields=kpi_fields(REFUGOS_SCRAP_COST_PCT_FIELD_LABELS),
        )
    except ValueError as exc:
        log_error(f"Erro de validação ao carregar custo de refugo / ROL (quality): {exc}")
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro ao carregar custo de refugo / ROL (quality): {exc}")
        return error_response(
            "Erro interno ao carregar custo de refugo / ROL.",
            status_code=500,
        )


@router.get(
    "/rework-cost-pct",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_quality_rework_cost_pct",
        path="/quality/rework-cost-pct",
    ),
)
@require_any_permission(KPI_QUALITY_ACCESS)
def get_quality_rework_cost_pct(
    branch: Optional[str] = BRANCH_QUERY_OPTIONAL(),
    start_date: Optional[str] = START_DATE_QUERY(),
    end_date: Optional[str] = END_DATE_QUERY(),
    date_start: Optional[str] = LEGACY_DATE_START_QUERY(),
    date_end: Optional[str] = LEGACY_DATE_END_QUERY(),
):
    start_date, end_date = resolve_period_dates(
        start_date=start_date,
        end_date=end_date,
        date_start=date_start,
        date_end=date_end,
    )
    try:
        request = build_retrabalho_query_request(
            filial=branch,
            data_inicio=start_date,
            data_fim=end_date,
            require_filial=False,
        )
    except ValueError as exc:
        log_error(
            f"Erro de validação ao carregar custo de retrabalho / ROL (quality): {exc}"
        )
        return error_response(str(exc), status_code=400)

    try:
        use_case = build_get_retrabalho_rework_cost_pct_use_case()
        result = use_case.execute(request)
        result = enrich_dashboard_metric(
            result,
            source_key=goal_keys.QUALITY_REWORK_COST_PCT,
            start_date=start_date,
            end_date=end_date,
            branch=branch,
        )
        return api_delpi_success(
            result,
            operation_id="get_quality_rework_cost_pct",
            message="Custo de retrabalho / ROL carregado com sucesso.",
            fields=kpi_fields(RETRABALHO_REWORK_COST_PCT_FIELD_LABELS),
        )
    except ValueError as exc:
        log_error(
            f"Erro de validação ao carregar custo de retrabalho / ROL (quality): {exc}"
        )
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro ao carregar custo de retrabalho / ROL (quality): {exc}")
        return error_response(
            "Erro interno ao carregar custo de retrabalho / ROL.",
            status_code=500,
        )


def _run_loss_series(
    *,
    metric: str,
    operation_id: str,
    branch: Optional[str],
    start_date: Optional[str],
    end_date: Optional[str],
    date_start: Optional[str],
    date_end: Optional[str],
    granularity: str,
    fetch_metrics,
):
    start_date, end_date = resolve_period_dates(
        start_date=start_date,
        end_date=end_date,
        date_start=date_start,
        date_end=date_end,
    )
    try:
        use_case = GetQualityScalarSeriesUseCase(
            metric=metric,
            fetch_metrics=fetch_metrics,
        )
        result = use_case.execute(
            branch=branch,
            date_start=start_date,
            date_end=end_date,
            granularity=granularity,
        )
        return api_delpi_success(
            result.to_dict(),
            operation_id=operation_id,
            message=f"{metric} series loaded.",
        )
    except ValueError as exc:
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro ao carregar série {metric}: {exc}")
        return error_response(
            f"Erro interno ao carregar série {metric}.",
            status_code=500,
        )


@router.get(
    "/scrap-cost-pct/series",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_quality_scrap_cost_pct_series",
        path="/quality/scrap-cost-pct/series",
    ),
)
@require_any_permission(KPI_QUALITY_ACCESS)
def get_quality_scrap_cost_pct_series(
    branch: Optional[str] = BRANCH_QUERY_OPTIONAL(),
    start_date: Optional[str] = START_DATE_QUERY(),
    end_date: Optional[str] = END_DATE_QUERY(),
    date_start: Optional[str] = LEGACY_DATE_START_QUERY(),
    date_end: Optional[str] = LEGACY_DATE_END_QUERY(),
    granularity: str = GRANULARITY_QUERY_MONTH(),
):
    def fetch_metrics(scope_branch, bucket_start, bucket_end):
        request = build_refugos_query_request(
            filial=scope_branch,
            data_inicio=bucket_start,
            data_fim=bucket_end,
            require_filial=False,
        )
        result = build_get_refugos_scrap_cost_pct_use_case().execute(request)
        return {
            "scrap_cost_pct": result.get("scrap_cost_pct")
            if isinstance(result, dict)
            else getattr(result, "scrap_cost_pct", None),
        }

    return _run_loss_series(
        metric="scrap_cost_pct",
        operation_id="get_quality_scrap_cost_pct_series",
        branch=branch,
        start_date=start_date,
        end_date=end_date,
        date_start=date_start,
        date_end=date_end,
        granularity=granularity,
        fetch_metrics=fetch_metrics,
    )


@router.get(
    "/rework-cost-pct/series",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_quality_rework_cost_pct_series",
        path="/quality/rework-cost-pct/series",
    ),
)
@require_any_permission(KPI_QUALITY_ACCESS)
def get_quality_rework_cost_pct_series(
    branch: Optional[str] = BRANCH_QUERY_OPTIONAL(),
    start_date: Optional[str] = START_DATE_QUERY(),
    end_date: Optional[str] = END_DATE_QUERY(),
    date_start: Optional[str] = LEGACY_DATE_START_QUERY(),
    date_end: Optional[str] = LEGACY_DATE_END_QUERY(),
    granularity: str = GRANULARITY_QUERY_MONTH(),
):
    def fetch_metrics(scope_branch, bucket_start, bucket_end):
        request = build_retrabalho_query_request(
            filial=scope_branch,
            data_inicio=bucket_start,
            data_fim=bucket_end,
            require_filial=False,
        )
        result = build_get_retrabalho_rework_cost_pct_use_case().execute(request)
        return {
            "rework_cost_pct": result.get("rework_cost_pct")
            if isinstance(result, dict)
            else getattr(result, "rework_cost_pct", None),
        }

    return _run_loss_series(
        metric="rework_cost_pct",
        operation_id="get_quality_rework_cost_pct_series",
        branch=branch,
        start_date=start_date,
        end_date=end_date,
        date_start=date_start,
        date_end=date_end,
        granularity=granularity,
        fetch_metrics=fetch_metrics,
    )

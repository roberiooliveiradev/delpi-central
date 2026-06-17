from fastapi import APIRouter, Query

from delpi_auth.authorization import require_any_permission

from app.application.security.api_delpi_permissions import KPI_HR_ACCESS

from app.composition.hr_composer import (
    build_hr_metrics_repository,
    build_hr_metrics_snapshot_service,
)
from app.core.responses import error_response
from app.interface.http.route_response_helpers import api_delpi_success
from app.infrastructure.persistence.portal_rh.portal_rh_base_repository import (
    PortalRhRepositoryError,
)
from app.infrastructure.providers.database.portal_rh_postgres_connection import (
    PortalRhDatabaseConfigError,
    PortalRhDatabaseConnectionError,
)
from app.interface.http.routes.hr.date_params import normalize_portal_rh_date
from app.application.services.strategic_indicators import dashboard_goal_source_keys as goal_keys
from app.application.services.strategic_indicators.dashboard_goals_service import (
    get_dashboard_goals_service,
)
from app.interface.http.kpi_field_labels import HR_FIELD_LABELS, kpi_fields
from app.interface.http.routes.shared.dashboard_goal_enrichment import enrich_dashboard_metric
from app.interface.http.openapi_agent_metadata_builder import OpenApiAgentMetadataBuilder
from app.utils.logger import log_error

router = APIRouter(prefix="/hr", tags=["Recursos Humanos"])


def _snapshot_payload(snapshot, *, start_date: str | None = None, end_date: str | None = None, branch: str | None = None) -> dict:
    payload = {
        "start_date": snapshot.start_date,
        "end_date": snapshot.end_date,
        "internal_satisfaction_pct": snapshot.internal_satisfaction_pct,
        "active_pdi_count": snapshot.active_pdi_count,
        "active_pdi_pct": snapshot.active_pdi_pct,
        "performance_reviews_completion_pct": snapshot.performance_reviews_completion_pct,
        "branches": [
            {
                "branch_code": branch.branch_code,
                "absenteeism_pct": branch.absenteeism_pct,
                "turnover_pct": branch.turnover_pct,
                "training_hours_per_collaborator": branch.training_hours_per_collaborator,
                "active_pdi_count": branch.active_pdi_count,
                "active_pdi_pct": branch.active_pdi_pct,
                "performance_reviews_completion_pct": branch.performance_reviews_completion_pct,
            }
            for branch in snapshot.branches
        ],
    }
    return get_dashboard_goals_service().attach_goals_index(
        payload,
        field_source_keys={
            "internal_satisfaction_pct": goal_keys.HR_SATISFACTION,
            "active_pdi_pct": goal_keys.HR_PDI,
            "active_pdi_count": goal_keys.HR_PDI,
            "performance_reviews_completion_pct": goal_keys.HR_PERFORMANCE_REVIEWS,
            "absenteeism_pct": goal_keys.HR_ABSENTEEISM,
            "turnover_pct": goal_keys.HR_TURNOVER,
            "training_hours_per_collaborator": goal_keys.HR_TRAINING_HOURS,
        },
        start_date=start_date,
        end_date=end_date,
        branch=branch,
    )


def _hr_query_dates(
    *,
    start_date: str | None,
    end_date: str | None,
) -> tuple[str | None, str | None]:
    return (
        normalize_portal_rh_date(start_date),
        normalize_portal_rh_date(end_date),
    )


@router.get(
    "/branches",
    **OpenApiAgentMetadataBuilder.from_contract(
        "list_hr_branches",
        path="/hr/branches",
    ),
)
@require_any_permission(KPI_HR_ACCESS)
def list_hr_branches():
    try:
        repository = build_hr_metrics_repository()
        branches = repository.list_active_branches()
        return api_delpi_success(
            {"branches": branches},
            operation_id="list_hr_branches",
            message="Filiais de RH listadas com sucesso.",
        )
    except PortalRhDatabaseConfigError as exc:
        log_error(f"Configuração Portal RH ausente: {exc}")
        return error_response(str(exc), status_code=503)
    except PortalRhDatabaseConnectionError as exc:
        log_error(f"Conexão Portal RH indisponível: {exc}")
        return error_response(
            "Não foi possível conectar ao banco do Portal RH. Verifique PORTAL_RH_DB_* no ambiente.",
            status_code=503,
        )
    except PortalRhRepositoryError as exc:
        log_error(f"Erro ao listar filiais de RH: {exc}")
        return error_response(str(exc), status_code=500)
    except Exception as exc:
        log_error(f"Erro ao listar filiais de RH: {exc}")
        return error_response(
            "Erro interno ao listar filiais de RH.",
            status_code=500,
        )


@router.get(
    "/snapshot",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_hr_snapshot",
        path="/hr/snapshot",
    ),
)
@require_any_permission(KPI_HR_ACCESS)
def get_hr_snapshot(
    branch: str | None = Query(default=None),
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
):
    try:
        service = build_hr_metrics_snapshot_service()
        snapshot = service.get_snapshot(
            start_date=normalize_portal_rh_date(start_date),
            end_date=normalize_portal_rh_date(end_date),
            branch=branch,
        )
        return api_delpi_success(
            _snapshot_payload(
                snapshot,
                start_date=normalize_portal_rh_date(start_date),
                end_date=normalize_portal_rh_date(end_date),
                branch=branch,
            ),
            operation_id="get_hr_snapshot",
            message="Indicadores de RH obtidos com sucesso.",
            fields=kpi_fields(HR_FIELD_LABELS),
        )
    except ValueError as exc:
        log_error(f"Erro de validação ao buscar RH: {exc}")
        return error_response(str(exc), status_code=400)
    except PortalRhDatabaseConfigError as exc:
        log_error(f"Configuração Portal RH ausente: {exc}")
        return error_response(str(exc), status_code=503)
    except PortalRhDatabaseConnectionError as exc:
        log_error(f"Conexão Portal RH indisponível: {exc}")
        return error_response(
            "Não foi possível conectar ao banco do Portal RH. Verifique PORTAL_RH_DB_* no ambiente.",
            status_code=503,
        )
    except PortalRhRepositoryError as exc:
        log_error(f"Erro ao buscar indicadores de RH: {exc}")
        return error_response(str(exc), status_code=500)
    except Exception as exc:
        log_error(f"Erro ao buscar indicadores de RH: {exc}")
        return error_response(
            "Erro interno ao buscar indicadores de RH.",
            status_code=500,
        )


@router.get(
    "/active-pdi-count",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_hr_active_pdi_count",
        path="/hr/active-pdi-count",
    ),
)
@require_any_permission(KPI_HR_ACCESS)
def get_hr_active_pdi_count(
    branch: str | None = Query(default=None),
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
):
    try:
        service = build_hr_metrics_snapshot_service()
        start, end = _hr_query_dates(start_date=start_date, end_date=end_date)
        data = service.get_active_pdi_count(
            start_date=start,
            end_date=end,
            branch=branch,
        )
        return api_delpi_success(
            enrich_dashboard_metric(
                data,
                source_key=goal_keys.HR_PDI,
                start_date=start,
                end_date=end,
                branch=branch,
            ),
            operation_id="get_hr_active_pdi_count",
            message="Contagem de PDIs ativos obtida com sucesso.",
            fields=kpi_fields(HR_FIELD_LABELS),
        )
    except ValueError as exc:
        log_error(f"Erro de validação ao buscar PDIs ativos: {exc}")
        return error_response(str(exc), status_code=400)
    except PortalRhDatabaseConfigError as exc:
        log_error(f"Configuração Portal RH ausente: {exc}")
        return error_response(str(exc), status_code=503)
    except PortalRhDatabaseConnectionError as exc:
        log_error(f"Conexão Portal RH indisponível: {exc}")
        return error_response(
            "Não foi possível conectar ao banco do Portal RH. Verifique PORTAL_RH_DB_* no ambiente.",
            status_code=503,
        )
    except PortalRhRepositoryError as exc:
        log_error(f"Erro ao buscar PDIs ativos: {exc}")
        return error_response(str(exc), status_code=500)
    except Exception as exc:
        log_error(f"Erro ao buscar PDIs ativos: {exc}")
        return error_response(
            "Erro interno ao buscar PDIs ativos.",
            status_code=500,
        )


@router.get(
    "/performance-reviews-completion",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_hr_performance_reviews_completion",
        path="/hr/performance-reviews-completion",
    ),
)
@require_any_permission(KPI_HR_ACCESS)
def get_hr_performance_reviews_completion(
    branch: str | None = Query(default=None),
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
):
    try:
        service = build_hr_metrics_snapshot_service()
        start, end = _hr_query_dates(start_date=start_date, end_date=end_date)
        data = service.get_performance_reviews_completion(
            start_date=start,
            end_date=end,
            branch=branch,
        )
        return api_delpi_success(
            enrich_dashboard_metric(
                data,
                source_key=goal_keys.HR_PERFORMANCE_REVIEWS,
                start_date=start,
                end_date=end,
                branch=branch,
            ),
            operation_id="get_hr_performance_reviews_completion",
            message="Percentual de avaliações de desempenho concluídas obtido com sucesso.",
            fields=kpi_fields(HR_FIELD_LABELS),
        )
    except ValueError as exc:
        log_error(f"Erro de validação ao buscar avaliações de desempenho: {exc}")
        return error_response(str(exc), status_code=400)
    except PortalRhDatabaseConfigError as exc:
        log_error(f"Configuração Portal RH ausente: {exc}")
        return error_response(str(exc), status_code=503)
    except PortalRhDatabaseConnectionError as exc:
        log_error(f"Conexão Portal RH indisponível: {exc}")
        return error_response(
            "Não foi possível conectar ao banco do Portal RH. Verifique PORTAL_RH_DB_* no ambiente.",
            status_code=503,
        )
    except PortalRhRepositoryError as exc:
        log_error(f"Erro ao buscar avaliações de desempenho: {exc}")
        return error_response(str(exc), status_code=500)
    except Exception as exc:
        log_error(f"Erro ao buscar avaliações de desempenho: {exc}")
        return error_response(
            "Erro interno ao buscar avaliações de desempenho.",
            status_code=500,
        )

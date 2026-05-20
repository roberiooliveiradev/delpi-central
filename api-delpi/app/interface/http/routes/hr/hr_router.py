from fastapi import APIRouter, Query

from delpi_auth.authorization import require_any_permission

from app.composition.hr_composer import (
    build_hr_metrics_repository,
    build_hr_metrics_snapshot_service,
)
from app.core.responses import error_response, success_response
from app.infrastructure.persistence.portal_rh.portal_rh_base_repository import (
    PortalRhRepositoryError,
)
from app.infrastructure.providers.database.portal_rh_postgres_connection import (
    PortalRhDatabaseConfigError,
    PortalRhDatabaseConnectionError,
)
from app.interface.http.routes.hr.date_params import normalize_portal_rh_date
from app.utils.logger import log_error

router = APIRouter(prefix="/hr", tags=["Recursos Humanos"])


def _snapshot_payload(snapshot) -> dict:
    return {
        "start_date": snapshot.start_date,
        "end_date": snapshot.end_date,
        "internal_satisfaction_pct": snapshot.internal_satisfaction_pct,
        "active_pdi_pct": snapshot.active_pdi_pct,
        "branches": [
            {
                "branch_code": branch.branch_code,
                "absenteeism_pct": branch.absenteeism_pct,
                "turnover_pct": branch.turnover_pct,
                "training_hours_per_collaborator": branch.training_hours_per_collaborator,
                "active_pdi_pct": branch.active_pdi_pct,
            }
            for branch in snapshot.branches
        ],
    }


@router.get("/branches")
@require_any_permission(["api-delpi.access", "dashboard-hr.view"])
def list_hr_branches():
    try:
        repository = build_hr_metrics_repository()
        branches = repository.list_active_branches()
        return success_response(
            data={"branches": branches},
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


@router.get("/snapshot")
@require_any_permission(["api-delpi.access", "dashboard-hr.view"])
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
        return success_response(
            data=_snapshot_payload(snapshot),
            message="Indicadores de RH obtidos com sucesso.",
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

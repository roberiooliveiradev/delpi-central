from fastapi import APIRouter, Query

from delpi_auth.authorization import require_any_permission
from app.core.responses import success_response, error_response
from app.utils.logger import log_error

from app.application.dto.production.production_request import ProductionRequest
from app.application.dto.financial.get_rol_request import GetRolRequest

from app.application.services.strategic_indicators import dashboard_goal_source_keys as goal_keys
from app.composition.production_composer import (
    build_get_direct_labor_cost_pct_use_case,
    build_get_production_cost_pct_use_case,
    build_get_depreciation_pct_use_case,
    build_get_overall_equipment_effectiveness_pct_use_case,
    build_get_on_time_delivery_pct_use_case,
    build_get_eficiencia_fabril_dashboard_use_case,
)
from app.interface.http.routes.shared.dashboard_goal_enrichment import enrich_dashboard_metric

router = APIRouter(prefix="/production", tags=["Produção"])


@router.get("/direct_labor_cost_pct")
@require_any_permission(["api-delpi.access", "dashboard-production.view"])
def get_direct_labor_cost_pct(
    branch: str | None = Query(default=None),
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
):
    try:
        use_case = build_get_direct_labor_cost_pct_use_case()

        request = ProductionRequest(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
        )

        request_rol = GetRolRequest(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
        )

        result = enrich_dashboard_metric(
            use_case.execute(request, request_rol),
            source_key=goal_keys.PRODUCTION_DIRECT_LABOR,
            start_date=start_date,
            end_date=end_date,
            branch=branch,
        )

        return success_response(
            data=result,
            message="Custo de mão de obra direta buscado com sucesso.",
        )

    except ValueError as exc:
        log_error(f"Erro de validação ao buscar custo de mão de obra direta: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao buscar custo de mão de obra direta: {exc}")
        return error_response(
            "Erro interno ao buscar custo de mão de obra direta.",
            status_code=500,
        )


@router.get("/production_cost_pct")
@require_any_permission(["api-delpi.access", "dashboard-production.view"])
def get_production_cost_pct(
    branch: str | None = Query(default=None),
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
):
    try:
        use_case = build_get_production_cost_pct_use_case()

        request = ProductionRequest(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
        )

        request_rol = GetRolRequest(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
        )

        result = enrich_dashboard_metric(
            use_case.execute(request, request_rol),
            source_key=goal_keys.PRODUCTION_COST,
            start_date=start_date,
            end_date=end_date,
            branch=branch,
        )

        return success_response(
            data=result,
            message="Custo de produção buscado com sucesso.",
        )

    except ValueError as exc:
        log_error(f"Erro de validação ao buscar custo de produção: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao buscar custo de produção: {exc}")
        return error_response(
            "Erro interno ao buscar custo de produção.",
            status_code=500,
        )


@router.get("/depreciation_pct")
@require_any_permission(["api-delpi.access", "dashboard-production.view"])
def get_depreciation_pct(
    branch: str | None = Query(default=None),
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
):
    try:
        use_case = build_get_depreciation_pct_use_case()

        request = ProductionRequest(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
        )

        request_rol = GetRolRequest(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
        )

        result = enrich_dashboard_metric(
            use_case.execute(request, request_rol),
            source_key=goal_keys.PRODUCTION_DEPRECIATION,
            start_date=start_date,
            end_date=end_date,
            branch=branch,
        )

        return success_response(
            data=result,
            message="Depreciação buscada com sucesso.",
        )

    except ValueError as exc:
        log_error(f"Erro de validação ao buscar depreciação: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao buscar depreciação: {exc}")
        return error_response(
            "Erro interno ao buscar depreciação.",
            status_code=500,
        )
    

@router.get("/overall_equipment_effectiveness_pct")
@require_any_permission(["api-delpi.access", "dashboard-production.view"])
def get_overall_equipment_effectiveness_pct(
    branch: str | None = Query(default=None),
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
):
    try:
        use_case = build_get_overall_equipment_effectiveness_pct_use_case()

        request = ProductionRequest(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
        )

        result = enrich_dashboard_metric(
            use_case.execute(request),
            source_key=goal_keys.PRODUCTION_OEE,
            start_date=start_date,
            end_date=end_date,
            branch=branch,
        )

        return success_response(
            data=result,
            message="Eficiência geral dos equipamentos buscada com sucesso.",
        )

    except ValueError as exc:
        log_error(f"Erro de validação ao buscar eficiência geral dos equipamentos: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao buscar eficiência geral dos equipamentos: {exc}")
        return error_response(
            "Erro interno ao buscar eficiência geral dos equipamentos.",
            status_code=500,
        )
    

@router.get("/on_time_delivery_pct")
@require_any_permission(["api-delpi.access", "dashboard-production.view"])
def get_on_time_delivery_pct(
    branch: str | None = Query(default=None),
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
):
    try:
        use_case = build_get_on_time_delivery_pct_use_case()

        request = ProductionRequest(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
        )

        result = enrich_dashboard_metric(
            use_case.execute(request),
            source_key=goal_keys.PRODUCTION_OTD,
            start_date=start_date,
            end_date=end_date,
            branch=branch,
        )

        return success_response(
            data=result,
            message="On-Time Delivery buscado com sucesso.",
        )

    except ValueError as exc:
        log_error(f"Erro de validação ao buscar On-Time Delivery: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao buscar On-Time Delivery: {exc}")
        return error_response(
            "Erro interno ao buscar On-Time Delivery.",
            status_code=500,
        )


@router.get("/eficiencia-fabril/dashboard")
@require_any_permission(
    [
        "api-delpi.access",
        "eficiencia-fabril.view",
        "dashboard-production.view",
    ]
)
def get_eficiencia_fabril_dashboard(
    date_start: str | None = Query(default=None),
    date_end: str | None = Query(default=None),
    branch: str | None = Query(default=None),
    employee: str | None = Query(default=None),
    work_center: str | None = Query(default=None),
    cost_center: str | None = Query(default=None),
    status_ok_only: bool = Query(default=True),
    page: int = Query(default=1, ge=1),
    page_size: int | None = Query(default=None, ge=1, le=500),
):
    try:
        use_case = build_get_eficiencia_fabril_dashboard_use_case()
        result = use_case.execute(
            date_start=date_start,
            date_end=date_end,
            branch=branch,
            employee=employee,
            work_center=work_center,
            cost_center=cost_center,
            status_ok_only=status_ok_only,
            page=page,
            page_size=page_size,
        )

        return success_response(
            data=result.to_dict(),
            message="Dashboard de eficiência fabril carregado com sucesso.",
        )

    except ValueError as exc:
        log_error(f"Erro de validação no dashboard eficiência fabril: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao carregar dashboard eficiência fabril: {exc}")
        return error_response(
            "Erro interno ao carregar dashboard de eficiência fabril.",
            status_code=500,
        )
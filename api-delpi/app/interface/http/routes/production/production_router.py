from fastapi import APIRouter, Query

from delpi_auth.authorization import require_permission
from app.core.responses import success_response, error_response
from app.utils.logger import log_error

from app.application.dto.production.production_request import ProductionRequest
from app.application.dto.financial.get_rol_request import GetRolRequest

from app.composition.production_composer import (
    build_get_direct_labor_cost_pct_use_case,
    build_get_production_cost_pct_use_case,
    build_get_depreciation_pct_use_case,
    build_get_overall_equipment_effectiveness_pct_use_case,
    build_get_on_time_delivery_pct_use_case,
)

router = APIRouter(prefix="/production", tags=["Produção"])


@router.get("/direct_labor_cost_pct")
@require_permission("api-delpi.access")
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

        result = use_case.execute(request, request_rol)

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
@require_permission("api-delpi.access")
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

        result = use_case.execute(request, request_rol)

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
@require_permission("api-delpi.access")
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

        result = use_case.execute(request, request_rol)

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
@require_permission("api-delpi.access")
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

        result = use_case.execute(request)


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
@require_permission("api-delpi.access")
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

        result = use_case.execute(request)

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
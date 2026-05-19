from fastapi import APIRouter, Query

from delpi_auth.authorization import require_any_permission
from app.core.responses import success_response, error_response
from app.utils.logger import log_error

from app.application.dto.supplies.get_cpv_request import GetCPVRequest
from app.application.dto.supplies.get_otd_request import GetOTDRequest
from app.application.dto.supplies.get_stock_value_request import GetStockValueRequest
from app.application.dto.supplies.get_inventory_turnover_request import (
    GetInventoryTurnoverRequest,
)

from app.interface.http.openapi_agent_metadata import SUPPLIES_STOCK_VALUE
from app.composition.supplies_composer import (
    build_get_cpv_use_case,
    build_get_otd_use_case,
    build_get_stock_value_use_case,
    build_get_inventory_turnover_use_case,
)

router = APIRouter(prefix="/supplies", tags=["Suprimentos"])


@router.get("/cpv")
@require_any_permission(["api-delpi.access", "dashboard-supplies.view"])
def get_cpv(
    branch: str | None = Query(default=None),
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    top_limit: int = Query(default=5, ge=1, le=20),
):
    try:
        use_case = build_get_cpv_use_case()

        request = GetCPVRequest(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
            top_limit=top_limit,
        )

        result = use_case.execute(request)

        return success_response(
            data=result,
            message="CPV buscado com sucesso.",
        )

    except ValueError as exc:
        log_error(f"Erro de validação ao buscar CPV: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao buscar CPV: {exc}")
        return error_response(
            "Erro interno ao buscar CPV.",
            status_code=500,
        )
    

@router.get("/otd")
@require_any_permission(["api-delpi.access", "dashboard-supplies.view"])
def get_otd(
    branch: str | None = Query(default=None),
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    top_limit: int = Query(default=5, ge=1, le=20),
    details_limit: int = Query(default=20, ge=1, le=100),
):
    try:
        use_case = build_get_otd_use_case()

        request = GetOTDRequest(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
            top_limit=top_limit,
            details_limit=details_limit,
        )

        result = use_case.execute(request)

        return success_response(
            data=result,
            message="OTD buscado com sucesso.",
        )

    except ValueError as exc:
        log_error(f"Erro de validação ao buscar OTD: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao buscar OTD: {exc}")
        return error_response(
            "Erro interno ao buscar OTD.",
            status_code=500,
        )
    

@router.get("/stock-value", **SUPPLIES_STOCK_VALUE)
@require_any_permission(["api-delpi.access", "dashboard-supplies.view"])
def get_stock_value(
    branch: str | None = Query(default=None),
    location: str | None = Query(default=None),
    top_limit: int = Query(default=10, ge=1, le=50),
):
    try:
        use_case = build_get_stock_value_use_case()

        request = GetStockValueRequest(
            branch=branch,
            location=location,
            top_limit=top_limit,
        )

        result = use_case.execute(request)

        return success_response(
            data=result,
            message="Valor total de estoque buscado com sucesso.",
        )

    except ValueError as exc:
        log_error(f"Erro de validação ao buscar valor total de estoque: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao buscar valor total de estoque: {exc}")
        return error_response(
            "Erro interno ao buscar valor total de estoque.",
            status_code=500,
        )
    

@router.get("/inventory-turnover")
@require_any_permission(["api-delpi.access", "dashboard-supplies.view"])
def get_inventory_turnover(
    branch: str | None = Query(default=None),
    location: str | None = Query(default=None),
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    strict_idd_period: bool = Query(default=False),
):
    try:
        use_case = build_get_inventory_turnover_use_case()

        request = GetInventoryTurnoverRequest(
            branch=branch,
            location=location,
            start_date=start_date,
            end_date=end_date,
            strict_idd_period=strict_idd_period,
        )

        result = use_case.execute(request)

        return success_response(
            data=result,
            message="Giro de estoque buscado com sucesso.",
        )

    except ValueError as exc:
        log_error(f"Erro de validação ao buscar giro de estoque: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao buscar giro de estoque: {exc}")
        return error_response(
            "Erro interno ao buscar giro de estoque.",
            status_code=500,
        )
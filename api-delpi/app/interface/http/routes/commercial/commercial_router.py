from fastapi import APIRouter, Query
from typing import Optional

from delpi_auth.authorization import require_any_permission
from app.core.responses import success_response, error_response
from app.utils.logger import log_error

from app.application.dto.commercial.commercial_target_request import CommercialTargetRequest
from app.application.dto.commercial.sales_conversion_rate_request import SalesConversionRateRequest
from app.application.dto.commercial.new_clients_average_request import NewClientsAverageRequest
from app.application.dto.commercial.new_clients_rol_pct_request import NewClientsRolPctRequest
from app.application.dto.commercial.commercial_rol_series_request import (
    CommercialRolSeriesRequest,
)
from app.application.dto.commercial.new_business_rol_pct_request import NewBusinessRolPctRequest
from app.application.dto.commercial.sales_order_otd_request import SalesOrderOtdRequest
from app.composition.commercial_composer import (
    build_get_head_office_rol_target_pct_use_case,
    build_get_branch_rol_target_pct_use_case,
    build_get_sales_conversion_rate_use_case,
    build_get_new_clients_average_use_case,
    build_get_new_clients_rol_pct_use_case,
    build_get_commercial_rol_series_use_case,
    build_get_sales_order_otd_use_case,
    build_get_new_business_rol_pct_use_case,
)


router = APIRouter(prefix="/commercial", tags=["Comercial"])


@router.get("/head_office_rol_target_pct")
@require_any_permission(["api-delpi.access", "dashboard-commercial.view"])
def get_head_office_rol_target_pct(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    try:
        use_case = build_get_head_office_rol_target_pct_use_case()

        request = CommercialTargetRequest(
            branch="01",
            start_date=start_date,
            end_date=end_date,
        )

        result = use_case.execute(request)

        return success_response(
            data=result,
            message="Head office ROL target percentage fetched successfully.",
        )

    except ValueError as exc:
        log_error(f"Validation error while fetching head office ROL target percentage: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Error while fetching head office ROL target percentage: {exc}")
        return error_response(
            "Internal error while fetching head office ROL target percentage.",
            status_code=500,
        )


@router.get("/branch_rol_target_pct")
@require_any_permission(["api-delpi.access", "dashboard-commercial.view"])
def get_branch_rol_target_pct(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    try:
        use_case = build_get_branch_rol_target_pct_use_case()

        request = CommercialTargetRequest(
            branch="02",
            start_date=start_date,
            end_date=end_date,
        )

        result = use_case.execute(request)

        return success_response(
            data=result,
            message="Branch ROL target percentage fetched successfully.",
        )

    except ValueError as exc:
        log_error(f"Validation error while fetching branch ROL target percentage: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Error while fetching branch ROL target percentage: {exc}")
        return error_response(
            "Internal error while fetching branch ROL target percentage.",
            status_code=500,
        )
    

@router.get("/rol/series")
@require_any_permission(["api-delpi.access", "dashboard-commercial.view"])
def get_commercial_rol_series(
    granularity: str = Query(..., min_length=3, max_length=10),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    try:
        request = CommercialRolSeriesRequest(
            granularity=granularity,
            date_start=start_date,
            date_end=end_date,
        )

        use_case = build_get_commercial_rol_series_use_case()
        result = use_case.execute(request)

        return success_response(
            data=result.to_dict(),
            message="Commercial ROL series fetched successfully.",
        )

    except ValueError as exc:
        log_error(f"Validation error while fetching commercial ROL series: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Error while fetching commercial ROL series: {exc}")
        return error_response(
            "Internal error while fetching commercial ROL series.",
            status_code=500,
        )


@router.get("/closing-rate")
@require_any_permission(["api-delpi.access", "dashboard-commercial.view"])
def get_sales_conversion_rate(
    branch: Optional[str] = Query(None, min_length=2, max_length=2),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    try:
        use_case = build_get_sales_conversion_rate_use_case()

        request = SalesConversionRateRequest(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
        )

        result = use_case.execute(request)

        return success_response(
            data=result,
            message="Sales Conversion Rate fetched successfully.",
        )

    except ValueError as exc:
        log_error(f"Validation error while fetching Sales Conversion Rate: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Error while fetching Sales Conversion Rate: {exc}")
        return error_response(
            "Internal error while fetching Sales Conversion Rate.",
            status_code=500,
        )
    

@router.get("/new-clients-average")
@require_any_permission(["api-delpi.access", "dashboard-commercial.view"])
def get_new_clients_average(
    branch: Optional[str] = Query(None, min_length=2, max_length=2),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    try:
        use_case = build_get_new_clients_average_use_case()

        request = NewClientsAverageRequest(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
        )

        result = use_case.execute(request)

        return success_response(
            data=result,
            message="Number of New Clients (Monthly Average) fetched successfully.",
        )

    except ValueError as exc:
        log_error(f"Validation error while fetching Number of New Clients (Monthly Average): {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Error while fetching Number of New Clients (Monthly Average): {exc}")
        return error_response(
            "Internal error while fetching Number of New Clients (Monthly Average).",
            status_code=500,
        )
    

@router.get("/sales-order-otd")
@require_any_permission(["api-delpi.access", "dashboard-commercial.view"])
def get_sales_order_otd(
    branch: Optional[str] = Query(None, min_length=2, max_length=2),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    try:
        use_case = build_get_sales_order_otd_use_case()

        request = SalesOrderOtdRequest(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
        )

        result = use_case.execute(request)

        return success_response(
            data=result,
            message="Sales order on-time delivery percentage fetched successfully.",
        )

    except ValueError as exc:
        log_error(f"Validation error while fetching sales order OTD: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Error while fetching sales order OTD: {exc}")
        return error_response(
            "Internal error while fetching sales order OTD.",
            status_code=500,
        )


@router.get("/new-business-rol-pct")
@require_any_permission(["api-delpi.access", "dashboard-commercial.view"])
def get_new_business_rol_pct(
    branch: Optional[str] = Query(None, min_length=2, max_length=2),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    try:
        use_case = build_get_new_business_rol_pct_use_case()

        request = NewBusinessRolPctRequest(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
        )

        result = use_case.execute(request)

        return success_response(
            data=result,
            message="New business share of net operating revenue fetched successfully.",
        )

    except ValueError as exc:
        log_error(f"Validation error while fetching new business ROL %: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Error while fetching new business ROL %: {exc}")
        return error_response(
            "Internal error while fetching new business ROL %.",
            status_code=500,
        )


@router.get("/new-clients-rol-pct")
@require_any_permission(["api-delpi.access", "dashboard-commercial.view"])
def get_new_clients_rol_pct(
    branch: Optional[str] = Query(None, min_length=2, max_length=2),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    try:
        use_case = build_get_new_clients_rol_pct_use_case()

        request = NewClientsRolPctRequest(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
        )

        result = use_case.execute(request)

        return success_response(
            data=result,
            message="% of Net Operating Revenue from New Clients fetched successfully.",
        )

    except ValueError as exc:
        log_error(f"Validation error while fetching % of Net Operating Revenue from New Clients: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Error while fetching % of Net Operating Revenue from New Clients: {exc}")
        return error_response(
            "Internal error while fetching % of Net Operating Revenue from New Clients.",
            status_code=500,
        )

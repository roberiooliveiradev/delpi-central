from fastapi import APIRouter, Query
from typing import Optional

from delpi_auth.authorization import require_permission
from app.core.responses import success_response, error_response
from app.utils.logger import log_error

from app.application.dto.commercial.commercial_target_request import CommercialTargetRequest
from app.composition.commercial_composer import (
    build_get_head_office_rol_target_pct_use_case,
    build_get_branch_rol_target_pct_use_case,
)


router = APIRouter(prefix="/commercial", tags=["Commercial"])


@router.get("/head_office_rol_target_pct")
@require_permission("api-delpi.access")
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
@require_permission("api-delpi.access")
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
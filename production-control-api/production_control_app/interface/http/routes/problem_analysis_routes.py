from __future__ import annotations

from fastapi import APIRouter, Query, Request

from production_control_app.composition.pc_composer import build_problem_analysis_service
from production_control_app.core.responses import fail, ok
from production_control_app.domain.errors import (
    BranchAccessDenied,
    DelpiGatewayError,
    DetectorNotFound,
    InvalidBranch,
)
from production_control_app.interface.http.auth_http import resolve_user

router = APIRouter(tags=["Problem analysis"])


@router.get("/problem-analysis")
def get_problem_analysis(
    request: Request,
    branch: str = Query(..., description="Filial TOTVS (01 ou 02)"),
):
    user = resolve_user(request)
    try:
        data = build_problem_analysis_service().list_detectors(user, branch=branch)
    except InvalidBranch as exc:
        return fail(str(exc), 422)
    except BranchAccessDenied as exc:
        return fail(str(exc), 403)
    except PermissionError as exc:
        return fail(str(exc), 403)
    except DelpiGatewayError as exc:
        return fail(str(exc), 502)
    return ok(data)


@router.get("/problem-analysis/{detector_id}")
def get_problem_analysis_detector(
    request: Request,
    detector_id: str,
    branch: str = Query(..., description="Filial TOTVS (01 ou 02)"),
    page: int = Query(1, ge=1),
    pageSize: int | None = Query(None, alias="pageSize", ge=1, le=200),
):
    user = resolve_user(request)
    try:
        data = build_problem_analysis_service().detector_items(
            user,
            branch=branch,
            detector_id=detector_id,
            page=page,
            page_size=pageSize,
        )
    except InvalidBranch as exc:
        return fail(str(exc), 422)
    except BranchAccessDenied as exc:
        return fail(str(exc), 403)
    except PermissionError as exc:
        return fail(str(exc), 403)
    except DetectorNotFound as exc:
        return fail(str(exc), 404)
    except DelpiGatewayError as exc:
        return fail(str(exc), 502)
    return ok(data)

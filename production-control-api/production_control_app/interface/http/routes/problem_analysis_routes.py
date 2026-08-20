from __future__ import annotations

from fastapi import APIRouter, Query, Request

from production_control_app.composition.pc_composer import build_problem_analysis_service
from production_control_app.core.responses import fail, ok
from production_control_app.domain.errors import BranchAccessDenied, DelpiGatewayError, InvalidBranch
from production_control_app.interface.http.auth_http import resolve_user

router = APIRouter(tags=["Problem analysis"])


@router.get("/problem-analysis")
def get_problem_analysis(
    request: Request,
    branch: str = Query(..., description="Filial TOTVS (01 ou 02)"),
    issueId: str | None = Query(None, alias="issueId"),
):
    user = resolve_user(request)
    try:
        data = build_problem_analysis_service().build(
            user,
            branch=branch,
            issue_id=issueId,
        )
    except InvalidBranch as exc:
        return fail(str(exc), 422)
    except BranchAccessDenied as exc:
        return fail(str(exc), 403)
    except PermissionError as exc:
        return fail(str(exc), 403)
    except DelpiGatewayError as exc:
        return fail(str(exc), 502)
    return ok(data)

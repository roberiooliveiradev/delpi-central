from __future__ import annotations

from fastapi import APIRouter, Query, Request

from production_control_app.composition.pc_composer import build_reports_service
from production_control_app.core.responses import fail, ok
from production_control_app.domain.errors import BranchAccessDenied, DelpiGatewayError, InvalidBranch
from production_control_app.interface.http.auth_http import resolve_user

router = APIRouter(tags=["Reports"])


@router.get("/reports")
def get_reports_catalog(
    request: Request,
    branch: str = Query(..., description="Filial TOTVS (01 ou 02)"),
):
    user = resolve_user(request)
    try:
        data = build_reports_service().list_catalog(user, branch=branch)
    except InvalidBranch as exc:
        return fail(str(exc), 422)
    except BranchAccessDenied as exc:
        return fail(str(exc), 403)
    except PermissionError as exc:
        return fail(str(exc), 403)
    return ok(data)


@router.get("/reports/stock-balances")
def get_stock_balances_report(
    request: Request,
    branch: str = Query(..., description="Filial TOTVS (01 ou 02)"),
    search: str = Query("", description="Código ou descrição do produto"),
    sort: str | None = Query(None, description="Ordenação da listagem"),
    page: int = Query(1, ge=1),
    pageSize: int | None = Query(None, alias="pageSize", ge=1, le=5000),
    refresh: bool = Query(False, description="Ignora o cache e relê a api-delpi"),
):
    user = resolve_user(request)
    try:
        data = build_reports_service().stock_balances(
            user,
            branch=branch,
            search=search,
            sort=sort,
            page=page,
            page_size=pageSize,
            refresh=refresh,
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

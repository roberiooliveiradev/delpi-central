from __future__ import annotations

from fastapi import APIRouter, Query, Request

from production_control_app.composition.pc_composer import build_demand_service
from production_control_app.core.responses import fail, ok
from production_control_app.domain.errors import (
    BranchAccessDenied,
    DelpiGatewayError,
    InvalidBranch,
)
from production_control_app.interface.http.auth_http import resolve_user

router = APIRouter(tags=["Demand"])


@router.get("/demand")
def get_demand(
    request: Request,
    branch: str = Query(..., description="Filial TOTVS (01 ou 02)"),
    search: str = Query("", description="Cliente, pedido, pedido do cliente ou produto"),
    status: str = Query("", description="late | at_risk | covered_by_order | covered_by_stock"),
    dueFrom: str | None = Query(None, alias="dueFrom"),
    dueTo: str | None = Query(None, alias="dueTo"),
    sort: str | None = Query(None),
    direction: str = Query("asc"),
    page: int = Query(1, ge=1),
    pageSize: int | None = Query(None, alias="pageSize", ge=1, le=200),
    refresh: bool = Query(False, description="Ignora o cache e relê a api-delpi"),
):
    user = resolve_user(request)
    try:
        data = build_demand_service().list_demand(
            user,
            branch=branch,
            search=search,
            status=status,
            due_from=dueFrom,
            due_to=dueTo,
            sort=sort,
            direction=direction,
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

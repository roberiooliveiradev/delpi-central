from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Body, Query, Request
from pydantic import BaseModel, Field

from production_control_app.composition.pc_composer import build_reports_service
from production_control_app.core.responses import fail, ok
from production_control_app.domain.errors import BranchAccessDenied, DelpiGatewayError, InvalidBranch
from production_control_app.interface.http.auth_http import resolve_user

router = APIRouter(tags=["Reports"])


class EmailScheduleBody(BaseModel):
    hour: int = Field(ge=0, le=23)
    minute: int = Field(ge=0, le=59)
    enabled: bool = True


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


@router.get("/reports/production-orders")
def get_production_orders_report(
    request: Request,
    branch: str = Query(..., description="Filial TOTVS (01 ou 02)"),
    opKey: str = Query("", description="Chave ou número da OP"),
    productCode: str = Query("", description="Código do produto"),
    motherOnly: str | None = Query("all", description="yes, no ou all"),
    openOnly: str | None = Query("yes", description="yes, no ou all"),
    deliveryStart: str | None = Query(None, description="Início da entrega prevista (YYYY-MM-DD)"),
    deliveryEnd: str | None = Query(None, description="Fim da entrega prevista (YYYY-MM-DD)"),
    actualEndStart: str | None = Query(None, description="Início do fim real (YYYY-MM-DD)"),
    actualEndEnd: str | None = Query(None, description="Fim do fim real (YYYY-MM-DD)"),
    sort: str | None = Query(None, description="Ordenação da listagem"),
    page: int = Query(1, ge=1),
    pageSize: int | None = Query(None, alias="pageSize", ge=1, le=200),
):
    user = resolve_user(request)
    try:
        data = build_reports_service().production_orders(
            user,
            branch=branch,
            op_key=opKey,
            product_code=productCode,
            mother_only=motherOnly,
            open_only=openOnly,
            delivery_start=deliveryStart,
            delivery_end=deliveryEnd,
            actual_end_start=actualEndStart,
            actual_end_end=actualEndEnd,
            sort=sort,
            page=page,
            page_size=pageSize,
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


@router.get("/reports/stock-balances/email-schedule")
def get_stock_balances_email_schedule(
    request: Request,
    branch: str = Query(..., description="Filial TOTVS (01 ou 02)"),
):
    user = resolve_user(request)
    try:
        data = build_reports_service().get_email_schedule(user, branch=branch)
    except InvalidBranch as exc:
        return fail(str(exc), 422)
    except BranchAccessDenied as exc:
        return fail(str(exc), 403)
    except PermissionError as exc:
        return fail(str(exc), 403)
    except DelpiGatewayError as exc:
        upstream = exc.status_code if isinstance(exc.status_code, int) else None
        status = upstream if upstream and 400 <= upstream < 600 else 502
        return fail(str(exc), status)
    return ok(data)


@router.put("/reports/stock-balances/email-schedule")
def put_stock_balances_email_schedule(
    request: Request,
    branch: str = Query(..., description="Filial TOTVS (01 ou 02)"),
    body: Annotated[EmailScheduleBody, Body(...)] = ...,
):
    user = resolve_user(request)
    try:
        data = build_reports_service().upsert_email_schedule(
            user,
            branch=branch,
            hour=body.hour,
            minute=body.minute,
            enabled=body.enabled,
        )
    except InvalidBranch as exc:
        return fail(str(exc), 422)
    except BranchAccessDenied as exc:
        return fail(str(exc), 403)
    except PermissionError as exc:
        return fail(str(exc), 403)
    except DelpiGatewayError as exc:
        upstream = exc.status_code if isinstance(exc.status_code, int) else None
        status = upstream if upstream and 400 <= upstream < 600 else 502
        return fail(str(exc), status)
    return ok(data)

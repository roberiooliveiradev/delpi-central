from __future__ import annotations

from fastapi import APIRouter, Body, Path, Query, Request
from pydantic import BaseModel, Field

from production_control_app.composition.pc_composer import build_line_feeder_service
from production_control_app.core.responses import fail, ok
from production_control_app.domain.errors import (
    BranchAccessDenied,
    DelpiGatewayError,
    InvalidBranch,
    SnapshotNotFound,
)
from production_control_app.interface.http.auth_http import resolve_user

router = APIRouter(tags=["Line feeder"])


class PickPlanCreateBody(BaseModel):
    branch: str = Field(..., min_length=2, max_length=2)
    cutoff_date: str = Field(..., alias="cutoffDate", min_length=10, max_length=10)
    cutoff_time: str | None = Field(default=None, alias="cutoffTime", max_length=5)
    work_center: str | None = Field(default=None, alias="workCenter", max_length=40)

    model_config = {"populate_by_name": True}


class PickItemStatusBody(BaseModel):
    branch: str = Field(..., min_length=2, max_length=2)
    status: str = Field(..., min_length=1, max_length=16)

    model_config = {"populate_by_name": True}


class PickPlanCloseBody(BaseModel):
    branch: str = Field(..., min_length=2, max_length=2)

    model_config = {"populate_by_name": True}


def _handle_line_feeder_errors(exc: Exception):
    if isinstance(exc, InvalidBranch):
        return fail(str(exc), 422)
    if isinstance(exc, BranchAccessDenied):
        return fail(str(exc), 403)
    if isinstance(exc, PermissionError):
        return fail(str(exc), 403)
    if isinstance(exc, SnapshotNotFound):
        return fail(str(exc), 404)
    if isinstance(exc, LookupError):
        return fail(str(exc), 404)
    if isinstance(exc, ValueError):
        return fail(str(exc), 422)
    if isinstance(exc, DelpiGatewayError):
        return fail(str(exc), 502)
    raise exc


@router.get("/line-feeder/requirements")
def get_line_feeder_requirements(
    request: Request,
    branch: str = Query(..., description="Filial TOTVS (01 ou 02)"),
    cutoff_date: str = Query(
        ...,
        alias="cutoffDate",
        description="Data do corte (YYYY-MM-DD)",
    ),
    cutoff_time: str | None = Query(
        default=None,
        alias="cutoffTime",
        description="Hora do corte (HH:MM); vazio considera o dia inteiro",
    ),
    work_center: str | None = Query(
        default=None,
        alias="workCenter",
        description="Recorte por bancada; o rateio do saldo continua global",
    ),
    status: str | None = Query(
        default=None,
        description="covered, to_pick, at_risk, unknown ou all",
    ),
    refresh: bool = Query(False, description="Ignora o cache e relê a api-delpi"),
):
    """Material que precisa estar nas bancadas até o horário do corte."""
    user = resolve_user(request)
    try:
        data = build_line_feeder_service().get_requirements(
            user,
            branch=branch,
            cutoff_date=cutoff_date,
            cutoff_time=cutoff_time,
            work_center=work_center,
            status=status,
            refresh=refresh,
        )
    except Exception as exc:
        return _handle_line_feeder_errors(exc)
    return ok(data)


@router.post("/line-feeder/pick-plans")
def create_line_feeder_pick_plan(
    request: Request,
    body: PickPlanCreateBody = Body(...),
):
    """Congela o que falta entregar no corte como lista de coleta."""
    user = resolve_user(request)
    try:
        data = build_line_feeder_service().create_pick_plan(
            user,
            branch=body.branch,
            cutoff_date=body.cutoff_date,
            cutoff_time=body.cutoff_time,
            work_center=body.work_center,
        )
    except Exception as exc:
        return _handle_line_feeder_errors(exc)
    return ok(data)


@router.get("/line-feeder/pick-plans")
def list_line_feeder_pick_plans(
    request: Request,
    branch: str = Query(..., description="Filial TOTVS (01 ou 02)"),
    status: str | None = Query(default=None, description="open ou closed"),
    limit: int = Query(50, ge=1, le=200),
):
    user = resolve_user(request)
    try:
        data = build_line_feeder_service().list_pick_plans(
            user,
            branch=branch,
            status=status,
            limit=limit,
        )
    except Exception as exc:
        return _handle_line_feeder_errors(exc)
    return ok(data)


@router.get("/line-feeder/pick-plans/{plan_id}")
def get_line_feeder_pick_plan(
    request: Request,
    plan_id: str = Path(..., description="Identificador da lista de coleta"),
    branch: str = Query(..., description="Filial TOTVS (01 ou 02)"),
):
    user = resolve_user(request)
    try:
        data = build_line_feeder_service().get_pick_plan(
            user,
            branch=branch,
            plan_id=plan_id,
        )
    except Exception as exc:
        return _handle_line_feeder_errors(exc)
    return ok(data)


@router.patch("/line-feeder/pick-plans/{plan_id}/items/{item_id}")
def update_line_feeder_pick_item(
    request: Request,
    plan_id: str = Path(..., description="Identificador da lista de coleta"),
    item_id: str = Path(..., description="Identificador do item"),
    body: PickItemStatusBody = Body(...),
):
    """Avança ou volta o item: pending, picked ou delivered."""
    user = resolve_user(request)
    try:
        data = build_line_feeder_service().update_pick_item_status(
            user,
            branch=body.branch,
            plan_id=plan_id,
            item_id=item_id,
            status=body.status,
        )
    except Exception as exc:
        return _handle_line_feeder_errors(exc)
    return ok(data)


@router.post("/line-feeder/pick-plans/{plan_id}/close")
def close_line_feeder_pick_plan(
    request: Request,
    plan_id: str = Path(..., description="Identificador da lista de coleta"),
    body: PickPlanCloseBody = Body(...),
):
    user = resolve_user(request)
    try:
        data = build_line_feeder_service().close_pick_plan(
            user,
            branch=body.branch,
            plan_id=plan_id,
        )
    except Exception as exc:
        return _handle_line_feeder_errors(exc)
    return ok(data)

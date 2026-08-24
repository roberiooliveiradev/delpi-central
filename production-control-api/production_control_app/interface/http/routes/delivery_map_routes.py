from __future__ import annotations

from fastapi import APIRouter, Body, Query, Request
from pydantic import BaseModel, Field

from production_control_app.composition.pc_composer import build_delivery_map_service
from production_control_app.core.responses import fail, ok
from production_control_app.domain.errors import (
    BranchAccessDenied,
    DelpiGatewayError,
    InvalidBranch,
    SnapshotNotFound,
)
from production_control_app.interface.http.auth_http import resolve_user

router = APIRouter(tags=["Delivery map"])


class DeliveryMapOverrideUpdate(BaseModel):
    production_order: str = Field(..., min_length=1, max_length=30)
    mp_ok: bool | None = None
    work_center: str | None = Field(default=None, max_length=40)


class DeliveryMapOverridesBody(BaseModel):
    updates: list[DeliveryMapOverrideUpdate] = Field(default_factory=list)


def _handle_errors(exc: Exception):
    if isinstance(exc, InvalidBranch):
        return fail(str(exc), 422)
    if isinstance(exc, BranchAccessDenied):
        return fail(str(exc), 403)
    if isinstance(exc, PermissionError):
        return fail(str(exc), 403)
    if isinstance(exc, SnapshotNotFound):
        return fail(str(exc), 404)
    if isinstance(exc, DelpiGatewayError):
        return fail(str(exc), 502)
    raise exc


@router.get("/delivery-map")
def get_delivery_map(
    request: Request,
    branch: str = Query(..., description="Filial TOTVS (01 ou 02)"),
    search: str = Query("", description="Filtra OP, produto ou observação"),
):
    user = resolve_user(request)
    try:
        data = build_delivery_map_service().build(user, branch=branch, search=search)
    except Exception as exc:
        return _handle_errors(exc)
    return ok(data)


@router.post("/delivery-map/refresh")
def refresh_delivery_map(
    request: Request,
    branch: str = Query(..., description="Filial TOTVS (01 ou 02)"),
    search: str = Query("", description="Filtro de leitura após o refresh"),
):
    user = resolve_user(request)
    try:
        data = build_delivery_map_service().refresh(user, branch=branch, search=search)
    except Exception as exc:
        return _handle_errors(exc)
    return ok(data, message="Mapa de entrega atualizado com os dados do TOTVS.")


@router.get("/delivery-map/progress")
def get_delivery_map_progress(
    request: Request,
    branch: str = Query(..., description="Filial TOTVS (01 ou 02)"),
    orders: str = Query(
        "",
        description="Lista de OPs mãe separadas por vírgula (progresso por conjunto)",
    ),
):
    user = resolve_user(request)
    production_orders = [
        part.strip()
        for part in str(orders or "").split(",")
        if part.strip()
    ]
    try:
        data = build_delivery_map_service().build_progress(
            user,
            branch=branch,
            production_orders=production_orders,
        )
    except Exception as exc:
        return _handle_errors(exc)
    return ok(data)


@router.patch("/delivery-map/overrides")
def patch_delivery_map_overrides(
    request: Request,
    branch: str = Query(..., description="Filial TOTVS (01 ou 02)"),
    search: str = Query("", description="Filtro de leitura após salvar"),
    body: DeliveryMapOverridesBody = Body(...),
):
    user = resolve_user(request)
    updates = [item.model_dump(exclude_none=True) for item in body.updates]
    try:
        data = build_delivery_map_service().patch_overrides(
            user,
            branch=branch,
            updates=updates,
            search=search,
        )
    except Exception as exc:
        return _handle_errors(exc)
    return ok(data)

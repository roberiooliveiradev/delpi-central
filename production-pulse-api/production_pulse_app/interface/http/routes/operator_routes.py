from __future__ import annotations

from urllib.parse import urlencode
from uuid import UUID

from fastapi import APIRouter, Query, Request
from fastapi.responses import RedirectResponse

from production_pulse_app.application.services.device_command_service import DeviceCommandService
from production_pulse_app.application.services.device_service import DeviceNotFoundError, DeviceService
from production_pulse_app.application.services.operator_placement_service import OperatorPlacementService
from production_pulse_app.core.responses import success
from production_pulse_app.domain.services.device_serialization_service import parse_device_id
from production_pulse_app.interface.http.rbac_http import (
    guard_branch_access,
    guard_device_branch_access,
    guard_operator,
)
from production_pulse_app.interface.http.routes.device_routes import _json_error

router = APIRouter(prefix="/operator", tags=["Operator"])
_placement_service = OperatorPlacementService()
_device_service = DeviceService()
_command_service = DeviceCommandService()


def _actor_sub(request: Request) -> str | None:
    user = getattr(request.state, "user", None)
    if user is None:
        return None
    return getattr(user, "sub", None) or getattr(user, "id", None)


@router.get("/placements")
async def list_operator_placements(
    request: Request,
    branch: str = Query(..., min_length=1),
    anchor_type: str | None = Query(default=None, alias="anchorType"),
    search: str | None = Query(default=None),
):
    denied = guard_operator(request) or guard_branch_access(request, branch)
    if denied is not None:
        return denied
    return success(
        _placement_service.list_placements(
            branch=branch,
            anchor_type=anchor_type,
            search=search,
        )
    )


@router.get("/work-centers")
async def list_operator_work_centers(
    request: Request,
    branch: str = Query(..., min_length=1),
    search: str | None = Query(default=None),
):
    denied = guard_operator(request) or guard_branch_access(request, branch)
    if denied is not None:
        return denied
    return success(
        _placement_service.list_placements(
            branch=branch,
            anchor_type="work_center",
            search=search,
        )
    )


@router.get("/placements/{placement_key}/devices")
async def list_operator_placement_devices(
    request: Request,
    placement_key: str,
    branch: str = Query(..., min_length=1),
    role: str | None = Query(default=None),
):
    denied = guard_operator(request) or guard_branch_access(request, branch)
    if denied is not None:
        return denied
    return success(
        _placement_service.list_placement_devices(
            branch=branch,
            placement_key=placement_key,
            role=role,
            operator_eligible_only=True,
        )
    )


@router.post("/devices/{device_id}/commands/{command_key}")
async def execute_operator_device_command(
    request: Request,
    device_id: UUID,
    command_key: str,
):
    denied = guard_operator(request)
    if denied is not None:
        return denied
    try:
        device = _device_service.get_device_record(parse_device_id(str(device_id)))
        branch_denied = guard_device_branch_access(request, device)
        if branch_denied is not None:
            return branch_denied
        data = _command_service.execute_command(
            parse_device_id(str(device_id)),
            command_key,
            actor_sub=_actor_sub(request),
        )
        return success(data)
    except Exception as exc:
        return _json_error(exc)


@router.get("/work-centers/{code}/devices")
async def legacy_work_center_devices_redirect(
    request: Request,
    code: str,
    branch: str = Query(..., min_length=1),
):
    denied = guard_operator(request) or guard_branch_access(request, branch)
    if denied is not None:
        return denied
    placement_key = f"wc:{branch}:{code}"
    query = urlencode({"branch": branch})
    target = f"/operator/placements/{placement_key}/devices?{query}"
    return RedirectResponse(url=target, status_code=308)


@router.get("/devices/{device_id}")
async def get_operator_device_surface(request: Request, device_id: UUID):
    denied = guard_operator(request)
    if denied is not None:
        return denied
    try:
        device = _device_service.get_device_record(parse_device_id(str(device_id)))
        branch_denied = guard_device_branch_access(request, device)
        if branch_denied is not None:
            return branch_denied
        return success(_device_service.get_device(device_id))
    except DeviceNotFoundError as exc:
        return _json_error(exc)

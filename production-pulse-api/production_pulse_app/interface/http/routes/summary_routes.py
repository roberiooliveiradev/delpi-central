from __future__ import annotations

from fastapi import APIRouter, Query, Request

from production_pulse_app.application.services.device_summary_service import DeviceSummaryService
from production_pulse_app.core.responses import success
from production_pulse_app.interface.http.rbac_http import (
    guard_branch_access,
    guard_view_devices,
    resolve_list_branches,
)

router = APIRouter(tags=["Summary"])
_summary_service = DeviceSummaryService()


@router.get("/summary")
async def get_operational_summary(
    request: Request,
    branch: str | None = Query(default=None),
):
    denied = guard_view_devices(request)
    if denied is not None:
        return denied
    branches, denied = resolve_list_branches(request, branch)
    if denied is not None:
        return denied
    return success(_summary_service.build_summary(branch=branch, branches=branches))

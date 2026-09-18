"""Fail-closed unit scope for canonical supplies.access on KPI routes.

Legacy api-delpi.access and dashboard-supplies.view stay global.
supplies.access requires supplies.unit.filial-*.
supplies.manage is not a branch bypass.
"""

from __future__ import annotations

from fastapi import HTTPException, Request

from delpi_auth.authz_core import has_permission
from delpi_auth.request_context import get_current_user

from app.application.security.api_delpi_permissions import (
    API_DELPI_ACCESS,
    DASHBOARD_SUPPLIES_VIEW,
    SUPPLIES_ACCESS,
)

_UNITS = {
    "01": "supplies.unit.filial-01",
    "02": "supplies.unit.filial-02",
}
_SURFACE = (SUPPLIES_ACCESS,)
_LEGACY_GLOBAL = (API_DELPI_ACCESS, DASHBOARD_SUPPLIES_VIEW)


def _allowed(user, branch: str) -> bool:
    unit = _UNITS.get(branch)
    if not unit or not has_permission(user, unit):
        return False
    return any(has_permission(user, code) for code in _SURFACE)


def enforce_canonical_supplies_branch(request: Request) -> None:
    user = get_current_user()
    if user is None or getattr(user, "is_superadmin", False):
        return
    if any(has_permission(user, code) for code in _LEGACY_GLOBAL):
        return
    if not any(has_permission(user, code) for code in _SURFACE):
        return
    raw_values = [item.strip() for item in request.query_params.getlist("branch") if item.strip()]
    if not raw_values:
        raise HTTPException(status_code=403, detail="Forbidden")
    for raw in raw_values:
        if raw in {"all", "*"}:
            if not all(_allowed(user, code) for code in _UNITS):
                raise HTTPException(status_code=403, detail="Forbidden")
            continue
        if not _allowed(user, raw):
            raise HTTPException(status_code=403, detail="Forbidden")

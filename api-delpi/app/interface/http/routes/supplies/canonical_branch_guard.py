"""Branch shape check for direct callers of supplies KPI routes.

supplies.access is not an api-delpi grant. Trusted supplies-api skips this
guard. Sibling api-delpi.access and dashboard-supplies.view stay global.
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
from app.interface.http.supplies_bff_service_access import is_trusted_supplies_bff_call

_LEGACY_GLOBAL = (API_DELPI_ACCESS, DASHBOARD_SUPPLIES_VIEW)


def enforce_canonical_supplies_branch(request: Request) -> None:
    if is_trusted_supplies_bff_call():
        return
    user = get_current_user()
    if user is None or getattr(user, "is_superadmin", False):
        return
    if any(has_permission(user, code) for code in _LEGACY_GLOBAL):
        return
    if has_permission(user, SUPPLIES_ACCESS):
        raise HTTPException(status_code=403, detail="Forbidden")
    _ = request

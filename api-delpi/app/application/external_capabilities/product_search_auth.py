"""Canonical AuthZ probe for Product Master search (no external RBAC disclosure)."""

from __future__ import annotations

from delpi_auth.authz_core import has_any_permission
from delpi_auth.request_context import get_current_user

from app.application.security.api_delpi_permissions import ENGINEERING_LMP_ACCESS


def user_can_search_products() -> bool:
    """Return whether the authenticated DELPI user may run product search."""
    user = get_current_user()
    if user is None:
        return False
    if getattr(user, "is_superadmin", False):
        return True
    return has_any_permission(user, ENGINEERING_LMP_ACCESS)


def require_product_search_access() -> None:
    """Raise Unauthorized/Forbidden using the same permission set as HTTP routes."""
    user = get_current_user()
    if user is None:
        raise PermissionError("Unauthorized")
    if getattr(user, "rbac_unavailable", False):
        raise RuntimeError("Service Unavailable")
    if getattr(user, "is_superadmin", False):
        return
    if not has_any_permission(user, ENGINEERING_LMP_ACCESS):
        raise PermissionError("Forbidden")

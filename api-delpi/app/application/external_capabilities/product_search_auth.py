"""Canonical AuthZ probe for Product Master search (no external RBAC disclosure).

Boundary note (PLUGIN-002 Abstraction Gate):
api-delpi application services already resolve the authenticated actor via the
canonical `delpi_auth.request_context` + `authz_core` pattern used by HTTP
`@require_*` decorators. This is an accepted repository pattern, not a new
RBAC matrix. No parallel permission authority is introduced here.
"""

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

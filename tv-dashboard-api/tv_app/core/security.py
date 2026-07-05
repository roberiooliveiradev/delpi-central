from __future__ import annotations

from typing import Any

from delpi_auth.authz_core import has_permission
from fastapi import Request

TV_READ = "tv-dashboard.read"
TV_WRITE = "tv-dashboard.write"
TV_MANAGE = "tv-dashboard.manage"
TV_ADMIN = "tv-dashboard.admin"


def _is_superadmin(user: Any | None) -> bool:
    return bool(user is not None and getattr(user, "is_superadmin", False))


def can(user: Any | None, permission: str) -> bool:
    if user is None:
        return False
    if _is_superadmin(user):
        return True
    if has_permission(user, TV_ADMIN):
        return True
    return has_permission(user, permission)


def assert_permission(user: Any | None, permission: str) -> None:
    if not can(user, permission):
        raise PermissionError("Você não tem permissão para esta ação.")


def actor_sub_from_request(request: Request) -> str | None:
    user = getattr(request.state, "user", None)
    if user is None:
        return None
    return getattr(user, "sub", None) or getattr(user, "preferred_username", None)

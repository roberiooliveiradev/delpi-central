"""RBAC codes for purchase-requests — aligned with contract Fase 0.2."""

from __future__ import annotations

from delpi_auth.authz_core import has_permission

UNIT_CODES = ("01", "02")

ACCESS_PERMISSION = "purchase-requests.access"
ADMIN_PERMISSION = "purchase-requests.admin"
VIEW_ALL_PERMISSION = "purchase-requests.view-all"
EXPORT_PERMISSION = "purchase-requests.export"
RBAC_MANAGE_PERMISSION = "rbac.manage"
USERS_MANAGE_PERMISSION = "users.manage"

UNIT_PERMISSIONS: dict[str, str] = {
    "01": "purchase-requests.unit.filial-01",
    "02": "purchase-requests.unit.filial-02",
}


def normalize_branch(value: str | None) -> str | None:
    code = (value or "").strip()
    if code in UNIT_CODES:
        return code
    return None


def has_access(user) -> bool:
    if getattr(user, "is_superadmin", False):
        return True
    return has_permission(user, ACCESS_PERMISSION) or has_permission(user, ADMIN_PERMISSION)


def has_admin(user) -> bool:
    if getattr(user, "is_superadmin", False):
        return True
    return has_any_module_admin_permission(user)


def has_portal_user_manage(user) -> bool:
    if getattr(user, "is_superadmin", False):
        return True
    return (
        has_permission(user, RBAC_MANAGE_PERMISSION)
        and has_permission(user, USERS_MANAGE_PERMISSION)
    )


def has_any_module_admin_permission(user) -> bool:
    """Module admin or platform RBAC managers (homologation / rollout)."""
    return has_permission(user, ADMIN_PERMISSION) or has_permission(user, RBAC_MANAGE_PERMISSION)


def has_view_all(user) -> bool:
    if getattr(user, "is_superadmin", False):
        return True
    return has_permission(user, VIEW_ALL_PERMISSION)


def has_branch_access(user, branch: str) -> bool:
    code = normalize_branch(branch)
    if not code:
        return False
    if getattr(user, "is_superadmin", False):
        return True
    if has_permission(user, ADMIN_PERMISSION):
        return True
    if has_permission(user, ACCESS_PERMISSION):
        return has_permission(user, UNIT_PERMISSIONS[code])
    return False


def assert_branch_access(user, branch: str) -> None:
    if not has_branch_access(user, branch):
        raise PermissionError(f"Sem permissão para acessar dados da filial {branch}.")

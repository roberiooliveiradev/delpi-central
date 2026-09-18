"""RBAC codes for purchase-requests — aligned with contract Fase 0.2."""

from __future__ import annotations

from delpi_auth.authz_core import has_permission

UNIT_CODES = ("01", "02")

ACCESS_PERMISSION = "purchase-requests.access"
SUPPLIES_ACCESS = "supplies.access"
SUPPLIES_MANAGE = "supplies.manage"
SUPPLIES_PR_ACCESS = "supplies.purchase-requests.access"
SUPPLIES_VIEW_ALL = "supplies.purchase-requests.view-all"
ADMIN_PERMISSION = "purchase-requests.admin"
VIEW_ALL_PERMISSION = "purchase-requests.view-all"
EXPORT_PERMISSION = "purchase-requests.export"
RBAC_MANAGE_PERMISSION = "rbac.manage"
USERS_MANAGE_PERMISSION = "users.manage"

UNIT_PERMISSIONS: dict[str, str] = {
    "01": "purchase-requests.unit.filial-01",
    "02": "purchase-requests.unit.filial-02",
}
SUPPLIES_UNIT_PERMISSIONS: dict[str, str] = {
    "01": "supplies.unit.filial-01",
    "02": "supplies.unit.filial-02",
}


def normalize_branch(value: str | None) -> str | None:
    code = (value or "").strip()
    if code in UNIT_CODES:
        return code
    return None


def has_access(user) -> bool:
    if getattr(user, "is_superadmin", False):
        return True
    if has_permission(user, SUPPLIES_ACCESS) or has_permission(user, SUPPLIES_PR_ACCESS):
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
    return has_permission(user, VIEW_ALL_PERMISSION) or has_permission(user, SUPPLIES_VIEW_ALL)


def has_branch_access(user, branch: str) -> bool:
    code = normalize_branch(branch)
    if not code:
        return False
    if getattr(user, "is_superadmin", False):
        return True
    if has_permission(user, SUPPLIES_ACCESS) or has_permission(user, SUPPLIES_PR_ACCESS):
        return has_permission(user, SUPPLIES_UNIT_PERMISSIONS[code]) or has_permission(
            user, UNIT_PERMISSIONS[code]
        )
    if has_permission(user, ADMIN_PERMISSION):
        return True
    if has_permission(user, ACCESS_PERMISSION):
        return has_permission(user, UNIT_PERMISSIONS[code])
    return False


def assert_branch_access(user, branch: str) -> None:
    if not has_branch_access(user, branch):
        raise PermissionError(f"Sem permissão para acessar dados da filial {branch}.")


def normalize_branches(values: list[str] | None, *, fallback: str | None = None) -> list[str]:
    raw = list(values or [])
    if not raw and fallback:
        raw = [fallback]
    codes: list[str] = []
    seen: set[str] = set()
    for item in raw:
        code = normalize_branch(item)
        if not code or code in seen:
            continue
        seen.add(code)
        codes.append(code)
    return codes


def assert_branches_access(user, branches: list[str]) -> list[str]:
    codes = normalize_branches(branches)
    if not codes:
        raise PermissionError("Sem permissão para acessar dados da filial.")
    for code in codes:
        assert_branch_access(user, code)
    return codes

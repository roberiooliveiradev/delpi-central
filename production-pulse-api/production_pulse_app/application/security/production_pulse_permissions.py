"""RBAC codes for Production Pulse — aligned with production-pulse.manifest.json."""

from __future__ import annotations

from delpi_auth.authz_core import has_any_permission, has_permission

ACCESS = "production-pulse.access"
DEVICES_VIEW = "production-pulse.devices.view"
DEVICES_MANAGE = "production-pulse.devices.manage"
DEVICES_COMMAND = "production-pulse.devices.command"
OPERATOR = "production-pulse.operator"
ADMIN = "production-pulse.admin"

BRANCH_CODES = ("01", "02")
BRANCH_VIEW_PERMISSIONS: dict[str, str] = {
    "01": "production-pulse.view.filial-01",
    "02": "production-pulse.view.filial-02",
}

ADMIN_DEVICE_ACTIONS = (DEVICES_VIEW, DEVICES_MANAGE, DEVICES_COMMAND)


def normalize_branch(value: str | None) -> str | None:
    code = (value or "").strip()
    if code in BRANCH_CODES:
        return code
    return None


def is_admin(user: object | None) -> bool:
    return has_permission(user, ADMIN)


def has_branch_access(user: object | None, branch: str) -> bool:
    code = normalize_branch(branch)
    if not code:
        return False
    if is_admin(user):
        return True
    return has_permission(user, BRANCH_VIEW_PERMISSIONS[code])


def branch_codes_for_access(user: object | None) -> list[str]:
    if is_admin(user):
        return list(BRANCH_CODES)
    return [code for code in BRANCH_CODES if has_branch_access(user, code)]


def can_view_devices(user: object | None) -> bool:
    if is_admin(user):
        return True
    return has_any_permission(user, ADMIN_DEVICE_ACTIONS)


def can_manage_devices(user: object | None) -> bool:
    if is_admin(user):
        return True
    return has_permission(user, DEVICES_MANAGE)


def can_admin_command(user: object | None) -> bool:
    if is_admin(user):
        return True
    return has_any_permission(user, (DEVICES_COMMAND, DEVICES_MANAGE))


def can_operator(user: object | None) -> bool:
    if is_admin(user):
        return True
    return has_permission(user, OPERATOR)


def assert_can_view_devices(user: object | None) -> None:
    if not can_view_devices(user):
        raise PermissionError("Sem permissão para visualizar dispositivos.")


def assert_can_manage_devices(user: object | None) -> None:
    if not can_manage_devices(user):
        raise PermissionError("Sem permissão para gerenciar dispositivos.")


def assert_can_admin_command(user: object | None) -> None:
    if not can_admin_command(user):
        raise PermissionError("Sem permissão para enviar comandos no painel administrativo.")


def assert_can_operator(user: object | None) -> None:
    if not can_operator(user):
        raise PermissionError("Sem permissão para acessar o modo operador.")


def assert_branch_access(user: object | None, branch: str) -> None:
    if not has_branch_access(user, branch):
        raise PermissionError("Sem permissão para esta filial.")


def assert_device_branch_access(user: object | None, device_row: dict) -> None:
    assert_branch_access(user, str(device_row.get("branch") or ""))
